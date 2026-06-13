#!/usr/bin/env python3
"""
trixel_world_adapter.py — EngAIn adapter layer for the Trixel World kernel.

Bridges the pure kernel (trixel_world_mr.py) into the live EngAIn runtime:

- Holds mutable in-memory world snapshot
- Loads/saves snapshot to disk
- Queues and validates deltas
- Calls step_trixel_world(...) from trixel_world_mr
- Exposes ZW-style command handlers:
    !zw/world.set_terrain
    !zw/world.fill_region
    !zw/world.add_feature
    !zw/world.set_skin
    !zw/world.add_override
    !zw/world.remove_override
    !zw/world.set_state_flag
    !zw/world.clear_state_flag
    !zw/world.register_skin

- Provides read APIs for renderers/tools:
    get_snapshot(), get_cells(), get_features(), get_skin_table(),
    get_walkable_cells(), get_cells_by_terrain(), get_cells_by_feature(),
    get_cell_with_skin(), get_effective_walkability()

Design:
- This adapter does AP/canon checks only for things that can be
  checked locally (bounds, known IDs, basic type sanity).
- Higher-level story canon checks should happen upstream in the
  scene_shell_builder or narrative planner.
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from .trixel_world_mr import (
    WorldGridConfig,
    TerrainType,
    step_trixel_world,
    create_empty_grid,
    make_cell_id,
    get_walkable_cells,
    get_cells_by_terrain,
    get_cells_by_feature,
    get_skin_for_cell,
    resolve_cell_walkability,
)


class TrixelWorldAdapter:
    """
    EngAIn adapter for the Trixel World kernel.

    This is the object the rest of EngAIn talks to.
    It owns:
      - current world snapshot (dict)
      - immutable WorldGridConfig
      - delta queue
      - simple AP/canon validation
      - ZW-style command handlers
    """

    def __init__(
        self,
        save_path: str,
        config: Optional[WorldGridConfig] = None,
        autoload: bool = True,
        autosave: bool = True,
    ) -> None:
        """
        Args:
            save_path: filesystem path to JSON snapshot file.
            config: world grid configuration; if None, uses the kernel default.
            autoload: if True, tries to load existing snapshot from save_path.
            autosave: if True, save after any flush with accepted deltas.
        """
        self._save_path = save_path
        self._config = config or WorldGridConfig()
        self._snapshot: Dict[str, Any] = self._make_initial_snapshot()
        self._delta_queue: List[Dict[str, Any]] = []
        self._next_delta_id: int = 1
        self._autosave: bool = autosave

        if autoload:
            self.load_snapshot()

    @property
    def config(self) -> WorldGridConfig:
        """Read-only access to grid configuration."""
        return self._config

    # ============================================================
    # Snapshot management
    # ============================================================

    def _make_initial_snapshot(self) -> Dict[str, Any]:
        """Create a blank world snapshot using the kernel helpers."""
        cells = create_empty_grid(self._config)
        return {
            "trixel_world": {
                "cells": cells,
                "features": {},
                "skin_table": {},
                "tick": 0.0,
            }
        }

    def get_snapshot(self) -> Dict[str, Any]:
        """Return a deep copy of the current snapshot for read-only use."""
        return json.loads(json.dumps(self._snapshot))

    def load_snapshot(self) -> None:
        """Load snapshot from disk if present; otherwise keep current."""
        if not os.path.exists(self._save_path):
            return
        try:
            with open(self._save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Minimal sanity check
            if "trixel_world" in data and "cells" in data["trixel_world"]:
                self._snapshot = data
        except (OSError, json.JSONDecodeError) as e:
            print(f"[TrixelWorldAdapter] Failed to load snapshot: {e}")

    def save_snapshot(self) -> None:
        """Persist current snapshot to disk."""
        save_dir = os.path.dirname(self._save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        try:
            with open(self._save_path, "w", encoding="utf-8") as f:
                json.dump(self._snapshot, f, indent=2, sort_keys=True)
        except OSError as e:
            print(f"[TrixelWorldAdapter] Failed to save snapshot: {e}")

    # ============================================================
    # Delta queuing + AP validation
    # ============================================================

    def _next_id(self) -> str:
        did = f"d_{self._next_delta_id:06d}"
        self._next_delta_id += 1
        return did

    def queue_delta(self, dtype: str, payload: Dict[str, Any]) -> Optional[str]:
        """
        Queue a delta after basic AP validation.

        Returns:
            delta_id if accepted into queue, None if rejected.
        """
        delta_id = self._next_id()
        delta = {"id": delta_id, "type": dtype, "payload": payload}

        ok, reason = self._validate_delta(delta)
        if not ok:
            print(f"[TrixelWorldAdapter] Rejecting delta {delta_id}: {reason}")
            return None

        self._delta_queue.append(delta)
        return delta_id

    def _validate_delta(self, delta: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Cheap AP/canon checks before the kernel sees the delta.

        We only check what we can know locally (IDs, bounds, enums).
        """
        dtype = delta.get("type")
        payload = delta.get("payload", {})
        world = self._snapshot.get("trixel_world", {})
        cells = world.get("cells", {})
        features = world.get("features", {})
        skin_table = world.get("skin_table", {})

        # Helper: validate cell IDs exist and are in-bounds
        def _check_cell_ids(cell_ids: List[str]) -> Tuple[bool, str]:
            for cid in cell_ids:
                if cid not in cells:
                    return False, f"Unknown cell_id: {cid}"
            return True, ""

        if dtype == "set_terrain":
            cell_ids = payload.get("cell_ids", [])
            terrain_type = payload.get("terrain_type", "")
            ok, reason = _check_cell_ids(cell_ids)
            if not ok:
                return False, reason
            if not terrain_type:
                return False, "Missing terrain_type"
            if terrain_type not in [t.value for t in TerrainType]:
                return False, f"Unknown terrain_type: {terrain_type}"
            return True, ""

        if dtype == "set_skin":
            cell_ids = payload.get("cell_ids", [])
            skin_id = payload.get("skin_id", "")
            ok, reason = _check_cell_ids(cell_ids)
            if not ok:
                return False, reason
            if not skin_id:
                return False, "Missing skin_id"
            # Skin may not exist yet; allow register + set ordering both ways.
            return True, ""

        if dtype in ("add_override", "remove_override"):
            cell_ids = payload.get("cell_ids", [])
            tag = payload.get("tag", "")
            ok, reason = _check_cell_ids(cell_ids)
            if not ok:
                return False, reason
            if not tag:
                return False, "Missing override tag"
            return True, ""

        if dtype in ("set_state_flag", "clear_state_flag"):
            cell_ids = payload.get("cell_ids", [])
            flag = payload.get("flag", "")
            ok, reason = _check_cell_ids(cell_ids)
            if not ok:
                return False, reason
            if not flag:
                return False, "Missing state flag"
            return True, ""

        if dtype == "add_feature":
            feature_id = payload.get("feature_id", "")
            if not feature_id:
                return False, "Missing feature_id"
            if feature_id in features:
                return False, f"Feature already exists: {feature_id}"
            cell_ids = payload.get("cell_ids", [])
            ok, reason = _check_cell_ids(cell_ids)
            if not ok:
                return False, reason
            return True, ""

        if dtype == "assign_feature":
            feature_id = payload.get("feature_id", "")
            cell_ids = payload.get("cell_ids", [])
            if not feature_id:
                return False, "Missing feature_id"
            if feature_id not in features:
                return False, f"Unknown feature_id: {feature_id}"
            ok, reason = _check_cell_ids(cell_ids)
            if not ok:
                return False, reason
            return True, ""

        if dtype == "register_skin":
            skin_id = payload.get("skin_id", "")
            if not skin_id:
                return False, "Missing skin_id"
            if skin_id in skin_table:
                print(f"[TrixelWorldAdapter] Warning: overwriting skin_id {skin_id}")
            return True, ""

        if dtype == "fill_region":
            terrain_type = payload.get("terrain_type", "")
            if not terrain_type:
                return False, "Missing terrain_type"
            if terrain_type not in [t.value for t in TerrainType]:
                return False, f"Unknown terrain_type: {terrain_type}"
            x_min = payload.get("x_min")
            x_max = payload.get("x_max")
            y_min = payload.get("y_min")
            y_max = payload.get("y_max")
            if any(v is None for v in (x_min, x_max, y_min, y_max)):
                return False, "Missing region bounds"
            if not (0 <= x_min <= x_max < self._config.grid_width):
                return False, "Region x-bounds out of range"
            if not (0 <= y_min <= y_max < self._config.grid_height):
                return False, "Region y-bounds out of range"
            return True, ""

        # Unknown types are rejected here; extend as you add more.
        return False, f"Unknown delta type: {dtype}"

    # ============================================================
    # Flush: apply queued deltas to kernel
    # ============================================================

    def flush(self, delta_time: float = 0.0) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Apply all queued deltas to the kernel in one step.

        Returns:
            accepted_delta_ids, alerts
        """
        if not self._delta_queue:
            return [], []

        snapshot_out, accepted_ids, alerts = step_trixel_world(
            snapshot_in=self._snapshot,
            deltas=self._delta_queue,
            config=self._config,
            delta_time=delta_time,
        )

        self._snapshot = snapshot_out
        self._delta_queue = []

        if self._autosave and accepted_ids:
            self.save_snapshot()

        return accepted_ids, alerts

    # ============================================================
    # Cell protection — shields critical cells from bulk fills
    # ============================================================

    def _is_cell_protected(self, cell_dict: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if a cell should be protected from bulk terrain overwrites.

        A cell is protected if it has:
          - non-empty feature_ids (belongs to a named feature)
          - non-empty override_tags (has behavior modifications)
          - non-empty socket_ids (has spawn/interaction points)
          - non-empty state_flags (has dynamic state)

        Additionally, cells belonging to features with confidence == "explicit"
        get the strongest protection.

        Returns:
            (is_protected, reason_string)
        """
        feature_ids = cell_dict.get("feature_ids", [])
        override_tags = cell_dict.get("override_tags", [])
        socket_ids = cell_dict.get("socket_ids", [])
        state_flags = cell_dict.get("state_flags", [])

        if feature_ids:
            # Check if any owning feature has explicit confidence
            features = self._snapshot.get("trixel_world", {}).get("features", {})
            for fid in feature_ids:
                feat = features.get(fid, {})
                if feat.get("confidence") == "explicit":
                    return True, f"feature:{fid}(explicit)"
            # Still protected, just lower priority
            return True, f"feature:{','.join(feature_ids)}"

        if override_tags:
            return True, f"override:{','.join(override_tags)}"

        if socket_ids:
            return True, f"socket:{','.join(socket_ids)}"

        if state_flags:
            return True, f"state:{','.join(state_flags)}"

        return False, ""

    def _get_protected_in_region(
        self,
        x_min: int, y_min: int,
        x_max: int, y_max: int,
    ) -> Dict[str, str]:
        """Scan a region and return protected cell_ids with reasons.

        Returns:
            {cell_id: reason_string} for all protected cells in the region.
        """
        cells = self._snapshot.get("trixel_world", {}).get("cells", {})
        protected: Dict[str, str] = {}
        for gy in range(y_min, y_max + 1):
            for gx in range(x_min, x_max + 1):
                cid = make_cell_id(gx, gy)
                cell = cells.get(cid)
                if cell is None:
                    continue
                is_prot, reason = self._is_cell_protected(cell)
                if is_prot:
                    protected[cid] = reason
        return protected

    # ============================================================
    # ZW-style command handlers
    # ============================================================

    # Each handler returns a dict shaped like a ZW broker response:
    # {
    #   "ok": bool,
    #   "accepted_ids": [...],
    #   "alerts": [...],
    #   "message": str,
    # }

    def handle_set_terrain(self, cell_ids: List[str], terrain_type: str) -> Dict[str, Any]:
        did = self.queue_delta(
            "set_terrain",
            {"cell_ids": cell_ids, "terrain_type": terrain_type},
        )
        if not did:
            return {"ok": False, "accepted_ids": [], "alerts": [], "message": "Rejected by AP validation"}
        accepted, alerts = self.flush()
        return {"ok": did in accepted, "accepted_ids": accepted, "alerts": alerts, "message": "set_terrain applied"}

    def handle_fill_region(
        self,
        x_min: int,
        y_min: int,
        x_max: int,
        y_max: int,
        terrain_type: str,
        skin_id: Optional[str] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """Fill a rectangular region with terrain, protecting critical cells.

        When force=False (default), cells with features, overrides, sockets,
        or state_flags are skipped. The fill only touches unprotected cells.

        When force=True, all cells in the region are overwritten regardless.
        Use force=True only for explicit user overrides ("I know what I'm doing").

        Returns:
            Standard response dict, plus:
              "protected_cells": {cell_id: reason} — cells that were skipped
              "cells_filled": int — how many cells were actually filled
              "cells_skipped": int — how many were protected
        """
        # Check for protected cells unless forced
        protected: Dict[str, str] = {}
        if not force:
            protected = self._get_protected_in_region(x_min, y_min, x_max, y_max)

        if not protected:
            # Fast path: no protected cells, use fill_region as-is
            payload: Dict[str, Any] = {
                "x_min": x_min,
                "y_min": y_min,
                "x_max": x_max,
                "y_max": y_max,
                "terrain_type": terrain_type,
            }
            if skin_id is not None:
                payload["skin_id"] = skin_id
            did = self.queue_delta("fill_region", payload)
            if not did:
                return {
                    "ok": False, "accepted_ids": [], "alerts": [],
                    "message": "Rejected by AP validation",
                    "protected_cells": {}, "cells_filled": 0, "cells_skipped": 0,
                }
            accepted, alerts = self.flush()
            total_cells = (x_max - x_min + 1) * (y_max - y_min + 1)
            return {
                "ok": did in accepted, "accepted_ids": accepted,
                "alerts": alerts, "message": "fill_region applied",
                "protected_cells": {}, "cells_filled": total_cells, "cells_skipped": 0,
            }

        # Slow path: collect unprotected cells and use set_terrain instead
        unprotected_ids: List[str] = []
        for gy in range(y_min, y_max + 1):
            for gx in range(x_min, x_max + 1):
                cid = make_cell_id(gx, gy)
                if cid not in protected:
                    unprotected_ids.append(cid)

        if not unprotected_ids:
            # Every cell in the region is protected
            return {
                "ok": True, "accepted_ids": [], "alerts": [],
                "message": "fill_region skipped: all cells protected",
                "protected_cells": protected,
                "cells_filled": 0,
                "cells_skipped": len(protected),
            }

        # Queue set_terrain for unprotected cells
        did = self.queue_delta(
            "set_terrain",
            {"cell_ids": unprotected_ids, "terrain_type": terrain_type},
        )
        if not did:
            return {
                "ok": False, "accepted_ids": [], "alerts": [],
                "message": "Rejected by AP validation",
                "protected_cells": protected,
                "cells_filled": 0,
                "cells_skipped": len(protected),
            }

        # If skin_id provided, also set skin on the same cells
        skin_did = None
        if skin_id is not None:
            skin_did = self.queue_delta(
                "set_skin",
                {"cell_ids": unprotected_ids, "skin_id": skin_id},
            )

        accepted, alerts = self.flush()

        return {
            "ok": did in accepted,
            "accepted_ids": accepted,
            "alerts": alerts,
            "message": f"fill_region applied with {len(protected)} cells protected",
            "protected_cells": protected,
            "cells_filled": len(unprotected_ids),
            "cells_skipped": len(protected),
        }

    def handle_set_skin(self, cell_ids: List[str], skin_id: str) -> Dict[str, Any]:
        did = self.queue_delta(
            "set_skin",
            {"cell_ids": cell_ids, "skin_id": skin_id},
        )
        if not did:
            return {"ok": False, "accepted_ids": [], "alerts": [], "message": "Rejected by AP validation"}
        accepted, alerts = self.flush()
        return {"ok": did in accepted, "accepted_ids": accepted, "alerts": alerts, "message": "set_skin applied"}

    def handle_add_override(self, cell_ids: List[str], tag: str) -> Dict[str, Any]:
        did = self.queue_delta(
            "add_override",
            {"cell_ids": cell_ids, "tag": tag},
        )
        if not did:
            return {"ok": False, "accepted_ids": [], "alerts": [], "message": "Rejected by AP validation"}
        accepted, alerts = self.flush()
        return {"ok": did in accepted, "accepted_ids": accepted, "alerts": alerts, "message": "add_override applied"}

    def handle_remove_override(self, cell_ids: List[str], tag: str) -> Dict[str, Any]:
        did = self.queue_delta(
            "remove_override",
            {"cell_ids": cell_ids, "tag": tag},
        )
        if not did:
            return {"ok": False, "accepted_ids": [], "alerts": [], "message": "Rejected by AP validation"}
        accepted, alerts = self.flush()
        return {"ok": did in accepted, "accepted_ids": accepted, "alerts": alerts, "message": "remove_override applied"}

    def handle_add_feature(
        self,
        feature_id: str,
        feature_type: str,
        cell_ids: List[str],
        narrative_source: str = "",
        confidence: str = "inferred_medium",
        activation_conditions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        payload = {
            "feature_id": feature_id,
            "feature_type": feature_type,
            "cell_ids": cell_ids,
            "narrative_source": narrative_source,
            "confidence": confidence,
            "activation_conditions": activation_conditions or [],
        }
        did = self.queue_delta("add_feature", payload)
        if not did:
            return {"ok": False, "accepted_ids": [], "alerts": [], "message": "Rejected by AP validation"}
        accepted, alerts = self.flush()
        return {"ok": did in accepted, "accepted_ids": accepted, "alerts": alerts, "message": "add_feature applied"}

    def handle_assign_feature(self, feature_id: str, cell_ids: List[str]) -> Dict[str, Any]:
        payload = {
            "feature_id": feature_id,
            "cell_ids": cell_ids,
        }
        did = self.queue_delta("assign_feature", payload)
        if not did:
            return {"ok": False, "accepted_ids": [], "alerts": [], "message": "Rejected by AP validation"}
        accepted, alerts = self.flush()
        return {"ok": did in accepted, "accepted_ids": accepted, "alerts": alerts, "message": "assign_feature applied"}

    def handle_set_state_flag(self, cell_ids: List[str], flag: str) -> Dict[str, Any]:
        did = self.queue_delta(
            "set_state_flag",
            {"cell_ids": cell_ids, "flag": flag},
        )
        if not did:
            return {"ok": False, "accepted_ids": [], "alerts": [], "message": "Rejected by AP validation"}
        accepted, alerts = self.flush()
        return {"ok": did in accepted, "accepted_ids": accepted, "alerts": alerts, "message": "set_state_flag applied"}

    def handle_clear_state_flag(self, cell_ids: List[str], flag: str) -> Dict[str, Any]:
        did = self.queue_delta(
            "clear_state_flag",
            {"cell_ids": cell_ids, "flag": flag},
        )
        if not did:
            return {"ok": False, "accepted_ids": [], "alerts": [], "message": "Rejected by AP validation"}
        accepted, alerts = self.flush()
        return {"ok": did in accepted, "accepted_ids": accepted, "alerts": alerts, "message": "clear_state_flag applied"}

    def handle_register_skin(
        self,
        skin_id: str,
        terrain_type: str,
        module_family: str,
        autotile_role: str = "center",
        asset_ref: str = "",
        style_tags: Optional[List[str]] = None,
        supports_variants: bool = True,
        variant_count: int = 1,
        variant_rules: str = "",
    ) -> Dict[str, Any]:
        payload = {
            "skin_id": skin_id,
            "terrain_type": terrain_type,
            "module_family": module_family,
            "autotile_role": autotile_role,
            "asset_ref": asset_ref,
            "style_tags": style_tags or [],
            "supports_variants": supports_variants,
            "variant_count": variant_count,
            "variant_rules": variant_rules,
        }
        did = self.queue_delta("register_skin", payload)
        if not did:
            return {"ok": False, "accepted_ids": [], "alerts": [], "message": "Rejected by AP validation"}
        accepted, alerts = self.flush()
        return {"ok": did in accepted, "accepted_ids": accepted, "alerts": alerts, "message": "register_skin applied"}

    # ============================================================
    # Read APIs for renderers / tools
    # ============================================================

    def get_cells(self) -> Dict[str, Dict[str, Any]]:
        return self._snapshot["trixel_world"]["cells"]

    def get_features(self) -> Dict[str, Dict[str, Any]]:
        return self._snapshot["trixel_world"]["features"]

    def get_skin_table(self) -> Dict[str, Dict[str, Any]]:
        return self._snapshot["trixel_world"]["skin_table"]

    def get_tick(self) -> float:
        return float(self._snapshot["trixel_world"].get("tick", 0.0))

    def get_walkable_cells(self) -> List[str]:
        cells = self.get_cells()
        return get_walkable_cells(cells)

    def get_cells_by_terrain(self, terrain_type: str) -> List[str]:
        cells = self.get_cells()
        return get_cells_by_terrain(cells, terrain_type)

    def get_cells_by_feature(self, feature_id: str) -> List[str]:
        cells = self.get_cells()
        return get_cells_by_feature(cells, feature_id)

    def get_cell(self, cell_id: str) -> Optional[Dict[str, Any]]:
        return self.get_cells().get(cell_id)

    def get_cell_with_skin(self, cell_id: str) -> Optional[Dict[str, Any]]:
        """
        Return cell dict with resolved skin_binding attached.
        Returns None if cell_id is unknown.
        """
        world = self._snapshot["trixel_world"]
        cells = world["cells"]
        skin_table = world["skin_table"]
        if cell_id not in cells:
            return None
        cell = cells[cell_id]
        x = cell["x"]
        y = cell["y"]

        # Compute neighbor terrains for autotile role
        neighbors: Dict[str, Optional[str]] = {}
        for direction, (dx, dy) in {
            "n": (0, -1),
            "s": (0, 1),
            "e": (1, 0),
            "w": (-1, 0),
            "ne": (1, -1),
            "nw": (-1, -1),
            "se": (1, 1),
            "sw": (-1, 1),
        }.items():
            nx = x + dx
            ny = y + dy
            if 0 <= nx < self._config.grid_width and 0 <= ny < self._config.grid_height:
                nid = make_cell_id(nx, ny)
                neighbors[direction] = cells.get(nid, {}).get("terrain_type")
            else:
                neighbors[direction] = None

        skin_binding = get_skin_for_cell(cell, skin_table, neighbors)

        out = dict(cell)
        out["skin_binding"] = skin_binding  # None if unskinned, dict otherwise
        return out

    def get_effective_walkability(self, cell_id: str) -> Optional[bool]:
        cells = self.get_cells()
        cell = cells.get(cell_id)
        if cell is None:
            return None
        return resolve_cell_walkability(cell)


# ==================================================================
# Minimal CLI/manual test harness
# ==================================================================

if __name__ == "__main__":
    """
    Manual smoke test:
      - create adapter with temp path
      - fill a region with sand
      - register a skin
      - apply skin
      - print summary
    """
    adapter = TrixelWorldAdapter(
        save_path="/tmp/trixel_world_snapshot.json",
        autoload=False,
    )

    # Fill a 4x4 region with sand
    resp = adapter.handle_fill_region(
        x_min=2,
        y_min=2,
        x_max=5,
        y_max=5,
        terrain_type=TerrainType.SAND.value,
    )
    print("fill_region:", resp)

    # Register a basic sand skin
    resp = adapter.handle_register_skin(
        skin_id="beach_primordial_v1",
        terrain_type=TerrainType.SAND.value,
        module_family="sand_base",
        autotile_role="center",
        asset_ref="res://tiles/beach_primordial_v1.png",
        style_tags=["pixel", "primordial"],
    )
    print("register_skin:", resp)

    # Set skin on all sand cells
    sand_cells = adapter.get_cells_by_terrain(TerrainType.SAND.value)
    resp = adapter.handle_set_skin(sand_cells, "beach_primordial_v1")
    print("set_skin:", resp)

    # Inspect one cell
    if sand_cells:
        cid = sand_cells[0]
        cell = adapter.get_cell_with_skin(cid)
        walk = adapter.get_effective_walkability(cid)
        print("sample cell:", cid, json.dumps(cell, indent=2))
        print("walkable:", walk)
