"""
There is deliberately no live pytest test in this file.

hermes's own auth layer (hermes_cli/auth.py::_auth_file_path) refuses to
touch ~/.hermes/auth.json whenever PYTEST_CURRENT_TEST is set in its
environment — a guard against hermes's own test suite corrupting real auth.
Our subprocess calls inherit that variable from pytest incidentally, which
trips the same guard even though this is a deliberate, human-authorized live
call, not an accidental one.

The correct fix is not to strip that variable inside
hermes_provider_adapter.py (considered and explicitly declined — that
adapter has no business overriding a safety boundary belonging to a
different tool) and not to fake the guard's absence some other way. The
correct fix is to never run the live proof under pytest at all, so the
variable is never set to begin with.

The real live proof — real hermes CLI, real openai-codex/gpt-5.6-sol
provider, both bodies, the presence-loss failure case — lives at:

    tier1/engainos/tools/live_hermes_continuity_proof.py

Run it directly:

    python3 tier1/engainos/tools/live_hermes_continuity_proof.py

It writes a receipt to runtime/logs/SHARED_SESSION_CONTINUITY_LIVE_HERMES_PROOF_V1.report.json
on success. It is not pytest-collected on purpose.
"""
