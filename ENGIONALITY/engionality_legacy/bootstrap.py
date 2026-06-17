# ENGINALITY/bootstrap.py
"""
EnginalityRuntime bootstrap.

Provides three minimal concrete implementations of the Protocols defined
in runtime_loop.py, then wires them into a ready-to-tick EnginalityRuntime.

    SimpleAnchorStore   — file-backed snapshot persistence
    SimpleAPEngine      — accept-everything prototype (Phase 1)
    SimpleZON4DKernel   — dict-mutation kernel (zon4d_kernel.py)

Usage (from start_button.py or any entry point):

    from ENGINALITY.bootstrap import build_runtime, run_tick_loop

    runtime = build_runtime()
    # Single tick with no incoming deltas:
    ctx = runtime.run_tick(pending_deltas=[])
    # Or drive a loop:
    run_tick_loop(runtime, ticks=10)

The bootstrap is intentionally minimal — every component can be swapped
for a production implementation without touching EnginalityRuntime.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .runtime_loop import (
    APVerdict,
    AnchorStore,
    APEngine,
    Delta,
    EnginalityRuntime,
    PerformanceABI,
    Snapshot,
)
from .zon4d_kernel import SimpleZON4DKernel
from .performer_engine import PerformerEngine


# ---------------------------------------------------------------------------
# Default paths
# ---------------------------------------------------------------------------

_DEFAULT_ANCHOR_DIR = Path(
    os.environ.get(
        "ENGAIN_ANCHOR_DIR",
        str(Path(__file__).parent.parent / ".engain_cache" / "enginality_anchors"),
    )
)

_INITIAL_STATE: Dict[str, Any] = {
    "entities": {},
    "world": {
        "tick": 0,
        "flags": {},
    },
}


# ---------------------------------------------------------------------------
# SimpleAnchorStore
# ---------------------------------------------------------------------------

class SimpleAnchorStore:
    """
    File-backed AnchorStore.

    Snapshots are written as JSON under anchor_dir/.
    The last immutable anchor is tracked in anchor_dir/immutable_anchor.json.
    Timeline hash is a running SHA-256 over snapshot IDs (simplified).
    """

    def __init__(self, anchor_dir: Path = _DEFAULT_ANCHOR_DIR) -> None:
        self.anchor_dir = anchor_dir
        self.anchor_dir.mkdir(parents=True, exist_ok=True)
        self._timeline_hashes: List[str] = []
        self._last_immutable: Optional[Snapshot] = None

    # -- AnchorStore Protocol --

    def load_initial_snapshot(self) -> Snapshot:
        init_path = self.anchor_dir / "initial_snapshot.json"
        if init_path.exists():
            try:
                data = json.loads(init_path.read_text(encoding="utf-8"))
                snap = Snapshot(
                    id=data["id"],
                    tick=data["tick"],
                    zon4d_state=data["zon4d_state"],
                    hash32=data.get("hash32"),
                    anchor_type=data.get("anchor_type", "soft"),
                )
                print(f"[AnchorStore] Loaded initial snapshot: {snap.id} (tick {snap.tick})")
                return snap
            except Exception as e:
                print(f"[AnchorStore] Failed to load initial snapshot ({e}), creating fresh")

        snap = Snapshot(
            id="snap_init",
            tick=0,
            zon4d_state=dict(_INITIAL_STATE),
            anchor_type="immutable",
        )
        snap = Snapshot(
            id=snap.id,
            tick=snap.tick,
            zon4d_state=snap.zon4d_state,
            hash32=self.compute_hash(snap),
            anchor_type=snap.anchor_type,
        )
        self._last_immutable = snap
        self.append_snapshot(snap)
        return snap

    def load_last_immutable_anchor(self) -> Snapshot:
        if self._last_immutable is not None:
            return self._last_immutable
        # Try loading from disk
        anchor_path = self.anchor_dir / "immutable_anchor.json"
        if anchor_path.exists():
            try:
                data = json.loads(anchor_path.read_text(encoding="utf-8"))
                snap = Snapshot(
                    id=data["id"],
                    tick=data["tick"],
                    zon4d_state=data["zon4d_state"],
                    hash32=data.get("hash32"),
                    anchor_type="immutable",
                )
                self._last_immutable = snap
                return snap
            except Exception:
                pass
        # Fallback: reconstruct initial
        return self.load_initial_snapshot()

    def compute_hash(self, snapshot: Snapshot) -> str:
        payload = json.dumps(
            {"id": snapshot.id, "tick": snapshot.tick, "state": snapshot.zon4d_state},
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:32]

    def append_snapshot(self, snapshot: Snapshot) -> None:
        # Write snapshot to disk
        snap_path = self.anchor_dir / f"{snapshot.id}.json"
        data = {
            "id": snapshot.id,
            "tick": snapshot.tick,
            "zon4d_state": snapshot.zon4d_state,
            "hash32": snapshot.hash32,
            "anchor_type": snapshot.anchor_type,
        }
        snap_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        # Track timeline hash
        self._timeline_hashes.append(snapshot.id)

        # If immutable, update the anchor file
        if snapshot.anchor_type == "immutable":
            self._last_immutable = snapshot
            anchor_path = self.anchor_dir / "immutable_anchor.json"
            anchor_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        # Always update initial snapshot reference
        init_path = self.anchor_dir / "initial_snapshot.json"
        if not init_path.exists():
            init_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def timeline_hash_ok(self) -> bool:
        # Phase 1: always OK (no cross-session hash chain yet)
        return True


# ---------------------------------------------------------------------------
# SimpleAPEngine
# ---------------------------------------------------------------------------

class SimpleAPEngine:
    """
    Accept-everything AP Engine for Phase 1.

    Every delta is accepted, every snapshot is finalized.
    Replace with a real rule engine when AP governance is needed.
    """

    def preflight_delta(
        self, snapshot: Snapshot, delta: Delta, ms_budget: int
    ) -> APVerdict:
        return APVerdict.ACCEPT

    def arbitrate_delta(
        self, snapshot: Snapshot, delta: Delta, ms_budget: int
    ) -> Optional[Delta]:
        return delta  # Return as-is

    def finalize_snapshot(
        self, snapshot: Snapshot, ms_budget: int
    ) -> APVerdict:
        return APVerdict.ACCEPT

    def arbitrate_snapshot(
        self, snapshot: Snapshot, ms_budget: int
    ) -> Optional[Snapshot]:
        return snapshot  # Return as-is


# ---------------------------------------------------------------------------
# LoggingPerformanceABI
# ---------------------------------------------------------------------------

class LoggingPerformanceABI:
    """
    Logs PerformanceTasks to stdout and optionally to a JSON file.
    Acts as the bridge until Godot/audio ABI is wired.
    """

    def __init__(self, log_path: Optional[str] = "/tmp/engain_performance_abi.json") -> None:
        self.log_path = log_path

    def schedule_performance(self, tick_id: int, tasks) -> None:
        print(f"[PerformanceABI] tick={tick_id} tasks={len(tasks)}")
        for t in tasks:
            print(f"  [{t.task_type.value}] {t.id} priority={t.priority}")
        if self.log_path and tasks:
            try:
                payload = [
                    {
                        "id": t.id,
                        "tick_id": t.tick_id,
                        "type": t.task_type.value,
                        "priority": t.priority,
                        "payload": t.payload,
                    }
                    for t in tasks
                ]
                Path(self.log_path).write_text(
                    json.dumps({"tick": tick_id, "tasks": payload}, indent=2),
                    encoding="utf-8",
                )
            except Exception:
                pass


# ---------------------------------------------------------------------------
# build_runtime — public factory
# ---------------------------------------------------------------------------

def build_runtime(
    anchor_dir: Optional[Path] = None,
    config: Optional[Dict[str, Any]] = None,
    with_performer: bool = True,
    with_logging_abi: bool = True,
) -> EnginalityRuntime:
    """
    Construct a fully wired EnginalityRuntime ready to tick.

    Args:
        anchor_dir:       Override snapshot persistence directory.
        config:           Runtime config overrides (max_deltas_per_tick, etc.)
        with_performer:   Attach PerformerEngine (True by default).
        with_logging_abi: Attach LoggingPerformanceABI (True by default).

    Returns:
        EnginalityRuntime instance with all protocols satisfied.
    """
    _config = {
        "max_deltas_per_tick": 1024,
        "ap_preflight_budget_ms": 5,
        "ap_final_budget_ms": 10,
    }
    if config:
        _config.update(config)

    anchor_store = SimpleAnchorStore(anchor_dir or _DEFAULT_ANCHOR_DIR)
    ap_engine = SimpleAPEngine()
    zon4d_kernel = SimpleZON4DKernel()
    performer = PerformerEngine() if with_performer else None
    performance_abi = LoggingPerformanceABI() if with_logging_abi else None

    runtime = EnginalityRuntime(
        anchor_store=anchor_store,
        ap_engine=ap_engine,
        zon4d_kernel=zon4d_kernel,
        config=_config,
        performer=performer,
        performance_abi=performance_abi,
    )

    print("[bootstrap] EnginalityRuntime ready")
    print(f"[bootstrap] AnchorStore: {anchor_store.anchor_dir}")
    print(f"[bootstrap] PerformerEngine: {'attached' if performer else 'detached'}")
    return runtime


# ---------------------------------------------------------------------------
# run_tick_loop — convenience driver for smoke testing
# ---------------------------------------------------------------------------

def run_tick_loop(
    runtime: EnginalityRuntime,
    ticks: int = 5,
    delta_time: float = 0.5,
    pending_deltas_per_tick: Optional[List[List[Delta]]] = None,
) -> None:
    """
    Drive the runtime for N ticks. Useful for smoke testing.

    pending_deltas_per_tick: optional list of delta lists, one per tick.
    If shorter than ticks, remaining ticks get empty delta lists.
    """
    for i in range(ticks):
        deltas = []
        if pending_deltas_per_tick and i < len(pending_deltas_per_tick):
            deltas = pending_deltas_per_tick[i]

        ctx = runtime.run_tick(
            pending_deltas=deltas,
            delta_time=delta_time,
        )

        status = "BREACH" if ctx.breached else "OK"
        tasks = len(ctx.performance_tasks)
        alerts = [a for a in ctx.alerts if a["level"] in ("CRITICAL", "WARNING")]

        print(
            f"[tick {ctx.tick_id:04d}] {status} "
            f"deltas_in={len(ctx.deltas_in)} "
            f"accepted={len(ctx.deltas_accepted)} "
            f"tasks={tasks} "
            f"alerts={len(alerts)}"
        )
        for a in alerts:
            print(f"  [{a['level']}] step={a['step']} {a['message']}")


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== EnginalityRuntime bootstrap smoke test ===\n")

    runtime = build_runtime()
    print()

    # 5 clean ticks with no deltas
    run_tick_loop(runtime, ticks=5, delta_time=0.5)
    print()

    # 1 tick with a real delta
    delta = Delta(
        id="d_test_001",
        source_id="smoke_test",
        entity_ref="geralt",
        temporal_index=1.0,
        temporal_scope=(0.0, 100.0),
        parent_ids=[],
        payload={"op": "set", "path": ["entities", "geralt"], "value": {"hp": 100, "pos": [0, 0, 0]}},
    )
    ctx = runtime.run_tick(pending_deltas=[delta], delta_time=0.5)
    assert not ctx.breached, f"Unexpected breach: {ctx.alerts}"
    assert ctx.snapshot_out is not None
    assert ctx.snapshot_out.zon4d_state["entities"]["geralt"]["hp"] == 100
    print(f"\n[tick {ctx.tick_id:04d}] Delta applied — geralt.hp = {ctx.snapshot_out.zon4d_state['entities']['geralt']['hp']}")

    print("\n✅ bootstrap smoke test passed")
