"""Signed HTTP surface for EngAInOS editor-edit authorization (authority/editor_edit_authority.py).

Served on the existing 8765 scene server under /editor/* (bridgeroom/scene_server.py),
composed by launch_engine.py through compose_from_environment(), and only when
ENGAIN_EDITOR_AUTHORIZATION=1 and the shipped policies name at least one client.
It shares nothing with the Trixel live route: its own flag, client policy, edit
policy, ledger, transport-secret directory and grant key. The shipped policies
(authority/EDITOR_EDIT_POLICY_V1.json, authority/EDITOR_EDIT_CLIENT_POLICY_V1.json)
are deny-all, so in production the route is not composed and /editor/* answers 404
(flag off) or 503 (flag on, nothing composed). `main()` with `--isolated` composes it
from explicit paths for disposable test environments.

Every route is POST, signed with local_signed_transport (verified before the
body is parsed), and allowed only for a client whose client-policy routes
include one of the route's transport roles. The authority then checks the
installation role binding (proposer, executor, approver) itself.

Each installation binding must hold exactly its own transport role
(editor_edit_authority.ROLE_ROUTE) and nothing else, so no single credential
can both run and approve an edit. The human_input binding's role
(edit_attest) opens no route: its secret, minted here like every other one,
only signs the human's typed confirmations, which the authority verifies.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping

from tier1.engainos.authority.editor_edit_authority import (
    EDITOR_ROUTES,
    ROLE_ROUTE,
    ROLES,
    EditAuthorityError,
    EditorEditAuthority,
    load_edit_policy,
    strict_json_loads,
)
from tier1.engainos.authority.local_signed_transport import (
    ClientAssignment,
    SignedRequestVerifier,
    TransportAuthError,
    bounded_content_length,
    load_client_policy,
    provision_credentials,
)

FLAG_ENV = "ENGAIN_EDITOR_AUTHORIZATION"
_REPO_ROOT = Path(__file__).resolve().parents[3]
EDIT_POLICY_PATH = _REPO_ROOT / "tier1" / "engainos" / "authority" / "EDITOR_EDIT_POLICY_V1.json"
CLIENT_POLICY_PATH = _REPO_ROOT / "tier1" / "engainos" / "authority" / "EDITOR_EDIT_CLIENT_POLICY_V1.json"
LEDGER_PATH = _REPO_ROOT / "runtime" / "editor_edit" / "editor_edit_ledger.json"
TRANSPORT_DIR = _REPO_ROOT / "runtime" / "engain_transport" / "8765-editor"

_ROUTES: dict[str, tuple[frozenset[str], str]] = {
    "/editor/proposals": (frozenset({"edit_propose"}), "register_proposal"),
    "/editor/acceptances": (frozenset({"edit_propose", "edit_approve"}), "accept"),
    "/editor/rejections": (frozenset({"edit_propose", "edit_approve"}), "reject"),
    "/editor/state": (frozenset({"edit_propose", "edit_execute", "edit_approve"}), "state"),
    "/editor/approval_mode": (frozenset({"edit_approve"}), "set_approval_mode"),
    "/editor/grants/pickup": (frozenset({"edit_execute"}), "pickup"),
    "/editor/consume": (frozenset({"edit_execute"}), "consume"),
    "/editor/outcomes": (frozenset({"edit_execute"}), "record_outcome"),
    "/editor/public_key": (frozenset({"edit_execute"}), "public_key"),
    "/editor/mandates": (frozenset({"edit_approve"}), "create_mandate"),
    "/editor/mandates/revoke": (frozenset({"edit_approve"}), "revoke_mandate"),
    "/editor/mandates/complete": (frozenset({"edit_propose"}), "complete_mandate"),
    "/editor/promotions": (frozenset({"edit_approve"}), "create_promotion"),
    "/editor/promotions/consume": (frozenset({"edit_execute"}), "consume_promotion"),
}


class EditorEditRoute:
    def __init__(self, authority: EditorEditAuthority, verifier: SignedRequestVerifier,
                 client_policy: Mapping[str, ClientAssignment]) -> None:
        self._authority = authority
        self._verifier = verifier
        self._client_policy = dict(client_policy)

    def handle(self, method: str, path: str, headers: Mapping[str, str], body: bytes) -> tuple[int, dict[str, Any]]:
        if path not in _ROUTES:
            return 404, {"error": "UNKNOWN_ROUTE"}
        if method != "POST":
            return 405, {"error": "METHOD_NOT_ALLOWED"}
        try:
            client_id = self._verifier.verify(method, path, headers, body)
        except TransportAuthError as exc:
            return exc.status, {"error": "TRANSPORT_AUTH", "message": exc.message}
        roles, operation = _ROUTES[path]
        assignment = self._client_policy.get(client_id)
        if assignment is None or not (assignment.routes & roles):
            return 403, {"error": "ROUTE_NOT_PERMITTED", "message": "client policy does not grant this route"}
        try:
            payload = strict_json_loads(body.decode("utf-8")) if body else None
        except (UnicodeDecodeError, ValueError, RecursionError):
            return 400, {"error": "SCHEMA_INVALID", "message": "body is not strict JSON"}
        try:
            if operation == "public_key":
                return 200, {"public_key_pem": self._authority.public_key_pem}
            return 200, getattr(self._authority, operation)(client_id, payload)
        except EditAuthorityError as exc:
            return exc.status, {"error": exc.code, "message": exc.message}


def make_server(route: EditorEditRoute, host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802 (http.server naming)
            try:
                length = bounded_content_length(self.headers)
            except TransportAuthError as exc:
                return self._reply(exc.status, {"error": "TRANSPORT_AUTH", "message": exc.message})
            body = self.rfile.read(length)
            self._reply(*route.handle("POST", self.path, self.headers, body))

        def do_GET(self) -> None:  # noqa: N802
            self._reply(405, {"error": "METHOD_NOT_ALLOWED"})

        def _reply(self, status: int, payload: dict[str, Any]) -> None:
            data = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *_args: Any) -> None:
            pass

    if host not in ("127.0.0.1", "::1", "localhost"):
        raise ValueError("the editor edit route binds to loopback only")
    return ThreadingHTTPServer((host, port), Handler)


def enabled() -> bool:
    return os.environ.get(FLAG_ENV) == "1"


def compose_from_environment(
    *, edit_policy: Path | None = None, client_policy: Path | None = None,
    ledger: Path | None = None, transport_dir: Path | None = None,
) -> tuple[EditorEditRoute | None, str]:
    """Build the 8765 editor route, or return (None, reason) before any ledger, key or secret exists."""
    if not enabled():
        return None, f"{FLAG_ENV} is not '1'"
    try:
        clients = load_client_policy(client_policy or CLIENT_POLICY_PATH, known_routes=EDITOR_ROUTES)
        installations = load_edit_policy(edit_policy or EDIT_POLICY_PATH)
    except (OSError, ValueError) as exc:
        return None, f"editor policy is invalid: {exc}"
    if not clients or not installations:
        return None, "editor policies are deny-all (no clients or no installations)"
    try:
        check_role_bindings(installations, clients)
    except ValueError as exc:
        return None, f"editor policy is invalid: {exc}"
    try:
        route = compose(edit_policy=edit_policy or EDIT_POLICY_PATH, client_policy=client_policy or CLIENT_POLICY_PATH,
                        ledger=ledger or LEDGER_PATH, transport_dir=transport_dir or TRANSPORT_DIR)
    except EditAuthorityError as exc:
        return None, f"editor authority unavailable: {exc.message}"
    return route, "composed"


def check_role_bindings(installations: Mapping[str, Any], clients: Mapping[str, ClientAssignment]) -> None:
    """Every installation binding holds exactly its own role's route, so one key never serves two roles."""
    for installation in installations.values():
        for role in ROLES:
            client_id = installation.client_for(role)
            assignment = clients.get(client_id)
            if assignment is None or assignment.routes != frozenset({ROLE_ROUTE[role]}):
                raise ValueError(f"installation {installation.installation_id} {role} client {client_id!r} "
                                 f"must hold exactly the route {ROLE_ROUTE[role]!r} in the editor client policy")


def scene_packet_verifier(stageroom_root: Path | None = None):
    """scene_id -> SHA-256 of the packet the 8765 resolver delivers for it now (a fresh, read-only resolve)."""
    from tier1.engainos.bridgeroom.stageroom_scene_resolver import StageroomSceneResolver, scene_packet_sha256
    return lambda scene_id: scene_packet_sha256(StageroomSceneResolver(stageroom_root).load_scene(scene_id))


def compose(*, edit_policy: Path, client_policy: Path, ledger: Path, transport_dir: Path,
            stageroom_root: Path | None = None) -> EditorEditRoute:
    clients = load_client_policy(client_policy, known_routes=EDITOR_ROUTES)
    installations = load_edit_policy(edit_policy)
    check_role_bindings(installations, clients)        # before any secret or ledger exists
    server_clients = sorted(cid for cid, a in clients.items() if a.routes & EDITOR_ROUTES)
    credentials = provision_credentials(transport_dir, server_clients)
    human_input_keys = {i.human_input_client_id: credentials[i.human_input_client_id] for i in installations.values()}
    authority = EditorEditAuthority(policy=installations, ledger_path=ledger, human_input_keys=human_input_keys,
                                    scene_packet_sha256=scene_packet_verifier(stageroom_root))
    return EditorEditRoute(authority, SignedRequestVerifier(credentials), {cid: clients[cid] for cid in server_clients})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Isolated EngAInOS editor-edit authority (not a production server).")
    parser.add_argument("--isolated", action="store_true", required=True,
                        help="required acknowledgement: this composition is for isolated testing only")
    parser.add_argument("--edit-policy", type=Path, required=True)
    parser.add_argument("--client-policy", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--transport-dir", type=Path, required=True)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--port-file", type=Path, required=True)
    parser.add_argument("--stageroom", type=Path, default=None,
                        help="Stageroom that scene_refs are verified against (default: the production one)")
    args = parser.parse_args(argv)
    route = compose(edit_policy=args.edit_policy, client_policy=args.client_policy,
                    ledger=args.ledger, transport_dir=args.transport_dir, stageroom_root=args.stageroom)
    server = make_server(route, port=args.port)
    args.port_file.write_text(str(server.server_address[1]), encoding="ascii")
    print(f"isolated editor edit authority on 127.0.0.1:{server.server_address[1]}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
