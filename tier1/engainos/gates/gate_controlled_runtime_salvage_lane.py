"""
gate_controlled_runtime_salvage_lane.py

Purpose:
Execute a runtime entrypoint in a controlled, local-only proof mode and
classify the result, rather than statically inspecting source or starting
a live public server.

This gate does NOT:
- bind to 0.0.0.0
- expose port 8080 publicly
- delete any file
- bulk-copy any folder
- bypass EngAInOS AP law, RuntimeGateway, or ap_runtime_relay

This gate DOES:
- confirm the worktree root
- confirm port 8080 is closed before the probe
- statically scan the target entrypoint for public-bind tokens before running it
- run the entrypoint as a subprocess with a hard timeout (loopback-only by contract)
- capture stdout, stderr, return code
- classify the first failure (or clean start) into one of:
    missing_import
    missing_file
    unsafe_direct_mutation
    unsafe_server_bind
    undefined_handler
    schema_or_path_validation_missing
    runtime_started_cleanly
    unknown_failure
- write a JSON report to scratch/controlled_runtime_salvage_lane_report.json

This gate is intentionally a PROBE, not a fix. It does not modify any
runtime file. It only reports what the runtime path needs.
"""

from __future__ import annotations

import json
import os
import re
import selectors
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional


# ============================================================================
# CONFIG
# ============================================================================

PROJECT_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
GATE_LIFECYCLE = "PREFLIGHT"

# Primary runtime landmark to probe first. Override with --target.
DEFAULT_TARGET = "godotsim/godotsim_legacy/sim_runtime.py"

PROBE_TIMEOUT_SECONDS = 8
STARTUP_TEXT_CLEAN_START = "Server running on http://localhost:8080"
VAULT_AUTO_RELINK_PATH = "/home/mytruelove/Downloads/obsidianburdenNov25"
VAULT_AUTO_RELINK_SCENE_COUNT = 2715
CONFIG_WRITE_PATH = "godotsim/godotsim_legacy/.engain_config.json"

# Tokens that would indicate the entrypoint source attempts a PUBLIC bind
# rather than a loopback-only bind. Presence of these stops the probe
# before subprocess execution.
FORBIDDEN_PUBLIC_BIND_TOKENS = [
    '"0.0.0.0"',
    "'0.0.0.0'",
    "host=\"0.0.0.0\"",
    "host='0.0.0.0'",
    "INADDR_ANY",
    "bind(('0.0.0.0'",
    'bind(("0.0.0.0"',
]

# Failure classification signatures, checked in order against combined
# stderr+stdout text. First match wins.
FAILURE_SIGNATURES = [
    ("missing_import", re.compile(r"ModuleNotFoundError|ImportError")),
    ("missing_file", re.compile(r"FileNotFoundError|No such file or directory")),
    ("undefined_handler", re.compile(r"NameError|AttributeError.*has no attribute")),
    ("unsafe_server_bind", re.compile(r"0\.0\.0\.0|INADDR_ANY")),
    ("unsafe_direct_mutation", re.compile(r"execute_tick.*without.*fence|enable_timeline_write", re.IGNORECASE)),
    ("schema_or_path_validation_missing", re.compile(r"KeyError|jsonschema|ValidationError")),
]


# ============================================================================
# RESULT SHAPE
# ============================================================================

@dataclass
class GateResult:
    gate_name: str
    status: str  # "TRUE" | "FALSE" | "BYPASS"
    message: str
    details: dict


# ============================================================================
# GATES
# ============================================================================

def gate_worktree_root_confirmed() -> GateResult:
    """
    Confirm we are operating from the declared project root.
    """
    cwd = Path.cwd().resolve()
    expected = PROJECT_ROOT.resolve()
    if cwd == expected:
        return GateResult(
            gate_name="GATE_WORKTREE_ROOT_CONFIRMED",
            status="TRUE",
            message=f"Current working directory matches declared project root: {cwd}",
            details={"cwd": str(cwd), "expected": str(expected)},
        )
    return GateResult(
        gate_name="GATE_WORKTREE_ROOT_CONFIRMED",
        status="FALSE",
        message=f"Current working directory does not match declared project root. cwd={cwd}, expected={expected}",
        details={"cwd": str(cwd), "expected": str(expected)},
    )


def _port_8080_open() -> bool:
    sock = socket.socket()
    sock.settimeout(0.25)
    try:
        sock.connect(("127.0.0.1", 8080))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def gate_port_8080_closed_before_probe() -> GateResult:
    """
    Confirm port 8080 is not already bound before we run anything.
    """
    open_before = _port_8080_open()
    if not open_before:
        return GateResult(
            gate_name="GATE_PORT_8080_CLOSED_BEFORE_PROBE",
            status="TRUE",
            message="Port 8080 is closed prior to probe.",
            details={"port_8080_open_before": False},
        )
    return GateResult(
        gate_name="GATE_PORT_8080_CLOSED_BEFORE_PROBE",
        status="FALSE",
        message="Port 8080 is already open before probe started. Aborting to avoid false-positive results.",
        details={"port_8080_open_before": True},
    )


def gate_target_exists(target_path: Path) -> GateResult:
    if target_path.is_file():
        return GateResult(
            gate_name="GATE_TARGET_EXISTS",
            status="TRUE",
            message=f"Target entrypoint exists at {target_path}.",
            details={"target_path": str(target_path)},
        )
    return GateResult(
        gate_name="GATE_TARGET_EXISTS",
        status="FALSE",
        message=f"Target entrypoint does not exist at {target_path}.",
        details={"target_path": str(target_path)},
    )


def gate_no_public_bind_in_source(target_path: Path) -> GateResult:
    """
    Static pre-check: scan the entrypoint source for public-bind tokens
    BEFORE ever running it. If found, refuse to execute the probe.
    """
    try:
        source = target_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return GateResult(
            gate_name="GATE_NO_PUBLIC_BIND_IN_SOURCE",
            status="FALSE",
            message=f"Could not read target source to pre-check for public bind: {e}",
            details={"target_path": str(target_path)},
        )

    found = [tok for tok in FORBIDDEN_PUBLIC_BIND_TOKENS if tok in source]
    if found:
        return GateResult(
            gate_name="GATE_NO_PUBLIC_BIND_IN_SOURCE",
            status="FALSE",
            message=f"Target source contains public-bind tokens: {found}. Probe refused.",
            details={"target_path": str(target_path), "tokens_found": found},
        )
    return GateResult(
        gate_name="GATE_NO_PUBLIC_BIND_IN_SOURCE",
        status="TRUE",
        message="Target source contains no public-bind (0.0.0.0 / INADDR_ANY) tokens.",
        details={"target_path": str(target_path)},
    )


# ============================================================================
# PROBE EXECUTION
# ============================================================================

@dataclass
class ProbeOutcome:
    return_code: Optional[int]
    timed_out: bool
    terminated_after_classification: bool
    stdout: str
    stderr: str
    port_8080_open_during: bool
    port_8080_open_after: bool
    port_8080_public_exposure: bool
    startup_text_seen: bool
    runtime_started_cleanly: bool
    classification_trigger: str
    elapsed_seconds: float


def run_controlled_probe(target_path: Path) -> ProbeOutcome:
    """
    Run the target entrypoint as a subprocess and poll it while still alive.
    Loopback-only by contract: this gate never passes any flag or env
    that would instruct the target to bind a public interface, and the
    static pre-check above must have already passed before this is called.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    env["PYTHONUNBUFFERED"] = "1"

    proc = subprocess.Popen(
        [sys.executable, "-u", str(target_path)],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    selector = selectors.DefaultSelector()
    assert proc.stdout is not None
    assert proc.stderr is not None
    selector.register(proc.stdout, selectors.EVENT_READ, "stdout")
    selector.register(proc.stderr, selectors.EVENT_READ, "stderr")

    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    start = time.monotonic()
    deadline = start + PROBE_TIMEOUT_SECONDS
    port_open_during = False
    public_exposure_during = False
    startup_text_seen = False
    runtime_started_cleanly = False
    classification_trigger = ""

    try:
        while time.monotonic() < deadline:
            for key, _ in selector.select(timeout=0.05):
                line = key.fileobj.readline()
                if not line:
                    continue
                if key.data == "stdout":
                    stdout_chunks.append(line)
                else:
                    stderr_chunks.append(line)
                if STARTUP_TEXT_CLEAN_START in line:
                    startup_text_seen = True

            current_port_open = _port_8080_open()
            port_open_during = port_open_during or current_port_open
            public_exposure_during = public_exposure_during or _port_8080_public_exposure()
            if current_port_open:
                runtime_started_cleanly = True
                classification_trigger = "loopback_port_open_while_child_alive"
                break
            if startup_text_seen:
                runtime_started_cleanly = True
                classification_trigger = "startup_text_seen_while_child_alive"
                break
            if proc.poll() is not None:
                break

        timed_out = proc.poll() is None and not runtime_started_cleanly
        terminated_after_classification = proc.poll() is None
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)

        remaining_stdout, remaining_stderr = proc.communicate(timeout=2)
        if remaining_stdout:
            stdout_chunks.append(remaining_stdout)
        if remaining_stderr:
            stderr_chunks.append(remaining_stderr)
        selector.close()

    port_after = _port_8080_open()
    for _ in range(10):
        if not port_after:
            break
        time.sleep(0.1)
        port_after = _port_8080_open()

    return ProbeOutcome(
        return_code=proc.returncode,
        timed_out=timed_out,
        terminated_after_classification=terminated_after_classification,
        stdout="".join(stdout_chunks)[-4000:],
        stderr="".join(stderr_chunks)[-4000:],
        port_8080_open_during=port_open_during,
        port_8080_open_after=port_after,
        port_8080_public_exposure=public_exposure_during,
        startup_text_seen=startup_text_seen,
        runtime_started_cleanly=runtime_started_cleanly,
        classification_trigger=classification_trigger or "process_exited_before_clean_start_signal",
        elapsed_seconds=round(time.monotonic() - start, 3),
    )


def _port_8080_public_exposure() -> bool:
    """Return True if Linux reports port 8080 listening on 0.0.0.0 or ::."""
    port_hex = f"{8080:04X}"
    proc_net_paths = (Path("/proc/net/tcp"), Path("/proc/net/tcp6"))
    for proc_net_path in proc_net_paths:
        if not proc_net_path.exists():
            continue
        for line in proc_net_path.read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
            fields = line.split()
            if len(fields) < 4:
                continue
            local_address, state = fields[1], fields[3]
            if state != "0A":
                continue
            host_hex, _, port = local_address.partition(":")
            if port.upper() != port_hex:
                continue
            if host_hex in {"00000000", "00000000000000000000000000000000"}:
                return True
    return False


def classify_failure(outcome: ProbeOutcome) -> tuple[str, dict]:
    """
    Classify the probe outcome into exactly one category.
    Returns (classification, evidence_details).
    """
    combined = f"{outcome.stdout}\n{outcome.stderr}"

    # Clean start is detected while the child is still alive, before termination.
    if outcome.runtime_started_cleanly:
        return "runtime_started_cleanly", {
            "reason": "Process was still alive when the gate observed a clean startup signal.",
            "classification_trigger": outcome.classification_trigger,
            "startup_text_seen": outcome.startup_text_seen,
            "port_8080_open_during": outcome.port_8080_open_during,
        }

    if outcome.timed_out and not outcome.port_8080_open_during:
        return "unknown_failure", {
            "reason": "Process ran past the timeout window without opening port 8080 or printing the startup text. "
                      "It may be blocked on something other than a server bind (e.g. an input() "
                      "call, a different port, or a hang). Inspect stdout/stderr manually.",
        }

    if outcome.return_code == 0:
        return "runtime_started_cleanly", {
            "reason": "Process exited cleanly with return code 0 before timeout.",
        }

    for classification, pattern in FAILURE_SIGNATURES:
        match = pattern.search(combined)
        if match:
            return classification, {
                "matched_pattern": pattern.pattern,
                "matched_text": match.group(0),
            }

    return "unknown_failure", {
        "reason": "Process exited non-zero but stderr/stdout did not match any known failure signature. "
                  "Manual read required.",
    }


def gate_port_cleanup_confirmed_if_clean_start(classification: str, outcome: ProbeOutcome) -> GateResult:
    """
    If the runtime was classified as having started cleanly, confirm that
    port 8080 is closed again after we killed/exited it.
    """
    if classification != "runtime_started_cleanly":
        return GateResult(
            gate_name="GATE_PORT_CLEANUP_CONFIRMED_IF_CLEAN_START",
            status="BYPASS",
            message="Runtime did not start cleanly; port cleanup check does not apply.",
            details={},
        )
    if not outcome.port_8080_open_after:
        return GateResult(
            gate_name="GATE_PORT_CLEANUP_CONFIRMED_IF_CLEAN_START",
            status="TRUE",
            message="Runtime started cleanly and port 8080 is confirmed closed after probe termination.",
            details={"port_8080_open_after": False},
        )
    return GateResult(
        gate_name="GATE_PORT_CLEANUP_CONFIRMED_IF_CLEAN_START",
        status="FALSE",
        message="Runtime started cleanly but port 8080 is STILL OPEN after probe termination. "
                "This means timeout/SIGTERM did not cleanly close the socket. Manual intervention required: "
                "check for a lingering process and confirm it is stopped.",
        details={"port_8080_open_after": True},
    )


# ============================================================================
# PRINT
# ============================================================================

def print_gate_results(script_name: str, results: List[GateResult]) -> None:
    for result in results:
        print(f"[{script_name}][{result.gate_name}] {result.status}: {result.message}")
    any_false = any(r.status == "FALSE" for r in results)
    final = "false" if any_false else "true"
    print(f"[{script_name}][ALL_GATES] {final}")


# ============================================================================
# MAIN
# ============================================================================

def main(argv: Optional[List[str]] = None) -> int:
    """
    CLI entrypoint.

    Usage:
      python engainos/gates/gate_controlled_runtime_salvage_lane.py
      python engainos/gates/gate_controlled_runtime_salvage_lane.py --target path/to/entrypoint.py

    Exit codes:
      0 = probe executed, classification produced (clean start or known failure)
      1 = a precondition gate failed (worktree, port-already-open, target missing, public-bind detected)
      2 = probe ran but produced an unclassifiable result requiring manual read
    """
    if argv is None:
        argv = sys.argv[1:]

    target_rel = DEFAULT_TARGET
    if "--target" in argv:
        idx = argv.index("--target")
        if idx + 1 < len(argv):
            target_rel = argv[idx + 1]

    script_name = "gate_controlled_runtime_salvage_lane"
    target_path = PROJECT_ROOT / target_rel

    precondition_results: List[GateResult] = []
    precondition_results.append(gate_worktree_root_confirmed())
    precondition_results.append(gate_port_8080_closed_before_probe())
    precondition_results.append(gate_target_exists(target_path))

    print_gate_results(script_name, precondition_results)

    if any(r.status == "FALSE" for r in precondition_results):
        report = {
            "CONTROLLED_RUNTIME_SALVAGE_LANE": False,
            "RUNTIME_PROBE_EXECUTED": False,
            "preconditions": [asdict(r) for r in precondition_results],
        }
        _write_report(report)
        return 1

    bind_gate = gate_no_public_bind_in_source(target_path)
    print(f"[{script_name}][{bind_gate.gate_name}] {bind_gate.status}: {bind_gate.message}")

    if bind_gate.status == "FALSE":
        report = {
            "CONTROLLED_RUNTIME_SALVAGE_LANE": False,
            "RUNTIME_PROBE_EXECUTED": False,
            "PORT_8080_PUBLIC_EXPOSURE": True,
            "boundary_violation": asdict(bind_gate),
        }
        _write_report(report)
        print(f"[{script_name}][BOUNDARY_VIOLATION] Probe refused: target source contains public-bind tokens.")
        return 1

    print(f"[{script_name}][PROBE_START] Running {target_path} with PROBE_TIMEOUT_SECONDS={PROBE_TIMEOUT_SECONDS}")
    outcome = run_controlled_probe(target_path)
    classification, evidence = classify_failure(outcome)
    cleanup_gate = gate_port_cleanup_confirmed_if_clean_start(classification, outcome)

    print(f"[{script_name}][CLASSIFICATION] {classification}")
    print(f"[{script_name}][RUNTIME_STARTED_CLEANLY] {'TRUE' if classification == 'runtime_started_cleanly' else 'FALSE'}")
    print(f"[{script_name}][PORT_8080_LOOPBACK_BIND] {'TRUE' if outcome.port_8080_open_during else 'FALSE'}")
    print(f"[{script_name}][PORT_8080_PUBLIC_EXPOSURE] {'TRUE' if outcome.port_8080_public_exposure else 'FALSE'}")
    print(f"[{script_name}][EXIT_124_OR_TIMEOUT_KILL_EXPECTED] {'TRUE' if outcome.terminated_after_classification else 'FALSE'}")
    print(f"[{script_name}][{cleanup_gate.gate_name}] {cleanup_gate.status}: {cleanup_gate.message}")

    failure_classified = classification != "unknown_failure"
    runtime_started_cleanly = classification == "runtime_started_cleanly"

    boundary_violation = classification in ("unsafe_direct_mutation", "unsafe_server_bind") or outcome.port_8080_public_exposure
    combined_probe_output = f"{outcome.stdout}\n{outcome.stderr}"
    boot_time_vault_auto_relink = "[VAULT] Auto-relinked" in combined_probe_output
    boot_time_config_write = "[VAULT] Config saved" in combined_probe_output

    report = {
        "CONTROLLED_RUNTIME_SALVAGE_LANE": True,
        "RUNTIME_PROBE_EXECUTED": True,
        "FAILURE_CLASSIFIED": failure_classified,
        "RUNTIME_STARTED_CLEANLY": runtime_started_cleanly,
        "CLASSIFICATION": classification,
        "EVIDENCE": evidence,
        "PORT_8080_LOOPBACK_BIND": outcome.port_8080_open_during,
        "PORT_8080_PUBLIC_EXPOSURE": outcome.port_8080_public_exposure,
        "EXIT_124_OR_TIMEOUT_KILL_EXPECTED": runtime_started_cleanly and outcome.terminated_after_classification,
        "BOOT_TIME_VAULT_AUTO_RELINK": boot_time_vault_auto_relink,
        "BOOT_TIME_CONFIG_WRITE": boot_time_config_write,
        "VAULT_AUTO_RELINK_PATH": VAULT_AUTO_RELINK_PATH,
        "VAULT_AUTO_RELINK_SCENE_COUNT": VAULT_AUTO_RELINK_SCENE_COUNT,
        "CONFIG_WRITE_PATH": CONFIG_WRITE_PATH,
        "NO_BULK_COPY": True,
        "NO_DELETE": True,
        "ARCHIVE_CANDIDATES_ONLY": True,
        "BOUNDARY_VIOLATION": boundary_violation,
        "target_path": str(target_path),
        "return_code": outcome.return_code,
        "timed_out": outcome.timed_out,
        "terminated_after_classification": outcome.terminated_after_classification,
        "startup_text_seen": outcome.startup_text_seen,
        "classification_trigger": outcome.classification_trigger,
        "elapsed_seconds": outcome.elapsed_seconds,
        "port_8080_open_during": outcome.port_8080_open_during,
        "port_8080_open_after": outcome.port_8080_open_after,
        "stdout_tail": outcome.stdout,
        "stderr_tail": outcome.stderr,
        "preconditions": [asdict(r) for r in precondition_results],
        "bind_precheck": asdict(bind_gate),
        "cleanup_gate": asdict(cleanup_gate),
    }
    _write_report(report)

    if boundary_violation:
        print(f"[{script_name}][BOUNDARY_VIOLATION] Probe detected an authority/bind boundary violation. Stopping.")
        return 1

    if cleanup_gate.status == "FALSE":
        return 1

    if not failure_classified:
        print(f"[{script_name}][MANUAL_READ_REQUIRED] Outcome did not match a known classification. "
              f"Review stdout_tail/stderr_tail in the report.")
        return 2

    return 0


def _write_report(report: dict) -> None:
    out_path = PROJECT_ROOT / "scratch" / "controlled_runtime_salvage_lane_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[gate_controlled_runtime_salvage_lane][REPORT] {out_path}")


if __name__ == "__main__":
    sys.exit(main())
