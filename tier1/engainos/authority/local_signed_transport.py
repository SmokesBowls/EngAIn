"""EngAIn-owned local signed-request transport.

Authenticates which *client binding* sent a request. It says nothing about who
the actor is: that comes only from the server-owned client policy, which maps
an authenticated client_id to an actor and tier. Transport credentials and
actor identity are separate on purpose.

Request signature (all ASCII, newline-joined):

    METHOD \\n PATH \\n TIMESTAMP \\n NONCE \\n hex(sha256(BODY))

signed with HMAC-SHA256 under the client's 32-byte secret, carried in

    X-EngAIn-Client     client_id
    X-EngAIn-Timestamp  unix seconds (decimal)
    X-EngAIn-Nonce      32 lowercase hex, never reused within the window
    X-EngAIn-Signature  64 lowercase hex

Verification happens before the body is parsed or anything else runs. Secrets
are minted by the composition root at every start (a restart rotates them),
written 0600 into a 0700 directory, and never logged or sent on the wire.

The client policy file is the only source of actor_id and tier. A missing
file or an empty `clients` object means deny-all. No assignment is ever
defaulted.

Transport roles (the route vocabulary), each a client *binding*, not a person,
model or canon identity:

  build    8765  asks EngAInOS to build and authorize one surface. The only
                 role that carries an actor_id and tier, because issuance
                 records them as authority evidence.
  consume  8765  the presentation executor: consumes one authorization for a
                 one-time grant bound to this client id.
  observe  8080  the presentation observer: reports what Godot is presenting,
                 as testimony.

Each server provisions secrets only for the clients holding its roles, in its
own subdirectory (TRANSPORT_DIR/<server>/), so one policy serves both
processes without them sharing or overwriting secrets.

The server buffers at most MAX_SIGNED_BODY_BYTES of the body (refused with 413
before reading when Content-Length is larger). Verification runs on those
buffered bytes before anything parses them or changes state.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

HEADER_CLIENT = "X-EngAIn-Client"
HEADER_TIMESTAMP = "X-EngAIn-Timestamp"
HEADER_NONCE = "X-EngAIn-Nonce"
HEADER_SIGNATURE = "X-EngAIn-Signature"

POLICY_CONTRACT = "engainos.local_client_policy.v1"
MAX_SKEW_S = 30
MAX_PENDING_NONCES = 100_000
MAX_SIGNED_BODY_BYTES = 16 * 1024 * 1024
KNOWN_ROUTES = frozenset({"build", "consume", "observe"})
ACTOR_ROUTES = frozenset({"build"})  # roles whose requests are recorded as authority evidence

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_POLICY_PATH = _REPO_ROOT / "tier1" / "engainos" / "authority" / "TRIXEL32D_LIVE_CLIENT_POLICY_V1.json"
DEFAULT_TRANSPORT_DIR = _REPO_ROOT / "runtime" / "engain_transport"

_CLIENT_ID = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
_HEX32 = re.compile(r"^[0-9a-f]{32}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_TIMESTAMP = re.compile(r"^[0-9]{1,12}$")


class TransportAuthError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


@dataclass(frozen=True)
class ClientAssignment:
    actor_id: str | None              # present only for ACTOR_ROUTES clients
    actor_authority_tier: int | None
    routes: frozenset[str]


def bounded_content_length(headers: Mapping[str, str], limit: int = MAX_SIGNED_BODY_BYTES) -> int:
    """Content-Length to buffer for a signed request, refused before reading if absent or too large."""
    raw = headers.get("Content-Length")
    if raw is None or not str(raw).isdigit():
        raise TransportAuthError(411, "signed requests require a Content-Length")
    length = int(raw)
    if length > limit:
        raise TransportAuthError(413, f"signed request body exceeds {limit} bytes")
    return length


def signing_string(method: str, path: str, timestamp: str, nonce: str, body: bytes) -> bytes:
    return "\n".join((method.upper(), path, timestamp, nonce, hashlib.sha256(body).hexdigest())).encode("ascii")


def sign(secret: bytes, method: str, path: str, timestamp: str, nonce: str, body: bytes) -> str:
    return hmac.new(secret, signing_string(method, path, timestamp, nonce, body), hashlib.sha256).hexdigest()


def signed_headers(client_id: str, secret: bytes, method: str, path: str, body: bytes,
                   *, now: float | None = None) -> dict[str, str]:
    """Client-side helper (Python callers and tests); Godot implements the same with HMACContext."""
    timestamp = str(int(time.time() if now is None else now))
    nonce = secrets.token_hex(16)
    return {
        HEADER_CLIENT: client_id,
        HEADER_TIMESTAMP: timestamp,
        HEADER_NONCE: nonce,
        HEADER_SIGNATURE: sign(secret, method, path, timestamp, nonce, body),
    }


class SignedRequestVerifier:
    """Verify one signed request. Thread-safe; nonces are remembered for the freshness window."""

    def __init__(
        self,
        credentials: Mapping[str, bytes],
        *,
        max_skew_s: int = MAX_SKEW_S,
        clock: Callable[[], float] = time.time,
    ) -> None:
        for client_id, secret in credentials.items():
            if not _CLIENT_ID.fullmatch(client_id) or not isinstance(secret, bytes) or len(secret) != 32:
                raise ValueError("credentials must map valid client ids to 32-byte secrets")
        self._credentials = dict(credentials)
        self._max_skew_s = max_skew_s
        self._clock = clock
        self._seen: dict[tuple[str, str], float] = {}
        self._lock = threading.Lock()

    def verify(self, method: str, path: str, headers: Mapping[str, str], body: bytes) -> str:
        """Return the authenticated client_id, or raise TransportAuthError(401)."""
        client_id = headers.get(HEADER_CLIENT)
        timestamp = headers.get(HEADER_TIMESTAMP)
        nonce = headers.get(HEADER_NONCE)
        signature = headers.get(HEADER_SIGNATURE)
        if not all(isinstance(v, str) for v in (client_id, timestamp, nonce, signature)):
            raise TransportAuthError(401, "request is not signed")
        secret = self._credentials.get(client_id)
        if secret is None:
            raise TransportAuthError(401, "request client is not a provisioned transport client")
        if not _TIMESTAMP.fullmatch(timestamp) or not _HEX32.fullmatch(nonce) or not _HEX64.fullmatch(signature):
            raise TransportAuthError(401, "request signature headers are malformed")
        expected = sign(secret, method, path, timestamp, nonce, body)
        if not hmac.compare_digest(expected, signature):
            raise TransportAuthError(401, "request signature does not verify")
        now = self._clock()
        if abs(now - int(timestamp)) > self._max_skew_s:
            raise TransportAuthError(401, "request timestamp is outside the freshness window")
        key = (client_id, nonce)
        with self._lock:
            # Forget nonces whose timestamps can no longer pass the freshness check.
            for seen_key in [k for k, expiry in self._seen.items() if expiry < now]:
                del self._seen[seen_key]
            if key in self._seen:
                raise TransportAuthError(401, "request nonce was already used")
            if len(self._seen) >= MAX_PENDING_NONCES:
                raise TransportAuthError(401, "request replay cache is full; refusing")
            self._seen[key] = int(timestamp) + self._max_skew_s
        return client_id


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(token: str) -> Any:
    raise ValueError(f"non-finite JSON constant {token}")


def load_client_policy(path: Path, known_routes: frozenset[str] = KNOWN_ROUTES) -> dict[str, ClientAssignment]:
    """Load the server-owned client policy. Missing file -> deny-all. Malformed -> ValueError."""
    if not path.exists():
        return {}
    data = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_strict_object,
        parse_constant=_reject_constant,
    )
    if not isinstance(data, dict) or set(data) != {"contract", "clients"} or data["contract"] != POLICY_CONTRACT:
        raise ValueError(f"client policy must be exactly {{contract: {POLICY_CONTRACT!r}, clients: {{...}}}}")
    clients = data["clients"]
    if not isinstance(clients, dict):
        raise ValueError("client policy clients must be an object")
    policy: dict[str, ClientAssignment] = {}
    for client_id, entry in clients.items():
        if not _CLIENT_ID.fullmatch(client_id):
            raise ValueError(f"client policy has an invalid client id {client_id!r}")
        if not isinstance(entry, dict) or "routes" not in entry:
            raise ValueError(f"client {client_id!r} must declare routes")
        routes = entry["routes"]
        if not isinstance(routes, list) or not routes or not all(isinstance(r, str) for r in routes) \
                or len(set(routes)) != len(routes) or not set(routes) <= known_routes:
            raise ValueError(f"client {client_id!r} routes must be a non-empty unique subset of {sorted(known_routes)}")
        if set(routes) & ACTOR_ROUTES:
            if set(entry) != {"actor_id", "actor_authority_tier", "routes"}:
                raise ValueError(f"client {client_id!r} must declare exactly actor_id, actor_authority_tier, routes")
            actor_id, tier = entry["actor_id"], entry["actor_authority_tier"]
            if not isinstance(actor_id, str) or not actor_id:
                raise ValueError(f"client {client_id!r} actor_id must be a non-empty string")
            # Tier 0 is the internal system tier (runtime, replay, validation): never a transport client.
            if isinstance(tier, bool) or tier not in (1, 2, 3):
                raise ValueError(f"client {client_id!r} tier must be 1, 2 or 3")
        else:
            # consume/observe carry no authority: an actor or tier here would be invented meaning.
            if set(entry) != {"routes"}:
                raise ValueError(f"client {client_id!r} holds no actor role; declare routes only")
            actor_id, tier = None, None
        policy[client_id] = ClientAssignment(actor_id, tier, frozenset(routes))
    return policy


def compose_verifier(
    policy: Mapping[str, ClientAssignment], server_routes: frozenset[str], server_dir: Path,
) -> tuple[SignedRequestVerifier, dict[str, ClientAssignment]]:
    """Provision secrets for the policy clients holding any of this server's roles; return its verifier."""
    clients = {cid: a for cid, a in policy.items() if a.routes & server_routes}
    return SignedRequestVerifier(provision_credentials(server_dir, sorted(clients))), clients


def provision_credentials(directory: Path, client_ids: list[str]) -> dict[str, bytes]:
    """Mint a fresh secret per client into `<directory>/<client_id>.key` (0600, hex). Rotates on every call."""
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(directory, 0o700)
    credentials: dict[str, bytes] = {}
    for client_id in client_ids:
        if not _CLIENT_ID.fullmatch(client_id):
            raise ValueError(f"invalid client id {client_id!r}")
        secret = secrets.token_bytes(32)
        final = directory / f"{client_id}.key"
        staging = directory / f".{client_id}.key.{secrets.token_hex(4)}"
        fd = os.open(staging, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.write(fd, secret.hex().encode("ascii"))
        finally:
            os.close(fd)
        os.replace(staging, final)
        credentials[client_id] = secret
    return credentials
