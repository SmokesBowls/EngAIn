"""
mailbox_request_handler.py - Real file-based request/response I/O for
SharedSessionBridge.

Replaces hand-written Python calls to handle_turn() with actual
request.json / response.json artifacts on disk — the same mailbox shape
this project has always used for the real avatar bodies (see
hermes_session_adapter.py in both engain_avatar and
godot_engain_3d_avatar), now wired to the provider-neutral dispatch path
instead of directly to one hardcoded provider.

Request schema (engain.mailbox_request.v1):
    {
        "shared_session_id": "...",
        "origin_body": "dragon_2d" | "dragon_3d" | ...,
        "player_input": "...",
        "snapshot": {...} | null   (optional)
    }

Response schema (engain.mailbox_response.v1):
    {
        "session_id": "...", "origin_body": "...",
        "actor": "...", "response": "...", "turn_id": N
    }
    — exactly SharedSessionBridge.handle_turn()'s own return shape; this
    handler does not reshape it.

This is deliberately NOT a persistent polling daemon. That is a separate,
larger decision — see the 2026-08-16 full audit's own finding about what a
real launcher/mailbox-worker composition requires before anything gets
called supported. This is the request/response TRANSLATION layer only:
given one real request file, process it through SharedSessionBridge
exactly once, and write one real response file. A future persistent
worker can call this repeatedly, the same way the existing avatar repos'
hermes_session_adapter.py --publish-request / --claim-response CLI
subcommands are also invoked per request rather than as a service.

Player input is passed through to SharedSessionBridge.handle_turn()
exactly as read from the request file — this handler does not construct,
inject, or otherwise touch any continuity recap. That is
ContinuityContextBuilder's job, inside the bridge, for every caller
uniformly, whether this file-based path or a direct Python call.

`binding` (item 1, 2026-08-18): handle_turn() now requires a
ProviderSessionBinding it never re-derives from Presence internally (see
shared_session_bridge.py's own module docstring Correction). This
mailbox request schema carries no provider/session fields of its own, so
this handler cannot construct one from the request the way
presence_authority_server.py's /dispatch handler does — the caller must
supply it, exactly as it must already supply a Bridge already wired to
the right presence/ledger/dispatcher. This is a single-shot, non-
concurrent translation layer (see the module docstring above — explicitly
NOT a persistent polling daemon, and not reachable from
ThreadingHTTPServer's concurrent surface at all), so a caller resolving
its own binding once, synchronously, before calling this function carries
none of the concurrent-interleaving risk item 1's design note traces for
/dispatch — there is no second, concurrent caller for this function to
race against.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from tier1.engainos.bridgeroom.shared_session_bridge import SharedSessionBridge
from tier1.engainos.core.provider_session_binding import ProviderSessionBinding


class MailboxRequestError(Exception):
    """The request file was missing a required field, or wasn't valid JSON."""


def _load_request(request_path: Path) -> Dict[str, Any]:
    try:
        raw = request_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise MailboxRequestError(f"cannot read request file {request_path}: {exc}") from exc
    try:
        request = json.loads(raw)
    except ValueError as exc:
        raise MailboxRequestError(f"request file {request_path} is not valid JSON: {exc}") from exc
    if not isinstance(request, dict):
        raise MailboxRequestError(f"request file {request_path} must decode to an object")

    missing = [key for key in ("shared_session_id", "origin_body", "player_input") if key not in request]
    if missing:
        raise MailboxRequestError(f"request file {request_path} is missing required fields: {missing}")
    return request


def handle_mailbox_request(
    request_path: Path,
    response_path: Path,
    bridge: SharedSessionBridge,
    binding: ProviderSessionBinding,
) -> Dict[str, Any]:
    """Reads one real request.json, runs it through the bridge exactly
    once, writes one real response.json. Returns the same dict written to
    response_path, for a caller (or a test) that wants it without a second
    disk read.

    `binding` is required, matching handle_turn()'s own contract — see
    this module's docstring for why a caller-resolved binding is safe
    here even though it wouldn't be for /dispatch's concurrent surface."""
    request = _load_request(request_path)

    result = bridge.handle_turn(
        session_id=request["shared_session_id"],
        origin_body=request["origin_body"],
        player_input=request["player_input"],
        binding=binding,
        snapshot=request.get("snapshot"),
    )

    response_path.parent.mkdir(parents=True, exist_ok=True)
    response_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
