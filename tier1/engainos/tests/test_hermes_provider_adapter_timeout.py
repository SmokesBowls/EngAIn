"""
Tests for hermes_provider_adapter.py's timeout configuration — the
2026-09-13 correction.

Live-test finding this closes: a real, live-reproduced `hermes chat
--resume 20260731_065008_63a62d` call against this project's own
actively-used session took 152.09s wall-clock to complete *successfully*
(see that day's receipt). The previous DEFAULT_TIMEOUT_S (90.0) —
mirrored, independently and NUMERICALLY EQUAL, by engain_continuity_
client.py's own 90.0 HTTP timeout in the dragon3d repo — guaranteed
failure for that session, not occasionally.

This file proves the actual mechanism at test-friendly scale (seconds,
not the real 240s/255s), using a fake `hermes` executable that sleeps a
controlled, short amount — never by waiting on the literal configured
default, which would make the suite impractically slow. What's under
test is the RELATIONSHIP (a call that would be killed by a narrow
timeout survives a wider one; the configured default itself exceeds the
real 152.09s observation), not the literal 240.0/255.0 values in real
time.
"""

from __future__ import annotations

import importlib
import os
import stat
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tier1.engainos.bridgeroom import hermes_provider_adapter as module
from tier1.engainos.core.provider_session_binding import ProviderSessionBinding

# The real, live-reproduced duration a successful call against this
# project's own actively-used session actually took (2026-09-13 receipt).
# Not a round number — the literal observed value.
OBSERVED_LIVE_SUCCESSFUL_CALL_SECONDS = 152.09


def _write_fake_hermes(tmp_path: Path, *, sleep_seconds: float, session_id: str) -> Path:
    """A fake `hermes` executable, placed literally at <tmp_path>/hermes
    so shutil.which("hermes") finds it once tmp_path is prepended to
    PATH. Emits the response body to stdout and the session_id line to
    stderr — matching dispatch_via_hermes_cli()'s own real parsing (it
    reads HERMES_SESSION_ID_PATTERN from .stderr specifically, and the
    response text from .stdout), not the different stdout-only
    convention godot_engain_3d_avatar's own fake_hermes_for_tests.sh
    uses for its own (Godot-side, combined-stream) test."""
    script = tmp_path / "hermes"
    script.write_text(
        "#!/bin/bash\n"
        f"sleep {sleep_seconds}\n"
        "echo \"fake response text\"\n"
        f"echo \"session_id: {session_id}\" >&2\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script


def _binding(provider_session_id: str) -> ProviderSessionBinding:
    return ProviderSessionBinding(
        provider_id="hermes",
        model_id="test-model",
        provider_session_id=provider_session_id,
        agent_id="hermes",
        instance_id="test-instance",
        shared_session_id="shared-timeout-test",
        launch_options={},
    )


@pytest.fixture()
def fake_hermes_on_path(tmp_path, monkeypatch):
    """Prepends tmp_path (where the fake hermes executable is written)
    onto PATH, restored automatically by monkeypatch after the test."""
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ.get('PATH', '')}")
    return tmp_path


def test_default_timeout_exceeds_the_live_observed_successful_call(monkeypatch):
    monkeypatch.delenv("ENGAIN_CONTINUITY_PROVIDER_TIMEOUT_S", raising=False)
    reloaded = importlib.reload(module)
    try:
        assert reloaded.DEFAULT_TIMEOUT_S > OBSERVED_LIVE_SUCCESSFUL_CALL_SECONDS
        assert reloaded.DEFAULT_TIMEOUT_S == 240.0
    finally:
        importlib.reload(module)  # leave the module state clean for later tests


def test_provider_timeout_is_configurable_via_env_var(monkeypatch):
    monkeypatch.setenv("ENGAIN_CONTINUITY_PROVIDER_TIMEOUT_S", "17.5")
    reloaded = importlib.reload(module)
    try:
        assert reloaded.DEFAULT_TIMEOUT_S == 17.5
    finally:
        monkeypatch.delenv("ENGAIN_CONTINUITY_PROVIDER_TIMEOUT_S", raising=False)
        importlib.reload(module)


def test_call_within_timeout_succeeds(tmp_path, fake_hermes_on_path):
    _write_fake_hermes(tmp_path, sleep_seconds=0.2, session_id="sess-a")
    binding = _binding("sess-a")
    result = module.dispatch_via_hermes_cli(binding, [], "hi", timeout_s=2.0)
    assert result["response"] == "fake response text"
    assert result["actor"] == "hermes"


def test_call_exceeding_a_narrow_timeout_is_killed_not_hung_forever(tmp_path, fake_hermes_on_path):
    """Establishes the baseline this fix corrects: with a narrow timeout
    budget, a call that takes longer than it is cleanly killed and
    reported, exactly like the real 90.0-vs-152.09s failure — just at
    test-friendly scale (0.1s budget, 0.5s call) instead of real minutes."""
    _write_fake_hermes(tmp_path, sleep_seconds=0.5, session_id="sess-b")
    binding = _binding("sess-b")
    with pytest.raises(module.HermesDispatchError, match="exceeded"):
        module.dispatch_via_hermes_cli(binding, [], "hi", timeout_s=0.1)


def test_call_exceeding_the_old_narrow_timeout_survives_a_wider_one(tmp_path, fake_hermes_on_path):
    """The actual A fix, proven at test-friendly scale: the SAME call
    duration that the previous test proved gets killed at a narrow
    timeout completes successfully once given real headroom — the exact
    relationship the real 240s-vs-90s change establishes for the real
    152.09s call, just without waiting real minutes in this suite."""
    _write_fake_hermes(tmp_path, sleep_seconds=0.5, session_id="sess-c")
    binding = _binding("sess-c")
    result = module.dispatch_via_hermes_cli(binding, [], "hi", timeout_s=2.0)
    assert result["response"] == "fake response text"


def test_session_drift_still_detected_regardless_of_timeout_width(tmp_path, fake_hermes_on_path):
    """Regression pin: widening the timeout must not weaken any other
    correctness check dispatch_via_hermes_cli() already performs."""
    _write_fake_hermes(tmp_path, sleep_seconds=0.1, session_id="a-different-session")
    binding = _binding("sess-d")
    with pytest.raises(module.HermesSessionDrift):
        module.dispatch_via_hermes_cli(binding, [], "hi", timeout_s=2.0)
