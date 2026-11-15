"""EngAInOS editor-edit authorization (proposal -> acceptance -> grant -> consume -> outcome).

Authorizes one Foundry (editor/executor) operation that Dragon (proposer) asked
for and a human accepted. It owns proposal, authorization and outcome records
only: it never edits files, never runs Foundry, and never touches runtime (8080)
state. It is a sibling of the Trixel live authority, not an extension of it:
no Trixel contract, field set, TTL or policy is shared or changed.

Identity and permission come from two server-owned files, both deny-all when
missing or empty:
  client policy (engainos.local_client_policy.v1, local_signed_transport):
      which authenticated transport client may call which editor route
      (route vocabulary EDITOR_ROUTES). It carries no actor or tier.
  edit policy (engainos.editor_edit_policy.v1, this module):
      per installation: four client bindings, the proposer and executor actor
      ids, the permitted operation class, the writable path prefixes and the
      protected paths. A request can never declare its own actor, scope or
      operation class; all of them are copied from this policy into the grant.

The four bindings are separate credentials, each held by one party and each
able to do only its own part (ROLE_ROUTE; editor_edit_route.compose refuses a
client holding any other route):
  proposer     Dragon's adapter: registers proposals; forwards a conversational
               acceptance or rejection, which it cannot make on its own.
  executor     the Foundry dock: picks up, consumes and reports grants. It can
               never accept, reject or change the approval mode, so the party
               that runs an edit holds no credential that approves one.
  approver     the human's Accept / Reject / approval-mode controls in the dock.
  human_input  the game's conversation input box (the human-input boundary).
               It calls no route; it signs exactly what the human typed
               (HUMAN_INPUT_CONTRACT), and a CONVERSATIONAL_ACCEPT is valid only
               with that signature over the exact `accept <code>` text.
approver and human_input are credential bindings, not actors: they carry no
actor id or tier (none is defined for them, and none is invented here).
No actor tier is read or assigned here (see AUTHORITY_TIER_SPEC_v1: a tier
needs a governing policy, and none is identified for editor edits yet).

Lifecycle of one proposal (states are terminal unless an arrow leaves them):
  PENDING --accept--> AUTHORIZED --consume--> CONSUMED --outcome--> COMPLETED | FAILED
  PENDING --reject--> REJECTED
  AUTHORIZED --grant expired--> AUTHORIZATION_EXPIRED
  AUTHORIZED --authority restart--> AUTHORIZATION_LOST    (grant key is per process)
  AUTHORIZED --target state moved--> AUTHORIZATION_STALE
Nothing ever moves a proposal back. A completed revert never restores an
authorization or makes a proposal executable again.

Both approval modes use one pipeline. The only difference is which evidence
authorizes it: MANUAL_ACCEPT comes from the approver binding;
CONVERSATIONAL_ACCEPT comes from the proposer-side adapter and must carry the
human_input binding's signature over the human's own typed confirmation,
which this authority parses itself (the same grammar as the adapter's). The
acceptance channel must equal the installation's current approval mode, and
only the approver may change the mode. Changing the mode records an event and
changes no proposal.

A grant is delivered only to the executor (pickup), is RSA-signed by a key
that exists only in this process (Godot verifies with the public key), lasts
GRANT_TTL_S, is bound to the exact proposal bytes, installation, executor,
operation class, path scope and the installation's edit-state sequence at
acceptance (any recorded edit or revert in between makes it stale), bound
to the content of every file in its scope as the acceptor saw it at approval
(base_scope_sha256, see scope_digest()), and is consumed at most once. The
executor reports the scope digest again immediately before executing; any
difference (for example a human edit made outside this pipeline) makes the
authorization stale instead of letting Foundry overwrite that work. The ledger is persisted atomically before any
response, so a consumed or rejected proposal stays so across restarts.

Standing mandates (FULL_SCENE, ENTIRE_GAME): one human approval (the approver binding,
create_mandate) for a bounded series of edits toward one stated goal. The mandate fixes the
mode, the goal text, the writable scope (a subset of this installation's policy prefixes, or
for ENTIRE_GAME an isolated workspace that the privileged editor never loads), a maximum edit
count and an expiry; the policy must list the mode in `mandate_modes` (absent -> no mandates).
Nothing ever widens, extends or renews a mandate: a new one needs a new approval, and only
one is ACTIVE per installation. While it is ACTIVE, a proposal the proposer registers with its
mandate_id is authorized at registration (channel MANDATE) instead of waiting for an accept;
every such grant still carries the mandate's scope only, is consumed once, and is checked
again against the reported outcome (an outcome outside scope revokes the mandate).
  ACTIVE --last edit authorized--> EXHAUSTED
  ACTIVE | EXHAUSTED --approver revoke / Stop--> REVOKED
  ACTIVE | EXHAUSTED --proposer declares the goal reached--> COMPLETED
  ACTIVE | EXHAUSTED --expires_at passed--> EXPIRED
  ACTIVE | EXHAUSTED --outcome outside scope--> REVOKED
Ending a mandate voids its unconsumed grants (proposal AUTHORIZATION_REVOKED). Dragon can only
end a mandate, never create, widen or extend one; Foundry can do neither.

Promotion: an ENTIRE_GAME workspace's files reach this installation's project only through
create_promotion (approver), after the mandate has ended, for an exact manifest of
{path, sha256} inside this installation's writable prefixes and outside its protected paths.
Editor-executable files (scripts, native code, binary resources, addons, project settings, or
a text resource the executor flags for embedded/new scripts) are refused unless the approver
sets allow_editor_code. The promotion grant is consumed once, against the target scope digest
the approver reviewed, and its outcome becomes the Revert Last Edit opportunity.

Revert slot: the installation's single "Revert Last Edit" opportunity as
reported by the executor. An operation outcome that changed files replaces
it (a failed operation included); rejected operations and operations that
changed nothing never touch it; a completed revert clears it.
"""

from __future__ import annotations

import base64
import copy
import fcntl
import hashlib
import json
import os
import re
import secrets
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from tier1.engainos.core.intent_shadow import record_intent

PROPOSAL_CONTRACT = "engainos.editor_proposal.v1"
GRANT_CONTRACT = "engainos.editor_edit_grant.v1"
LEDGER_CONTRACT = "engainos.editor_edit_ledger.v1"
POLICY_CONTRACT = "engainos.editor_edit_policy.v1"
GRANT_TTL_S = 120
MANDATE_MODES = ("FULL_SCENE", "ENTIRE_GAME")
MANDATE_LIVE_STATES = frozenset({"ACTIVE", "EXHAUSTED"})   # may still hold an unconsumed grant
MAX_MANDATE_EDITS = 500
MIN_MANDATE_TTL_S = 60
MAX_MANDATE_TTL_S = 86_400
MAX_GOAL_BYTES = 8 * 1024
PROMOTION_GRANT_CONTRACT = "engainos.editor_promotion_grant.v1"
PROMOTION_GRANT_FIELDS = frozenset({
    "contract", "grant_id", "promotion_id", "mandate_id", "workspace_id", "installation_id", "project_id",
    "executor_actor_id", "executor_client_id", "manifest_sha256", "editor_code_paths", "base_state_seq",
    "base_scope_sha256", "writable_path_prefixes", "protected_paths", "issued_at", "expires_at",
})
# Files Godot may execute inside the editor that opens them (or that cannot be inspected).
EDITOR_CODE_SUFFIXES = (".gd", ".gdc", ".cs", ".gdextension", ".so", ".dll", ".dylib", ".scn", ".res", ".pck")
EDITOR_CODE_NAMES = frozenset({"project.godot", "override.cfg", "plugin.cfg"})
PINNED_CRYPTOGRAPHY_MAJOR = 50  # tier1/engainos/requirements-authority.txt: cryptography==50.0.2
EDITOR_ROUTES = frozenset({"edit_propose", "edit_execute", "edit_approve", "edit_attest"})
ROLES = ("proposer", "executor", "approver", "human_input")
ROLE_ROUTE = {"proposer": "edit_propose", "executor": "edit_execute", "approver": "edit_approve",
              "human_input": "edit_attest"}
APPROVAL_MODES = ("MANUAL_ACCEPT", "CONVERSATIONAL_ACCEPT")
DEFAULT_APPROVAL_MODE = "MANUAL_ACCEPT"
CHANNEL_ROLE = {"MANUAL_ACCEPT": "approver", "CONVERSATIONAL_ACCEPT": "proposer"}
HUMAN_INPUT_CONTRACT = "engainos.human_input_attestation.v1"
HUMAN_INPUT_FIELDS = frozenset({"contract", "client_id", "installation_id", "request_id", "issued_at", "nonce",
                                "player_input_sha256", "signature"})
ATTESTATION_MAX_AGE_S = 185   # the HUD request's call lifetime (EngAInBridge3D.CALL_LIFETIME_SEC)
ATTESTATION_SKEW_S = 30
# create + modify inside writable prefixes, never inside protected paths, never delete.
OPERATION_CLASSES = frozenset({"project_file_edit.v1"})
REVERT_STATUSES = frozenset({
    "reverted", "refused_missing", "refused_state", "refused_mismatch",
    "refused_prepare_failed", "failed_recovered", "failed_unrecoverable",
})
MAX_BODY_BYTES = 16 * 1024
MAX_CHANGED_PATHS = 10_000
GRANT_FIELDS = frozenset({
    "contract", "grant_id", "authorization_id", "proposal_id", "body_sha256",
    "installation_id", "project_id", "executor_actor_id", "executor_client_id",
    "operation_class", "writable_path_prefixes", "protected_paths", "base_state_seq",
    "base_scope_sha256", "channel", "issued_at", "expires_at", "mandate_id", "workspace_id",
})

_PROPOSAL_ID = re.compile(r"^dragonreq_[0-9]{8}_[0-9]{6}_[0-9a-f]{8}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_CLIENT_ID = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
_TOKEN = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
_REQUEST_ID = re.compile(r"^req_[0-9a-f]{32}$")
_HEX32 = re.compile(r"^[0-9a-f]{32}$")
_WORKSPACE_ID = re.compile(r"^ws_[0-9a-z_-]{1,60}$")
# The confirmation grammar, identical to the Dragon adapter's dragon_edit_acceptance._CONFIRMATION.
_CONFIRMATION = re.compile(
    r"^\s*(accept|approve|reject)\s+(?:proposal\s+)?(dragonreq_[0-9]{8}_[0-9]{6}_[0-9a-f]{8}|[0-9a-f]{8})\s*[.!]?\s*$",
    re.IGNORECASE)


class EditAuthorityError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def body_sha256(body: str) -> str:
    """Canonical representation of an approved instruction: sha256 of its exact UTF-8 bytes."""
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def proposal_code(proposal_id: str) -> str:
    """The short reference a human types (`accept <code>`): the proposal id's random suffix."""
    return proposal_id[-8:]


def human_input_signing_bytes(attestation: Mapping[str, Any]) -> bytes:
    """What the human-input binding signs (HMAC-SHA256 with its transport secret).

    Newline-joined, starting with the contract so it can never equal a transport
    signing string (those start with the HTTP method):
        contract, client_id, installation_id, request_id, issued_at, nonce, player_input_sha256
    The game's EngAInBridge3D.gd builds the same bytes.
    """
    return "\n".join((HUMAN_INPUT_CONTRACT, str(attestation["client_id"]), str(attestation["installation_id"]),
                      str(attestation["request_id"]), str(attestation["issued_at"]), str(attestation["nonce"]),
                      str(attestation["player_input_sha256"]))).encode("utf-8")


def sign_human_input(secret: bytes, attestation: Mapping[str, Any]) -> str:
    """Reference signer (tests and Python callers); the game signs the same bytes with HMACContext."""
    import hmac
    return hmac.new(secret, human_input_signing_bytes(attestation), hashlib.sha256).hexdigest()


def parse_confirmation(player_input: str) -> tuple[str, str] | None:
    """(action, reference) for an exact `accept|approve|reject <code|proposal_id>`, else None."""
    match = _CONFIRMATION.fullmatch(player_input or "")
    if match is None:
        return None
    return ("reject" if match.group(1).lower() == "reject" else "accept"), match.group(2).lower()


def scope_digest(entries: Mapping[str, str]) -> str:
    """Optimistic-concurrency digest over {relative_path: sha256} of every file in a grant's scope.

    sha256 of the sorted lines "<sha256>  <path>\\n" (sha256sum format, paths sorted by code
    point). Computed identically by the Dragon adapter (dragon_edit_acceptance.py) and the
    Foundry dock (edit_authority_client.gd); the authority only compares the values.
    """
    return hashlib.sha256("".join(f"{entries[p]}  {p}\n" for p in sorted(entries)).encode("utf-8")).hexdigest()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(token: str) -> Any:
    raise ValueError(f"non-finite JSON constant {token}")


def strict_json_loads(text: str) -> Any:
    return json.loads(text, object_pairs_hook=_strict_object, parse_constant=_reject_constant)


def is_editor_code_path(path: str) -> bool:
    """True for a path Godot may execute in the editor that opens it, judged by name alone."""
    lower = path.lower()
    return lower.startswith("addons/") or lower.rsplit("/", 1)[-1] in EDITOR_CODE_NAMES or lower.endswith(EDITOR_CODE_SUFFIXES)


def _under(path: str, entry: str) -> bool:
    """Same rule as Foundry's edit_authority_client._under."""
    return path == entry.rstrip("/") or path.startswith(entry if entry.endswith("/") else entry + "/")


def _safe_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or len(value) > 256 or "\x00" in value or "\\" in value:
        return False
    if value.startswith("/"):
        return False
    segments = value.rstrip("/").split("/")
    return all(segment not in ("", ".", "..") for segment in segments)


@dataclass(frozen=True)
class Installation:
    installation_id: str
    project_id: str
    proposer_client_id: str
    proposer_actor_id: str
    executor_client_id: str
    executor_actor_id: str
    approver_client_id: str
    human_input_client_id: str
    operation_class: str
    writable_path_prefixes: tuple[str, ...]
    protected_paths: tuple[str, ...]
    mandate_modes: tuple[str, ...] = ()

    def client_for(self, role: str) -> str:
        return {"proposer": self.proposer_client_id, "executor": self.executor_client_id,
                "approver": self.approver_client_id, "human_input": self.human_input_client_id}[role]


_INSTALLATION_KEYS = {"project_id", "proposer", "executor", "approver", "human_input", "operation_class",
                      "writable_path_prefixes", "protected_paths"}
_PARTY_KEYS = {"client_id", "actor_id"}
_BINDING_KEYS = {"client_id"}     # approver, human_input: credentials held by the human, no actor


def load_edit_policy(path: Path) -> dict[str, Installation]:
    """Load the server-owned edit policy. Missing file -> deny-all. Malformed -> ValueError."""
    if not path.exists():
        return {}
    data = strict_json_loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"contract", "installations"} or data["contract"] != POLICY_CONTRACT:
        raise ValueError(f"edit policy must be exactly {{contract: {POLICY_CONTRACT!r}, installations: {{...}}}}")
    if not isinstance(data["installations"], dict):
        raise ValueError("edit policy installations must be an object")
    result: dict[str, Installation] = {}
    seen_clients: set[str] = set()
    for installation_id, entry in data["installations"].items():
        if not isinstance(entry, dict) or set(entry) not in (_INSTALLATION_KEYS, _INSTALLATION_KEYS | {"mandate_modes"}):
            raise ValueError(f"installation {installation_id!r} must declare exactly {sorted(_INSTALLATION_KEYS)}"
                             " (and optionally mandate_modes)")
        mandate_modes = entry.get("mandate_modes", [])
        if not isinstance(mandate_modes, list) or len(set(mandate_modes)) != len(mandate_modes) \
                or not all(m in MANDATE_MODES for m in mandate_modes):
            raise ValueError(f"installation {installation_id!r} mandate_modes must be unique values from {MANDATE_MODES}")
        parties = {}
        for role in ROLES:
            party = entry[role]
            keys = _PARTY_KEYS if role in ("proposer", "executor") else _BINDING_KEYS
            if not isinstance(party, dict) or set(party) != keys:
                raise ValueError(f"installation {installation_id!r} {role} must declare exactly {sorted(keys)}")
            if not isinstance(party["client_id"], str) or not _CLIENT_ID.fullmatch(party["client_id"]):
                raise ValueError(f"installation {installation_id!r} {role} client_id is invalid")
            parties[role] = party
            if keys == _BINDING_KEYS:
                continue
            try:
                actor = uuid.UUID(party["actor_id"])
            except (ValueError, AttributeError, TypeError) as exc:
                raise ValueError(f"installation {installation_id!r} {role} actor_id must be a UUID") from exc
            if str(actor) != party["actor_id"]:
                raise ValueError(f"installation {installation_id!r} {role} actor_id must be canonical lowercase")
        project_id = entry["project_id"]
        if not isinstance(project_id, str) or not _TOKEN.fullmatch(project_id):
            raise ValueError(f"installation {installation_id!r} project_id is invalid")
        expected = str(uuid.uuid5(uuid.UUID(parties["proposer"]["actor_id"]), project_id))
        if installation_id != expected:
            raise ValueError(f"installation id {installation_id!r} is not uuid5(proposer actor, project_id)")
        if parties["proposer"]["actor_id"] == parties["executor"]["actor_id"]:
            raise ValueError(f"installation {installation_id!r}: proposer and executor must be different actors")
        clients = {parties[role]["client_id"] for role in ROLES}
        if len(clients) != len(ROLES) or clients & seen_clients:
            raise ValueError(f"installation {installation_id!r}: each client binding serves exactly one role")
        seen_clients |= clients
        if entry["operation_class"] not in OPERATION_CLASSES:
            raise ValueError(f"installation {installation_id!r} operation_class must be one of {sorted(OPERATION_CLASSES)}")
        prefixes, protected = entry["writable_path_prefixes"], entry["protected_paths"]
        if not isinstance(prefixes, list) or not prefixes or len(set(prefixes)) != len(prefixes) \
                or not all(_safe_relative_path(p) and p.endswith("/") for p in prefixes):
            raise ValueError(f"installation {installation_id!r} writable_path_prefixes must be unique relative directories ending in '/'")
        if not isinstance(protected, list) or len(set(protected)) != len(protected) \
                or not all(_safe_relative_path(p) for p in protected):
            raise ValueError(f"installation {installation_id!r} protected_paths must be unique relative paths")
        result[installation_id] = Installation(
            installation_id, project_id,
            parties["proposer"]["client_id"], parties["proposer"]["actor_id"],
            parties["executor"]["client_id"], parties["executor"]["actor_id"],
            parties["approver"]["client_id"], parties["human_input"]["client_id"],
            entry["operation_class"], tuple(prefixes), tuple(protected), tuple(mandate_modes),
        )
    return result


class _GrantSigner:
    """RSA-3072 PKCS#1 v1.5 SHA-256 over the exact grant_json bytes; key lives in this process only."""

    def __init__(self) -> None:
        try:
            import cryptography
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding, rsa
        except ImportError as exc:  # fail closed: no signer, no grants
            raise EditAuthorityError(503, "SIGNER_UNAVAILABLE", "grant signing requires the 'cryptography' package") from exc
        if str(getattr(cryptography, "__version__", "")).split(".")[0] != str(PINNED_CRYPTOGRAPHY_MAJOR):
            raise EditAuthorityError(503, "SIGNER_UNAVAILABLE",
                                     f"grant signing is verified against cryptography {PINNED_CRYPTOGRAPHY_MAJOR}.x")
        self._hashes, self._padding = hashes, padding
        self._key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
        self.public_key_pem = self._key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode("ascii")

    def sign(self, grant: Mapping[str, Any]) -> dict[str, str]:
        if set(grant) != (PROMOTION_GRANT_FIELDS if grant.get("contract") == PROMOTION_GRANT_CONTRACT else GRANT_FIELDS):
            raise EditAuthorityError(500, "GRANT_FIELDS", "editor grant fields are incomplete or unknown")
        grant_json = json.dumps(grant, sort_keys=True, separators=(",", ":"), allow_nan=False)
        signature = self._key.sign(grant_json.encode("utf-8"), self._padding.PKCS1v15(), self._hashes.SHA256())
        return {"grant_json": grant_json, "grant_signature_b64": base64.b64encode(signature).decode("ascii")}

    def verify(self, grant_json: str, grant_signature_b64: str) -> bool:
        """Python-side check for tests; the Godot executor performs the same verification."""
        from cryptography.exceptions import InvalidSignature
        try:
            self._key.public_key().verify(base64.b64decode(grant_signature_b64, validate=True),
                                          grant_json.encode("utf-8"), self._padding.PKCS1v15(), self._hashes.SHA256())
        except (InvalidSignature, ValueError):
            return False
        return True


def _empty_ledger() -> dict[str, Any]:
    return {"contract": LEDGER_CONTRACT, "installations": {}, "proposals": {}, "grants": {}, "events": [],
            "mandates": {}, "promotions": {}}


_LEGACY_LEDGER_KEYS = frozenset({"contract", "installations", "proposals", "grants", "events"})


class _DurableLedger:
    """One owner process (flock on a sidecar lock file); every commit is write-tmp + fsync + rename + fsync(dir)."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self.path.with_name(self.path.name + ".lock")
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0), 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(fd)
            raise EditAuthorityError(503, "LEDGER_OWNED", "editor edit ledger is owned by another process") from exc
        self._lock_fd = fd
        if self.path.exists():
            data = strict_json_loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and set(data) == _LEGACY_LEDGER_KEYS:
                data.update(mandates={}, promotions={})     # a ledger written before mandates existed
            if not isinstance(data, dict) or data.get("contract") != LEDGER_CONTRACT \
                    or set(data) != set(_empty_ledger()):
                raise EditAuthorityError(503, "LEDGER_CORRUPT", "editor edit ledger has an unknown shape")
            self.data = data
        else:
            self.data = _empty_ledger()

    def commit(self) -> None:
        staging = self.path.with_name(f".{self.path.name}.{secrets.token_hex(4)}")
        payload = json.dumps(self.data, sort_keys=True, indent=1, allow_nan=False).encode("utf-8")
        fd = os.open(staging, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.write(fd, payload)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(staging, self.path)
        dir_fd = os.open(self.path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

    def close(self) -> None:
        if self._lock_fd is not None:
            os.close(self._lock_fd)
            self._lock_fd = None


def _require_keys(payload: Any, keys: set[str]) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != keys:
        raise EditAuthorityError(400, "SCHEMA_INVALID", f"request must contain exactly {sorted(keys)}")
    return payload


def _require_str(payload: Mapping[str, Any], key: str, *, allow_empty: bool = False, limit: int = 128) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or (not value and not allow_empty) or len(value) > limit:
        raise EditAuthorityError(400, "SCHEMA_INVALID", f"{key} must be a string of at most {limit} characters")
    return value


class EditorEditAuthority:
    def __init__(self, *, policy: Mapping[str, Installation], ledger_path: Path,
                 clock: Callable[[], float] = time.time,
                 human_input_keys: Mapping[str, bytes] | None = None,
                 scene_packet_sha256: Callable[[str], str] | None = None) -> None:
        self._policy = dict(policy)
        # scene_id -> SHA-256 of the packet EngAIn delivers now (composition root); none -> no scene_ref verifies.
        self._scene_packet_sha256 = scene_packet_sha256
        # human_input client_id -> its secret (minted by the composition root); none -> nothing verifies.
        self._human_input_keys = dict(human_input_keys or {})
        self._clock = clock
        self._lock = threading.Lock()
        self._signer = _GrantSigner()
        self._signed: dict[str, dict[str, str]] = {}  # grant_id -> signed grant, memory only
        self._signed_promotions: dict[str, dict[str, str]] = {}  # promotion_id -> signed promotion grant
        self._ledger = _DurableLedger(ledger_path)
        # A restart rotates the signing key: every grant still outstanding can never verify again.
        data = self._ledger.data
        changed = False
        for grant_id, grant in data["grants"].items():
            if grant["state"] == "ISSUED":
                grant["state"] = "LOST"
                proposal = data["proposals"][grant["proposal_id"]]
                proposal["state"] = "AUTHORIZATION_LOST"
                self._event("grant_lost_on_restart", proposal["installation_id"], proposal_id=grant["proposal_id"], grant_id=grant_id)
                changed = True
        for promotion in data["promotions"].values():
            if promotion["state"] == "ISSUED":
                promotion["state"] = "LOST"
                self._event("promotion_lost_on_restart", promotion["installation_id"], promotion_id=promotion["promotion_id"])
                changed = True
        if changed:
            self._ledger.commit()

    # ---- helpers -------------------------------------------------------------------------------

    @property
    def public_key_pem(self) -> str:
        return self._signer.public_key_pem

    def verify_grant(self, grant_json: str, grant_signature_b64: str) -> bool:
        return self._signer.verify(grant_json, grant_signature_b64)

    def close(self) -> None:
        self._ledger.close()

    def _event(self, kind: str, installation_id: str, **fields: Any) -> None:
        self._ledger.data["events"].append({"kind": kind, "installation_id": installation_id, "at": self._clock(), **fields})

    def _refuse(self, client_id: str, route: str, status: int, code: str, message: str, **context: Any) -> EditAuthorityError:
        record_intent(issuer=client_id, command={"route": route, **context}, reason_rejected=code, message=message)
        return EditAuthorityError(status, code, message)

    def _installation(self, client_id: str, route: str, payload: Mapping[str, Any], roles: tuple[str, ...]) -> tuple[Installation, str]:
        installation_id = _require_str(payload, "installation_id")
        installation = self._policy.get(installation_id)
        if installation is None:
            raise self._refuse(client_id, route, 403, "INSTALLATION_NOT_AUTHORIZED",
                               "installation is not in the editor edit policy", installation_id=installation_id)
        for role in roles:
            if installation.client_for(role) == client_id:
                return installation, role
        raise self._refuse(client_id, route, 403, "CLIENT_ROLE_MISMATCH",
                           f"client is not this installation's {' or '.join(roles)}", installation_id=installation_id)

    def _install_state(self, installation_id: str) -> dict[str, Any]:
        return self._ledger.data["installations"].setdefault(
            installation_id, {"approval_mode": DEFAULT_APPROVAL_MODE, "state_seq": 0, "revert_slot": None})

    def _proposal(self, client_id: str, route: str, installation: Installation, proposal_id: Any) -> dict[str, Any]:
        proposal = self._ledger.data["proposals"].get(proposal_id) if isinstance(proposal_id, str) else None
        if proposal is None or proposal["installation_id"] != installation.installation_id:
            raise self._refuse(client_id, route, 404, "PROPOSAL_UNKNOWN", "no such proposal for this installation",
                               proposal_id=str(proposal_id))
        return proposal

    def _expire_if_due(self, grant_id: str, grant: dict[str, Any]) -> bool:
        if grant["state"] == "ISSUED" and self._clock() > grant["expires_at"]:
            grant["state"] = "EXPIRED"
            proposal = self._ledger.data["proposals"][grant["proposal_id"]]
            proposal["state"] = "AUTHORIZATION_EXPIRED"
            self._signed.pop(grant_id, None)
            self._event("grant_expired", proposal["installation_id"], proposal_id=grant["proposal_id"], grant_id=grant_id)
            return True
        return False

    # ---- mandates ------------------------------------------------------------------------------

    def _mandate(self, client_id: str, route: str, installation: Installation, mandate_id: Any) -> dict[str, Any]:
        mandate = self._ledger.data["mandates"].get(mandate_id) if isinstance(mandate_id, str) else None
        if mandate is None or mandate["installation_id"] != installation.installation_id:
            raise self._refuse(client_id, route, 404, "MANDATE_UNKNOWN", "no such mandate for this installation",
                               mandate_id=str(mandate_id))
        return mandate

    def _end_mandate(self, mandate: dict[str, Any], state: str, reason: str) -> None:
        """Terminal transition; every unconsumed grant issued under it becomes unusable."""
        mandate["state"], mandate["end_reason"], mandate["ended_at"] = state, reason, self._clock()
        for grant_id, grant in self._ledger.data["grants"].items():
            if grant.get("mandate_id") == mandate["mandate_id"] and grant["state"] == "ISSUED":
                grant["state"] = "VOID"
                self._ledger.data["proposals"][grant["proposal_id"]]["state"] = "AUTHORIZATION_REVOKED"
                self._signed.pop(grant_id, None)
        self._event("mandate_ended", mandate["installation_id"], mandate_id=mandate["mandate_id"], state=state, reason=reason)

    def _expire_mandates(self, installation_id: str) -> bool:
        changed = False
        for mandate in self._ledger.data["mandates"].values():
            if mandate["installation_id"] == installation_id and mandate["state"] in MANDATE_LIVE_STATES \
                    and self._clock() > mandate["expires_at"]:
                self._end_mandate(mandate, "EXPIRED", "expires_at passed")
                changed = True
        return changed

    def _in_flight(self, installation_id: str) -> str:
        """The operation that has been authorized but has not reported an outcome yet, or ""."""
        for grant_id, grant in self._ledger.data["grants"].items():
            proposal = self._ledger.data["proposals"][grant["proposal_id"]]
            if proposal["installation_id"] != installation_id:
                continue
            self._expire_if_due(grant_id, grant)
            if grant["state"] == "ISSUED" or proposal["state"] == "CONSUMED":
                return proposal["proposal_id"]
        for promotion in self._ledger.data["promotions"].values():
            if promotion["installation_id"] == installation_id:
                self._expire_promotion_if_due(promotion)
                if promotion["state"] in ("ISSUED", "CONSUMED"):
                    return promotion["promotion_id"]
        return ""

    def _expire_promotion_if_due(self, promotion: dict[str, Any]) -> bool:
        if promotion["state"] == "ISSUED" and self._clock() > promotion["expires_at"]:
            promotion["state"] = "EXPIRED"
            self._signed_promotions.pop(promotion["promotion_id"], None)
            self._event("promotion_expired", promotion["installation_id"], promotion_id=promotion["promotion_id"])
            return True
        return False

    @staticmethod
    def _mandate_view(mandate: dict[str, Any] | None) -> dict[str, Any] | None:
        if mandate is None:
            return None
        view = {k: copy.deepcopy(v) for k, v in mandate.items() if k not in ("edits", "approval")}
        view["edits_recorded"] = len(mandate["edits"])
        view["recent_edits"] = copy.deepcopy(mandate["edits"][-5:])
        return view

    def _latest(self, table: str, installation_id: str) -> dict[str, Any] | None:
        rows = [r for r in self._ledger.data[table].values() if r["installation_id"] == installation_id]
        return max(rows, key=lambda r: (r["created_at"], r.get("mandate_id", ""), r.get("promotion_id", ""))) if rows else None

    def _verified_scene_ref(self, client_id: str, route: str, ref: Any) -> dict[str, str]:
        """A scene_ref names the exact EngAIn packet the work is built from; it must match what EngAIn delivers now."""
        if not isinstance(ref, dict) or set(ref) != {"scene_id", "packet_sha256"} \
                or not isinstance(ref["scene_id"], str) or not ref["scene_id"] or len(ref["scene_id"]) > 256 \
                or not isinstance(ref["packet_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", ref["packet_sha256"]):
            raise self._refuse(client_id, route, 400, "SCHEMA_INVALID",
                               "scene_ref must be exactly {scene_id, packet_sha256 (64 lowercase hex)}")
        if self._scene_packet_sha256 is None:
            raise self._refuse(client_id, route, 503, "SCENE_REF_UNVERIFIABLE", "no EngAIn scene source is composed")
        try:
            current = self._scene_packet_sha256(ref["scene_id"])
        except (OSError, ValueError) as exc:
            raise self._refuse(client_id, route, 404, "SCENE_REF_UNKNOWN", f"EngAIn cannot deliver {ref['scene_id']!r}: {exc}")
        if current != ref["packet_sha256"]:
            raise self._refuse(client_id, route, 409, "SCENE_REF_STALE",
                               f"{ref['scene_id']} is now packet {current}, not {ref['packet_sha256']}")
        return {"scene_id": ref["scene_id"], "packet_sha256": current}

    def create_mandate(self, client_id: str, payload: Any) -> dict[str, Any]:
        route = "create_mandate"
        with self._lock:
            keys = {"installation_id", "mode", "goal", "writable_path_prefixes", "workspace_id", "max_edits", "ttl_s", "evidence"}
            payload = _require_keys(payload, keys | {"scene_ref"} if isinstance(payload, dict) and "scene_ref" in payload else keys)
            installation, _ = self._installation(client_id, route, payload, ("approver",))
            scene_ref = self._verified_scene_ref(client_id, route, payload["scene_ref"]) if "scene_ref" in payload else None
            mode = payload["mode"]
            if mode not in MANDATE_MODES:
                raise self._refuse(client_id, route, 400, "SCHEMA_INVALID", f"mode must be one of {MANDATE_MODES}")
            if mode not in installation.mandate_modes:
                raise self._refuse(client_id, route, 403, "MANDATE_MODE_NOT_PERMITTED",
                                   f"the edit policy does not permit {mode} mandates for this installation")
            goal = payload["goal"]
            if not isinstance(goal, str) or not goal.strip() or len(goal.encode("utf-8")) > MAX_GOAL_BYTES:
                raise self._refuse(client_id, route, 400, "SCHEMA_INVALID", f"goal must be 1..{MAX_GOAL_BYTES} UTF-8 bytes")
            for key, low, high in (("max_edits", 1, MAX_MANDATE_EDITS), ("ttl_s", MIN_MANDATE_TTL_S, MAX_MANDATE_TTL_S)):
                value = payload[key]
                if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
                    raise self._refuse(client_id, route, 400, "SCHEMA_INVALID", f"{key} must be an integer {low}..{high}")
            evidence = _require_keys(payload["evidence"], {"dock_instance_id"})
            _require_str(evidence, "dock_instance_id")
            prefixes, workspace_id = payload["writable_path_prefixes"], payload["workspace_id"]
            if not isinstance(prefixes, list) or not prefixes or len(set(prefixes)) != len(prefixes) \
                    or not all(isinstance(p, str) for p in prefixes):
                raise self._refuse(client_id, route, 400, "SCHEMA_INVALID", "writable_path_prefixes must be a non-empty unique list")
            if mode == "FULL_SCENE":
                # The open project: one scene folder, inside what the policy already allows.
                if workspace_id != "" or len(prefixes) != 1 or not _safe_relative_path(prefixes[0]) \
                        or not prefixes[0].endswith("/"):
                    raise self._refuse(client_id, route, 400, "SCHEMA_INVALID",
                                       "FULL_SCENE takes exactly one project folder ending in '/' and no workspace")
                if not any(_under(prefixes[0], p) for p in installation.writable_path_prefixes) \
                        or any(_under(prefixes[0], p) for p in installation.protected_paths):
                    raise self._refuse(client_id, route, 403, "SCOPE_NOT_PERMITTED",
                                       "the folder is outside this installation's writable prefixes or inside a protected path")
            else:
                # An isolated workspace, never the open project (Foundry keeps the game in <workspace>/game/).
                if not isinstance(workspace_id, str) or not _WORKSPACE_ID.fullmatch(workspace_id) \
                        or not all(_safe_relative_path(p) and p.endswith("/") for p in prefixes):
                    raise self._refuse(client_id, route, 400, "SCHEMA_INVALID",
                                       "ENTIRE_GAME needs a workspace_id (ws_...) and workspace folders ending in '/'")
            self._expire_mandates(installation.installation_id)
            active = [m for m in self._ledger.data["mandates"].values()
                      if m["installation_id"] == installation.installation_id and m["state"] == "ACTIVE"]
            if active:
                raise self._refuse(client_id, route, 409, "MANDATE_ALREADY_ACTIVE",
                                   f"mandate {active[0]['mandate_id']} is still active; stop it before approving another")
            busy = self._in_flight(installation.installation_id)
            if busy:
                raise self._refuse(client_id, route, 409, "OPERATION_IN_FLIGHT",
                                   f"{busy} is authorized or running; wait for its outcome")
            now = int(self._clock())
            mandate = {
                "mandate_id": "mandate_" + secrets.token_hex(8), "installation_id": installation.installation_id,
                "project_id": installation.project_id, "mode": mode, "goal": goal, "goal_sha256": body_sha256(goal),
                "workspace_id": workspace_id, "writable_path_prefixes": list(prefixes),
                # An isolated workspace protects nothing of the open project (promotion re-applies the policy).
                "protected_paths": [] if workspace_id else list(installation.protected_paths),
                "max_edits": payload["max_edits"],
                "edits_authorized": 0, "created_at": now, "expires_at": now + payload["ttl_s"], "state": "ACTIVE",
                "end_reason": "", "ended_at": None, "summary": "", "edits": [],
                "approval": {"approved_by_client": client_id, "evidence": dict(evidence), "at": now},
            }
            if scene_ref is not None:
                mandate["scene_ref"] = scene_ref
            self._ledger.data["mandates"][mandate["mandate_id"]] = mandate
            self._event("mandate_created", installation.installation_id, mandate_id=mandate["mandate_id"], mode=mode,
                        goal_sha256=mandate["goal_sha256"], workspace_id=workspace_id, writable_path_prefixes=list(prefixes),
                        max_edits=mandate["max_edits"], expires_at=mandate["expires_at"], scene_ref=scene_ref)
            self._ledger.commit()
            return self._mandate_view(mandate)

    def revoke_mandate(self, client_id: str, payload: Any) -> dict[str, Any]:
        """The human's Stop: ends the mandate now; an edit already running reports its outcome as usual."""
        route = "revoke_mandate"
        with self._lock:
            payload = _require_keys(payload, {"installation_id", "mandate_id", "evidence"})
            installation, _ = self._installation(client_id, route, payload, ("approver",))
            _require_str(_require_keys(payload["evidence"], {"dock_instance_id"}), "dock_instance_id")
            mandate = self._mandate(client_id, route, installation, payload["mandate_id"])
            self._expire_mandates(installation.installation_id)
            if mandate["state"] not in MANDATE_LIVE_STATES:
                self._ledger.commit()
                raise self._refuse(client_id, route, 409, "MANDATE_NOT_ACTIVE", f"mandate is {mandate['state']}")
            self._end_mandate(mandate, "REVOKED", "stopped by the human")
            self._ledger.commit()
            return self._mandate_view(mandate)

    def complete_mandate(self, client_id: str, payload: Any) -> dict[str, Any]:
        """Dragon declares the goal reached. This can only end a mandate, never extend one."""
        route = "complete_mandate"
        with self._lock:
            payload = _require_keys(payload, {"installation_id", "mandate_id", "summary"})
            installation, _ = self._installation(client_id, route, payload, ("proposer",))
            summary = _require_str(payload, "summary", limit=MAX_GOAL_BYTES)
            mandate = self._mandate(client_id, route, installation, payload["mandate_id"])
            self._expire_mandates(installation.installation_id)
            if mandate["state"] not in MANDATE_LIVE_STATES:
                self._ledger.commit()
                raise self._refuse(client_id, route, 409, "MANDATE_NOT_ACTIVE", f"mandate is {mandate['state']}")
            mandate["summary"] = summary
            self._end_mandate(mandate, "COMPLETED", "Dragon declared the goal reached")
            self._ledger.commit()
            return self._mandate_view(mandate)

    def _authorize_under_mandate(self, client_id: str, route: str, installation: Installation,
                                 proposal: dict[str, Any], mandate: dict[str, Any]) -> dict[str, Any]:
        install = self._install_state(installation.installation_id)
        now = int(self._clock())
        mandate["edits_authorized"] += 1
        edit_index = mandate["edits_authorized"]
        grant = {
            "contract": GRANT_CONTRACT, "grant_id": secrets.token_hex(16), "authorization_id": secrets.token_hex(16),
            "proposal_id": proposal["proposal_id"], "body_sha256": proposal["body_sha256"],
            "installation_id": installation.installation_id, "project_id": installation.project_id,
            "executor_actor_id": installation.executor_actor_id, "executor_client_id": installation.executor_client_id,
            "operation_class": installation.operation_class,
            "writable_path_prefixes": list(mandate["writable_path_prefixes"]),
            "protected_paths": list(mandate["protected_paths"]),
            "base_state_seq": install["state_seq"], "base_scope_sha256": "", "channel": "MANDATE",
            "issued_at": now, "expires_at": min(now + GRANT_TTL_S, int(mandate["expires_at"])),
            "mandate_id": mandate["mandate_id"], "workspace_id": mandate["workspace_id"],
        }
        signed = self._signer.sign(grant)
        proposal["state"] = "AUTHORIZED"
        proposal["authorization"] = {"authorization_id": grant["authorization_id"], "grant_id": grant["grant_id"],
                                     "channel": "MANDATE", "accepted_by_client": client_id,
                                     "evidence": {"mandate_id": mandate["mandate_id"], "edit_index": edit_index}, "at": now}
        self._ledger.data["grants"][grant["grant_id"]] = {
            "proposal_id": proposal["proposal_id"], "state": "ISSUED", "expires_at": grant["expires_at"],
            "base_state_seq": grant["base_state_seq"], "base_scope_sha256": "", "channel": "MANDATE",
            "mandate_id": mandate["mandate_id"], "workspace_id": mandate["workspace_id"],
            "writable_path_prefixes": grant["writable_path_prefixes"], "protected_paths": grant["protected_paths"]}
        if edit_index >= mandate["max_edits"]:
            mandate["state"] = "EXHAUSTED"
        self._event("proposal_authorized", installation.installation_id, proposal_id=proposal["proposal_id"],
                    grant_id=grant["grant_id"], channel="MANDATE", mandate_id=mandate["mandate_id"], edit_index=edit_index)
        self._signed[grant["grant_id"]] = signed
        return {"mandate_id": mandate["mandate_id"], "edit_index": edit_index, "max_edits": mandate["max_edits"],
                "expires_at": grant["expires_at"]}

    # ---- promotion ------------------------------------------------------------------------------

    def create_promotion(self, client_id: str, payload: Any) -> dict[str, Any]:
        route = "create_promotion"
        with self._lock:
            payload = _require_keys(payload, {"installation_id", "mandate_id", "manifest", "base_scope_sha256",
                                              "allow_editor_code", "evidence"})
            installation, _ = self._installation(client_id, route, payload, ("approver",))
            _require_str(_require_keys(payload["evidence"], {"dock_instance_id"}), "dock_instance_id")
            mandate = self._mandate(client_id, route, installation, payload["mandate_id"])
            if not mandate["workspace_id"]:
                raise self._refuse(client_id, route, 409, "NOT_A_WORKSPACE_MANDATE", "only an ENTIRE_GAME workspace is promoted")
            self._expire_mandates(installation.installation_id)
            if mandate["state"] == "ACTIVE":
                self._ledger.commit()
                raise self._refuse(client_id, route, 409, "MANDATE_STILL_ACTIVE", "stop or finish the mandate before promoting")
            busy = self._in_flight(installation.installation_id)
            if busy:
                raise self._refuse(client_id, route, 409, "OPERATION_IN_FLIGHT", f"{busy} is authorized or running")
            if any(p["mandate_id"] == mandate["mandate_id"] and p["state"] == "COMPLETED"
                   for p in self._ledger.data["promotions"].values()):
                raise self._refuse(client_id, route, 409, "PROMOTION_DUPLICATE", "this workspace was already promoted")
            manifest, allow = payload["manifest"], payload["allow_editor_code"]
            if not isinstance(allow, bool) or not isinstance(payload["base_scope_sha256"], str) \
                    or not _HEX64.fullmatch(payload["base_scope_sha256"]):
                raise self._refuse(client_id, route, 400, "SCHEMA_INVALID", "allow_editor_code bool, base_scope_sha256 hex")
            if not isinstance(manifest, list) or not 1 <= len(manifest) <= MAX_CHANGED_PATHS:
                raise self._refuse(client_id, route, 400, "SCHEMA_INVALID", "manifest must list 1.. files")
            paths, editor_code = [], []
            for entry in manifest:
                if not isinstance(entry, dict) or set(entry) != {"path", "sha256", "editor_code"} \
                        or not _safe_relative_path(entry["path"]) or entry["path"].endswith("/") \
                        or not isinstance(entry["sha256"], str) or not _HEX64.fullmatch(entry["sha256"]) \
                        or not isinstance(entry["editor_code"], bool):
                    raise self._refuse(client_id, route, 400, "SCHEMA_INVALID", "manifest entries are {path, sha256, editor_code}")
                path = entry["path"]
                if not any(_under(path, p) for p in installation.writable_path_prefixes) \
                        or any(_under(path, p) for p in installation.protected_paths):
                    raise self._refuse(client_id, route, 403, "SCOPE_NOT_PERMITTED",
                                       f"{path} is outside this installation's writable prefixes or protected")
                paths.append(path)
                if entry["editor_code"] or is_editor_code_path(path):
                    editor_code.append(path)
            if len(set(paths)) != len(paths):
                raise self._refuse(client_id, route, 400, "SCHEMA_INVALID", "manifest paths must be unique")
            if editor_code and not allow:
                raise self._refuse(client_id, route, 409, "EDITOR_CODE_NOT_ALLOWED",
                                   "the manifest contains editor-executable files: " + ", ".join(sorted(editor_code)))
            ordered = sorted(manifest, key=lambda e: e["path"])
            manifest_sha = body_sha256(json.dumps(ordered, sort_keys=True, separators=(",", ":")))
            now = int(self._clock())
            install = self._install_state(installation.installation_id)
            promotion_id = "promotion_" + secrets.token_hex(8)
            grant = {
                "contract": PROMOTION_GRANT_CONTRACT, "grant_id": secrets.token_hex(16), "promotion_id": promotion_id,
                "mandate_id": mandate["mandate_id"], "workspace_id": mandate["workspace_id"],
                "installation_id": installation.installation_id, "project_id": installation.project_id,
                "executor_actor_id": installation.executor_actor_id, "executor_client_id": installation.executor_client_id,
                "manifest_sha256": manifest_sha, "editor_code_paths": sorted(editor_code),
                "base_state_seq": install["state_seq"], "base_scope_sha256": payload["base_scope_sha256"],
                "writable_path_prefixes": list(installation.writable_path_prefixes),
                "protected_paths": list(installation.protected_paths),
                "issued_at": now, "expires_at": now + GRANT_TTL_S,
            }
            signed = self._signer.sign(grant)
            self._ledger.data["promotions"][promotion_id] = {
                "promotion_id": promotion_id, "installation_id": installation.installation_id,
                "mandate_id": mandate["mandate_id"], "workspace_id": mandate["workspace_id"], "grant_id": grant["grant_id"],
                "manifest": ordered, "manifest_sha256": manifest_sha, "editor_code_paths": sorted(editor_code),
                "allow_editor_code": allow, "base_state_seq": grant["base_state_seq"],
                "base_scope_sha256": grant["base_scope_sha256"], "created_at": now, "expires_at": grant["expires_at"],
                "state": "ISSUED", "approval": {"approved_by_client": client_id, "evidence": dict(payload["evidence"]), "at": now},
                "outcome": None,
            }
            self._event("promotion_authorized", installation.installation_id, promotion_id=promotion_id,
                        mandate_id=mandate["mandate_id"], manifest_sha256=manifest_sha, file_count=len(paths),
                        editor_code_count=len(editor_code))
            self._ledger.commit()
            self._signed_promotions[promotion_id] = signed
            return {"promotion_id": promotion_id, "state": "AUTHORIZED", "manifest_sha256": manifest_sha,
                    "editor_code_paths": sorted(editor_code), "expires_at": grant["expires_at"]}

    def consume_promotion(self, client_id: str, payload: Any) -> dict[str, Any]:
        route = "consume_promotion"
        with self._lock:
            payload = _require_keys(payload, {"installation_id", "grant_id", "promotion_id", "manifest_sha256",
                                              "current_scope_sha256"})
            installation, _ = self._installation(client_id, route, payload, ("executor",))
            promotion = self._ledger.data["promotions"].get(payload["promotion_id"]) \
                if isinstance(payload["promotion_id"], str) else None
            if promotion is None or promotion["installation_id"] != installation.installation_id \
                    or promotion["grant_id"] != payload["grant_id"]:
                raise self._refuse(client_id, route, 404, "GRANT_UNKNOWN", "no such promotion grant")
            if self._expire_promotion_if_due(promotion):
                self._ledger.commit()
                raise self._refuse(client_id, route, 410, "GRANT_EXPIRED", "promotion grant expired; approve again")
            if promotion["state"] != "ISSUED":
                raise self._refuse(client_id, route, 409, "GRANT_NOT_CONSUMABLE", f"promotion is {promotion['state']}")
            if payload["manifest_sha256"] != promotion["manifest_sha256"]:
                raise self._refuse(client_id, route, 409, "MANIFEST_MISMATCH", "files differ from the approved manifest")
            install = self._install_state(installation.installation_id)
            if payload["current_scope_sha256"] != promotion["base_scope_sha256"] or install["state_seq"] != promotion["base_state_seq"]:
                promotion["state"] = "STALE"
                self._signed_promotions.pop(promotion["promotion_id"], None)
                self._event("promotion_stale", installation.installation_id, promotion_id=promotion["promotion_id"])
                self._ledger.commit()
                raise self._refuse(client_id, route, 409, "TARGET_STATE_CHANGED",
                                   "the project changed after the promotion was approved; nothing was copied")
            promotion["state"] = "CONSUMED"
            self._signed_promotions.pop(promotion["promotion_id"], None)
            self._event("promotion_consumed", installation.installation_id, promotion_id=promotion["promotion_id"])
            self._ledger.commit()
            return {"promotion_id": promotion["promotion_id"], "state": "CONSUMED"}

    def _record_promotion_outcome(self, client_id: str, route: str, payload: Any) -> dict[str, Any]:
        payload = _require_keys(payload, {"installation_id", "kind", "promotion_id", "grant_id", "edit_id", "ok",
                                          "receipt_state", "changed_paths"})
        installation, _ = self._installation(client_id, route, payload, ("executor",))
        promotion = self._ledger.data["promotions"].get(payload["promotion_id"]) if isinstance(payload["promotion_id"], str) else None
        if promotion is None or promotion["installation_id"] != installation.installation_id \
                or promotion["grant_id"] != payload["grant_id"] or promotion["state"] != "CONSUMED":
            raise self._refuse(client_id, route, 409, "OUTCOME_NOT_EXPECTED", "no consumed promotion awaits this outcome")
        changed = payload["changed_paths"]
        if not isinstance(changed, list) or not all(isinstance(v, str) for v in changed) or not isinstance(payload["ok"], bool) \
                or payload["receipt_state"] not in ("", "AVAILABLE", "ERROR"):
            raise self._refuse(client_id, route, 400, "SCHEMA_INVALID", "changed_paths list, ok bool, receipt_state")
        edit_id = _require_str(payload, "edit_id", allow_empty=True)
        if bool(changed) != bool(edit_id) or bool(changed) != bool(payload["receipt_state"]):
            raise self._refuse(client_id, route, 400, "SCHEMA_INVALID", "edit_id and receipt_state are present exactly when files changed")
        outside = sorted(set(changed) - {e["path"] for e in promotion["manifest"]})
        promotion["state"] = "COMPLETED" if payload["ok"] and not outside else "FAILED"
        promotion["outcome"] = {"edit_id": edit_id, "ok": payload["ok"], "receipt_state": payload["receipt_state"],
                                "changed_paths": changed, "outside_manifest": outside, "at": self._clock()}
        install = self._install_state(installation.installation_id)
        if changed:
            install["state_seq"] += 1
            install["revert_slot"] = {"edit_id": edit_id, "proposal_id": promotion["promotion_id"],
                                      "receipt_state": payload["receipt_state"],
                                      "revertible": payload["receipt_state"] == "AVAILABLE",
                                      "turn_ok": payload["ok"], "at": self._clock()}
        self._event("promotion_outcome", installation.installation_id, promotion_id=promotion["promotion_id"],
                    edit_id=edit_id, ok=payload["ok"], changed_path_count=len(changed), outside_manifest=outside)
        self._ledger.commit()
        return {"promotion_id": promotion["promotion_id"], "state": promotion["state"],
                "revert_slot": copy.deepcopy(install["revert_slot"])}

    # ---- routes ---------------------------------------------------------------------------------

    def register_proposal(self, client_id: str, payload: Any) -> dict[str, Any]:
        route = "register_proposal"
        with self._lock:
            keys = {"installation_id", "proposal_id", "body", "body_sha256", "client_request_id", "dragon_session_id"}
            payload = _require_keys(payload, keys | {"mandate_id"} if isinstance(payload, dict) and "mandate_id" in payload else keys)
            installation, _ = self._installation(client_id, route, payload, ("proposer",))
            proposal_id = payload["proposal_id"]
            if not isinstance(proposal_id, str) or not _PROPOSAL_ID.fullmatch(proposal_id):
                raise self._refuse(client_id, route, 400, "SCHEMA_INVALID", "proposal_id has the wrong form")
            body = payload["body"]
            if not isinstance(body, str) or not body.strip() or len(body.encode("utf-8")) > MAX_BODY_BYTES:
                raise self._refuse(client_id, route, 400, "SCHEMA_INVALID", f"body must be 1..{MAX_BODY_BYTES} UTF-8 bytes")
            if payload["body_sha256"] != body_sha256(body):
                raise self._refuse(client_id, route, 400, "BODY_HASH_MISMATCH", "body_sha256 is not the sha256 of body",
                                   proposal_id=proposal_id)
            client_request_id = _require_str(payload, "client_request_id")
            dragon_session_id = _require_str(payload, "dragon_session_id", allow_empty=True)
            if proposal_id in self._ledger.data["proposals"]:
                raise self._refuse(client_id, route, 409, "PROPOSAL_DUPLICATE", "proposal_id already registered",
                                   proposal_id=proposal_id)
            mandate = None
            if "mandate_id" in payload:
                mandate = self._mandate(client_id, route, installation, payload["mandate_id"])
                if self._expire_mandates(installation.installation_id):
                    self._ledger.commit()
                if mandate["state"] != "ACTIVE":
                    raise self._refuse(client_id, route, 409, "MANDATE_NOT_ACTIVE", f"mandate is {mandate['state']}",
                                       proposal_id=proposal_id)
                busy = self._in_flight(installation.installation_id)
                if busy:  # one edit at a time: the next proposal waits for this one's outcome
                    raise self._refuse(client_id, route, 409, "OPERATION_IN_FLIGHT",
                                       f"{busy} is authorized or running; wait for its outcome", proposal_id=proposal_id)
            self._install_state(installation.installation_id)
            self._ledger.data["proposals"][proposal_id] = {
                "contract": PROPOSAL_CONTRACT, "proposal_id": proposal_id,
                "installation_id": installation.installation_id, "project_id": installation.project_id,
                "proposer_actor_id": installation.proposer_actor_id, "executor_actor_id": installation.executor_actor_id,
                "body": body, "body_sha256": payload["body_sha256"], "client_request_id": client_request_id,
                "dragon_session_id": dragon_session_id, "created_at": self._clock(), "state": "PENDING",
                "authorization": None, "consumption": None, "outcome": None, "rejection": None,
                "mandate_id": mandate["mandate_id"] if mandate else "",
            }
            self._event("proposal_registered", installation.installation_id, proposal_id=proposal_id)
            reply = {"proposal_id": proposal_id, "state": "PENDING", "code": proposal_code(proposal_id)}
            if mandate is not None:
                reply.update(self._authorize_under_mandate(client_id, route, installation,
                                                           self._ledger.data["proposals"][proposal_id], mandate),
                             state="AUTHORIZED")
            self._ledger.commit()
            return reply

    def state(self, client_id: str, payload: Any) -> dict[str, Any]:
        with self._lock:
            payload = _require_keys(payload, {"installation_id"})
            installation, _ = self._installation(client_id, "state", payload, ("proposer", "executor", "approver"))
            if self._expire_mandates(installation.installation_id):
                self._ledger.commit()
            install = copy.deepcopy(self._install_state(installation.installation_id))
            promotion = self._latest("promotions", installation.installation_id)
            pending = [
                {"proposal_id": p["proposal_id"], "code": proposal_code(p["proposal_id"]), "body": p["body"],
                 "body_sha256": p["body_sha256"], "created_at": p["created_at"]}
                for p in sorted(self._ledger.data["proposals"].values(), key=lambda p: p["proposal_id"])
                if p["installation_id"] == installation.installation_id and p["state"] == "PENDING"
            ]
            return {"approval_mode": install["approval_mode"], "state_seq": install["state_seq"],
                    "revert_slot": install["revert_slot"], "pending": pending,
                    "operation_class": installation.operation_class,
                    "writable_path_prefixes": list(installation.writable_path_prefixes),
                    "protected_paths": list(installation.protected_paths),
                    "mandate_modes": list(installation.mandate_modes),
                    "mandate": self._mandate_view(self._latest("mandates", installation.installation_id)),
                    "promotion": None if promotion is None else {
                        k: copy.deepcopy(promotion[k]) for k in ("promotion_id", "mandate_id", "state", "manifest_sha256",
                                                                 "editor_code_paths", "created_at", "outcome")}}

    def set_approval_mode(self, client_id: str, payload: Any) -> dict[str, Any]:
        route = "set_approval_mode"
        with self._lock:
            payload = _require_keys(payload, {"installation_id", "mode", "previous_mode"})
            installation, _ = self._installation(client_id, route, payload, ("approver",))
            if payload["mode"] not in APPROVAL_MODES:
                raise self._refuse(client_id, route, 400, "SCHEMA_INVALID", f"mode must be one of {APPROVAL_MODES}")
            install = self._install_state(installation.installation_id)
            if payload["previous_mode"] != install["approval_mode"]:
                raise self._refuse(client_id, route, 409, "APPROVAL_MODE_CHANGED",
                                   f"approval mode is {install['approval_mode']}, not {payload['previous_mode']}")
            if payload["mode"] != install["approval_mode"]:
                install["approval_mode"] = payload["mode"]
                # Recorded only: no proposal, authorization or grant is read or written here.
                self._event("approval_mode_set", installation.installation_id,
                            mode=payload["mode"], previous_mode=payload["previous_mode"])
                self._ledger.commit()
            return {"approval_mode": install["approval_mode"]}

    def accept(self, client_id: str, payload: Any) -> dict[str, Any]:
        route = "accept"
        with self._lock:
            payload = _require_keys(payload, {"installation_id", "proposal_id", "body_sha256", "channel", "evidence",
                                              "base_scope_sha256"})
            channel = payload["channel"]
            if channel not in CHANNEL_ROLE:
                raise self._refuse(client_id, route, 400, "SCHEMA_INVALID", f"channel must be one of {APPROVAL_MODES}")
            installation, _ = self._installation(client_id, route, payload, (CHANNEL_ROLE[channel],))
            if not isinstance(payload["base_scope_sha256"], str) or not _HEX64.fullmatch(payload["base_scope_sha256"]):
                raise self._refuse(client_id, route, 400, "SCHEMA_INVALID", "base_scope_sha256 must be 64 lowercase hex")
            install = self._install_state(installation.installation_id)
            proposal_id = payload["proposal_id"]
            if channel != install["approval_mode"]:
                raise self._refuse(client_id, route, 409, "APPROVAL_MODE_MISMATCH",
                                   f"approval mode is {install['approval_mode']}; {channel} acceptance refused",
                                   proposal_id=str(proposal_id))
            proposal = self._proposal(client_id, route, installation, proposal_id)
            if proposal["state"] != "PENDING":
                raise self._refuse(client_id, route, 409, "PROPOSAL_NOT_PENDING", f"proposal is {proposal['state']}",
                                   proposal_id=proposal_id)
            if payload["body_sha256"] != proposal["body_sha256"]:
                raise self._refuse(client_id, route, 409, "BODY_HASH_MISMATCH",
                                   "accepted bytes differ from the registered proposal", proposal_id=proposal_id)
            evidence = self._validate_evidence(client_id, route, channel, payload["evidence"], proposal, installation, "accept")
            now = int(self._clock())
            authorization_id = secrets.token_hex(16)
            grant = {
                "contract": GRANT_CONTRACT, "grant_id": secrets.token_hex(16), "authorization_id": authorization_id,
                "proposal_id": proposal_id, "body_sha256": proposal["body_sha256"],
                "installation_id": installation.installation_id, "project_id": installation.project_id,
                "executor_actor_id": installation.executor_actor_id, "executor_client_id": installation.executor_client_id,
                "operation_class": installation.operation_class,
                "writable_path_prefixes": list(installation.writable_path_prefixes),
                "protected_paths": list(installation.protected_paths),
                "base_state_seq": install["state_seq"], "base_scope_sha256": payload["base_scope_sha256"],
                "channel": channel,
                "issued_at": now, "expires_at": now + GRANT_TTL_S, "mandate_id": "", "workspace_id": "",
            }
            signed = self._signer.sign(grant)
            proposal["state"] = "AUTHORIZED"
            proposal["authorization"] = {"authorization_id": authorization_id, "grant_id": grant["grant_id"],
                                         "channel": channel, "accepted_by_client": client_id,
                                         "evidence": evidence, "at": now}
            self._ledger.data["grants"][grant["grant_id"]] = {
                "proposal_id": proposal_id, "state": "ISSUED", "expires_at": grant["expires_at"],
                "base_state_seq": grant["base_state_seq"], "base_scope_sha256": grant["base_scope_sha256"],
                "channel": channel}
            self._event("proposal_authorized", installation.installation_id, proposal_id=proposal_id,
                        grant_id=grant["grant_id"], channel=channel)
            self._ledger.commit()
            self._signed[grant["grant_id"]] = signed
            # The acceptor never receives the grant: only the executor can pick it up.
            return {"proposal_id": proposal_id, "state": "AUTHORIZED", "authorization_id": authorization_id,
                    "expires_at": grant["expires_at"]}

    def _validate_evidence(self, client_id: str, route: str, channel: str, evidence: Any,
                           proposal: Mapping[str, Any], installation: Installation, action: str) -> dict[str, Any]:
        proposal_id = proposal["proposal_id"]
        if channel == "MANUAL_ACCEPT":
            evidence = _require_keys(evidence, {"dock_instance_id"})
            _require_str(evidence, "dock_instance_id")
            return dict(evidence)
        evidence = _require_keys(evidence, {"client_request_id", "player_input", "reference", "attestation"})
        _require_str(evidence, "client_request_id")
        player_input = _require_str(evidence, "player_input", limit=256)
        attestation = self._verify_human_input(client_id, route, evidence["attestation"], installation, proposal, player_input)
        parsed = parse_confirmation(player_input)
        if parsed is None:
            raise self._refuse(client_id, route, 400, "NOT_A_CONFIRMATION",
                               "the typed text is not an exact `accept <code>` / `reject <code>`", proposal_id=proposal_id)
        if parsed[0] != action:
            raise self._refuse(client_id, route, 409, "CONFIRMATION_ACTION_MISMATCH",
                               f"the human typed {parsed[0]!r}, not {action!r}", proposal_id=proposal_id)
        if parsed[1] != evidence["reference"] or parsed[1] not in (proposal_id, proposal_code(proposal_id)):
            raise self._refuse(client_id, route, 409, "REFERENCE_MISMATCH",
                               "the confirmation does not reference this exact proposal", proposal_id=proposal_id)
        return {"client_request_id": evidence["client_request_id"], "player_input_sha256": body_sha256(player_input),
                "reference": parsed[1], "human_input": attestation}

    def _verify_human_input(self, client_id: str, route: str, attestation: Any, installation: Installation,
                            proposal: Mapping[str, Any], player_input: str) -> dict[str, Any]:
        """The human-input boundary's signature over exactly this typed text; anything else is refused."""
        import hmac
        proposal_id = proposal["proposal_id"]

        def unverified(message: str) -> EditAuthorityError:
            return self._refuse(client_id, route, 403, "HUMAN_INPUT_UNVERIFIED", message, proposal_id=proposal_id)

        if not isinstance(attestation, dict) or set(attestation) != HUMAN_INPUT_FIELDS:
            raise unverified(f"a conversational confirmation needs the human-input attestation {sorted(HUMAN_INPUT_FIELDS)}")
        issued_at = attestation["issued_at"]
        if attestation["contract"] != HUMAN_INPUT_CONTRACT or not isinstance(issued_at, int) or isinstance(issued_at, bool) \
                or not all(isinstance(attestation[k], str) for k in HUMAN_INPUT_FIELDS - {"issued_at"}) \
                or not _REQUEST_ID.fullmatch(attestation["request_id"]) or not _HEX32.fullmatch(attestation["nonce"]) \
                or not _HEX64.fullmatch(attestation["player_input_sha256"]) or not _HEX64.fullmatch(attestation["signature"]):
            raise unverified("the human-input attestation is malformed")
        if attestation["client_id"] != installation.human_input_client_id \
                or attestation["installation_id"] != installation.installation_id:
            raise unverified("the attestation was not made by this installation's human-input binding")
        secret = self._human_input_keys.get(installation.human_input_client_id)
        if secret is None:
            raise unverified("no human-input credential is provisioned for this installation")
        if not hmac.compare_digest(sign_human_input(secret, attestation), attestation["signature"]):
            raise unverified("the human-input signature does not verify")
        if attestation["player_input_sha256"] != body_sha256(player_input):
            raise unverified("the attested input is not the submitted confirmation text")
        now = self._clock()
        if issued_at > now + ATTESTATION_SKEW_S or now - issued_at > ATTESTATION_MAX_AGE_S:
            raise self._refuse(client_id, route, 409, "ATTESTATION_STALE", "the typed confirmation is too old or from the future",
                               proposal_id=proposal_id)
        if issued_at < proposal["created_at"] - ATTESTATION_SKEW_S:
            raise self._refuse(client_id, route, 409, "ATTESTATION_PREDATES_PROPOSAL",
                               "the confirmation was typed before this proposal existed", proposal_id=proposal_id)
        for other in self._ledger.data["proposals"].values():
            for decision in (other["authorization"], other["rejection"]):
                used = ((decision or {}).get("evidence") or {}).get("human_input")
                if used and (used["nonce"] == attestation["nonce"] or used["request_id"] == attestation["request_id"]):
                    raise self._refuse(client_id, route, 409, "ATTESTATION_REPLAYED",
                                       "this typed confirmation was already used", proposal_id=proposal_id)
        return {k: attestation[k] for k in ("client_id", "request_id", "issued_at", "nonce")}

    def reject(self, client_id: str, payload: Any) -> dict[str, Any]:
        route = "reject"
        with self._lock:
            payload = _require_keys(payload, {"installation_id", "proposal_id", "channel", "evidence"})
            channel = payload["channel"]
            if channel not in CHANNEL_ROLE:
                raise self._refuse(client_id, route, 400, "SCHEMA_INVALID", f"channel must be one of {APPROVAL_MODES}")
            installation, _ = self._installation(client_id, route, payload, (CHANNEL_ROLE[channel],))
            proposal = self._proposal(client_id, route, installation, payload["proposal_id"])
            if proposal["state"] != "PENDING":
                raise self._refuse(client_id, route, 409, "PROPOSAL_NOT_PENDING", f"proposal is {proposal['state']}",
                                   proposal_id=proposal["proposal_id"])
            evidence = self._validate_evidence(client_id, route, channel, payload["evidence"], proposal, installation, "reject")
            proposal["state"] = "REJECTED"
            proposal["rejection"] = {"channel": channel, "client": client_id, "evidence": evidence, "at": self._clock()}
            self._event("proposal_rejected", installation.installation_id, proposal_id=proposal["proposal_id"])
            self._ledger.commit()  # revert slot and state_seq deliberately untouched
            return {"proposal_id": proposal["proposal_id"], "state": "REJECTED"}

    def pickup(self, client_id: str, payload: Any) -> dict[str, Any]:
        with self._lock:
            payload = _require_keys(payload, {"installation_id"})
            installation, _ = self._installation(client_id, "pickup", payload, ("executor",))
            grants, changed = [], self._expire_mandates(installation.installation_id)   # first: it voids their grants
            for grant_id, grant in self._ledger.data["grants"].items():
                proposal = self._ledger.data["proposals"][grant["proposal_id"]]
                if proposal["installation_id"] != installation.installation_id:
                    continue
                if self._expire_if_due(grant_id, grant):
                    changed = True
                elif grant["state"] == "ISSUED" and grant_id in self._signed:
                    grants.append(dict(self._signed[grant_id]))
            promotions = []
            for promotion in self._ledger.data["promotions"].values():
                if promotion["installation_id"] != installation.installation_id:
                    continue
                if self._expire_promotion_if_due(promotion):
                    changed = True
                elif promotion["state"] == "ISSUED" and promotion["promotion_id"] in self._signed_promotions:
                    promotions.append(dict(self._signed_promotions[promotion["promotion_id"]]))
            if changed:
                self._ledger.commit()
            return {"grants": grants, "promotions": promotions}

    def consume(self, client_id: str, payload: Any) -> dict[str, Any]:
        route = "consume"
        with self._lock:
            payload = _require_keys(payload, {"installation_id", "grant_id", "proposal_id", "body_sha256", "current_scope_sha256"})
            installation, _ = self._installation(client_id, route, payload, ("executor",))
            grant_id = payload["grant_id"]
            grant = self._ledger.data["grants"].get(grant_id) if isinstance(grant_id, str) else None
            if grant is None or grant["proposal_id"] != payload["proposal_id"]:
                raise self._refuse(client_id, route, 404, "GRANT_UNKNOWN", "no such grant for this proposal")
            proposal = self._proposal(client_id, route, installation, payload["proposal_id"])
            if grant.get("mandate_id") and self._expire_mandates(installation.installation_id):
                self._ledger.commit()      # an expired mandate has voided this grant
            if self._expire_if_due(grant_id, grant):
                self._ledger.commit()
                raise self._refuse(client_id, route, 410, "GRANT_EXPIRED", "grant expired; it is never reissued",
                                   proposal_id=proposal["proposal_id"])
            if grant["state"] != "ISSUED" or proposal["state"] != "AUTHORIZED":
                raise self._refuse(client_id, route, 409, "GRANT_NOT_CONSUMABLE",
                                   f"grant is {grant['state']}, proposal is {proposal['state']}", proposal_id=proposal["proposal_id"])
            if payload["body_sha256"] != proposal["body_sha256"]:
                raise self._refuse(client_id, route, 409, "BODY_HASH_MISMATCH", "executed bytes differ from the approved proposal",
                                   proposal_id=proposal["proposal_id"])
            tree = payload["current_scope_sha256"]
            if not isinstance(tree, str) or not _HEX64.fullmatch(tree):
                raise self._refuse(client_id, route, 400, "SCHEMA_INVALID", "current_scope_sha256 must be 64 lowercase hex")
            install = self._install_state(installation.installation_id)
            # A mandate grant has no per-edit approval moment to compare with: the staged turn's own
            # conflict check (Foundry) still refuses to overwrite anything changed during the turn.
            scope_moved = bool(grant["base_scope_sha256"]) and tree != grant["base_scope_sha256"]
            if install["state_seq"] != grant["base_state_seq"] or scope_moved:
                grant["state"] = "VOID"
                proposal["state"] = "AUTHORIZATION_STALE"
                self._signed.pop(grant_id, None)
                self._event("grant_stale", installation.installation_id, proposal_id=proposal["proposal_id"],
                            grant_id=grant_id, reason="scope_content_changed" if scope_moved else "state_seq_changed")
                self._ledger.commit()
                raise self._refuse(client_id, route, 409, "TARGET_STATE_CHANGED",
                                   "files in this grant's scope changed after approval (a manual edit, or another "
                                   "recorded edit or revert); nothing was executed: propose and approve again",
                                   proposal_id=proposal["proposal_id"])
            grant["state"] = "CONSUMED"
            proposal["state"] = "CONSUMED"
            proposal["consumption"] = {"grant_id": grant_id, "scope_sha256": tree, "at": self._clock()}
            self._signed.pop(grant_id, None)
            self._event("grant_consumed", installation.installation_id, proposal_id=proposal["proposal_id"], grant_id=grant_id)
            self._ledger.commit()
            return {"proposal_id": proposal["proposal_id"], "state": "CONSUMED"}

    def record_outcome(self, client_id: str, payload: Any) -> dict[str, Any]:
        route = "record_outcome"
        with self._lock:
            kind = payload.get("kind") if isinstance(payload, dict) else None
            if kind == "edit":
                return self._record_edit_outcome(client_id, route, payload)
            if kind == "revert":
                return self._record_revert_outcome(client_id, route, payload)
            if kind == "promotion":
                return self._record_promotion_outcome(client_id, route, payload)
            raise EditAuthorityError(400, "SCHEMA_INVALID", "kind must be 'edit', 'revert' or 'promotion'")

    def _record_edit_outcome(self, client_id: str, route: str, payload: Any) -> dict[str, Any]:
        payload = _require_keys(payload, {"installation_id", "kind", "proposal_id", "grant_id", "edit_id", "turn_ok",
                                          "receipt_state", "changed_paths", "scope_violations"})
        installation, _ = self._installation(client_id, route, payload, ("executor",))
        proposal = self._proposal(client_id, route, installation, payload["proposal_id"])
        if proposal["state"] != "CONSUMED" or (proposal["consumption"] or {}).get("grant_id") != payload["grant_id"]:
            raise self._refuse(client_id, route, 409, "OUTCOME_NOT_EXPECTED",
                               f"proposal is {proposal['state']}; an outcome is recorded once, after consumption",
                               proposal_id=proposal["proposal_id"])
        changed, violations = payload["changed_paths"], payload["scope_violations"]
        for name, value in (("changed_paths", changed), ("scope_violations", violations)):
            if not isinstance(value, list) or len(value) > MAX_CHANGED_PATHS or not all(isinstance(v, str) and len(v) <= 512 for v in value):
                raise self._refuse(client_id, route, 400, "SCHEMA_INVALID", f"{name} must be a list of strings")
        if not isinstance(payload["turn_ok"], bool) or payload["receipt_state"] not in ("", "AVAILABLE", "ERROR"):
            raise self._refuse(client_id, route, 400, "SCHEMA_INVALID", "turn_ok must be boolean; receipt_state '', AVAILABLE or ERROR")
        edit_id = _require_str(payload, "edit_id", allow_empty=True)
        if bool(changed) != bool(edit_id) or bool(changed) != bool(payload["receipt_state"]):
            raise self._refuse(client_id, route, 400, "SCHEMA_INVALID",
                               "edit_id and receipt_state are present exactly when files changed")
        install = self._install_state(installation.installation_id)
        proposal["state"] = "COMPLETED" if payload["turn_ok"] else "FAILED"
        proposal["outcome"] = {k: payload[k] for k in ("edit_id", "turn_ok", "receipt_state", "changed_paths", "scope_violations")}
        proposal["outcome"]["at"] = self._clock()
        if changed:  # only an operation that changed files replaces the revert opportunity (failed ones included)
            install["state_seq"] += 1
            install["revert_slot"] = {"edit_id": edit_id, "proposal_id": proposal["proposal_id"],
                                      "receipt_state": payload["receipt_state"],
                                      "revertible": payload["receipt_state"] == "AVAILABLE",
                                      "turn_ok": payload["turn_ok"], "at": self._clock()}
        self._event("edit_outcome", installation.installation_id, proposal_id=proposal["proposal_id"],
                    edit_id=edit_id, turn_ok=payload["turn_ok"], changed_path_count=len(changed),
                    scope_violation_count=len(violations))
        grant = self._ledger.data["grants"][payload["grant_id"]]
        if grant.get("mandate_id"):
            mandate = self._ledger.data["mandates"][grant["mandate_id"]]
            outside = sorted(p for p in changed if not any(_under(p, w) for w in grant["writable_path_prefixes"])
                             or any(_under(p, q) for q in grant["protected_paths"]))
            mandate["edits"].append({"proposal_id": proposal["proposal_id"], "edit_id": edit_id, "turn_ok": payload["turn_ok"],
                                     "changed_paths": changed[:50], "scope_violation_count": len(violations),
                                     "at": self._clock()})
            if outside and mandate["state"] in MANDATE_LIVE_STATES:
                # Foundry's staging should make this impossible; if it happens, stop delegating.
                self._end_mandate(mandate, "REVOKED", "an outcome reported changes outside the mandate scope: " + ", ".join(outside[:10]))
        self._ledger.commit()
        return {"proposal_id": proposal["proposal_id"], "state": proposal["state"],
                "revert_slot": copy.deepcopy(install["revert_slot"])}

    def _record_revert_outcome(self, client_id: str, route: str, payload: Any) -> dict[str, Any]:
        payload = _require_keys(payload, {"installation_id", "kind", "edit_id", "status"})
        installation, _ = self._installation(client_id, route, payload, ("executor",))
        edit_id = _require_str(payload, "edit_id")
        if payload["status"] not in REVERT_STATUSES:
            raise self._refuse(client_id, route, 400, "SCHEMA_INVALID", f"status must be one of {sorted(REVERT_STATUSES)}")
        install = self._install_state(installation.installation_id)
        slot = install["revert_slot"]
        if payload["status"] in ("reverted", "failed_unrecoverable"):
            install["state_seq"] += 1  # project files changed: grants accepted before this are stale
            if slot is not None and slot["edit_id"] == edit_id:
                install["revert_slot"] = None if payload["status"] == "reverted" else {**slot, "revertible": False}
        # Proposals are never read or written here: a revert cannot restore or re-grant an authorization.
        self._event("revert_outcome", installation.installation_id, edit_id=edit_id, status=payload["status"])
        self._ledger.commit()
        return {"revert_slot": copy.deepcopy(install["revert_slot"]), "state_seq": install["state_seq"]}

    def proposal_record(self, proposal_id: str) -> dict[str, Any] | None:
        """Read-only copy for tests and audit tooling."""
        with self._lock:
            proposal = self._ledger.data["proposals"].get(proposal_id)
            return copy.deepcopy(proposal)

    def events(self) -> list[dict[str, Any]]:
        with self._lock:
            return copy.deepcopy(self._ledger.data["events"])
