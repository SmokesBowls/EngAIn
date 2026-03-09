#!/usr/bin/env python3
"""
trixel_world_zw.py — ZW broker glue for the Trixel World subsystem.

Responsibility:
Map parsed ZW commands onto TrixelWorldAdapter handler calls.

Command lane:
ZW parser → broker → TrixelWorldZWRouter → TrixelWorldAdapter → trixel_world_mr kernel

This file does NOT:
- parse raw text into ZW commands
- persist snapshots (adapter handles that)
- perform heavy AP/canon checks (adapter + upstream planners handle that)

It only:
- accept already-parsed ZW messages
- dispatch them to the adapter
- return normalized responses for the broker
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .trixel_world_adapter import TrixelWorldAdapter
from .trixel_world_mr import TerrainType, WorldGridConfig
from .scene_shell_builder import build_scene_shell


class TrixelWorldZWRouter:
    """
    Thin ZW-facing façade over TrixelWorldAdapter.

    Expected ZW message shape (already parsed):

        {
            "command": "!zw/world.set_terrain",
            "payload": {
                ... command-specific fields ...
            },
            "meta": {
                "request_id": "...",
                "source": "empire" | "tool" | "test",
                ...
            }
        }

    The router ignores `meta` except for passing request_id through in responses.
    """

    def __init__(
        self,
        adapter: Optional[TrixelWorldAdapter] = None,
        save_path: str = "/tmp/trixel_world_snapshot.json",
        config: Optional[WorldGridConfig] = None,
    ) -> None:
        """
        Args:
            adapter: Optional pre-constructed TrixelWorldAdapter.
            save_path: Used if we construct our own adapter.
            config: World configuration if we construct our own adapter.
        """
        if adapter is not None:
            self._adapter = adapter
        else:
            self._adapter = TrixelWorldAdapter(
                save_path=save_path,
                config=config,
                autoload=True,
                autosave=True,
            )

    def handle_zw(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for the ZW broker.

        Args:
            message: Parsed ZW command dict:
                {
                    "command": "!zw/world.set_terrain",
                    "payload": {...},
                    "meta": {...}
                }

        Returns:
            {
                "ok": bool,
                "command": str,
                "request_id": str,
                "result": {adapter_response},
                "error": str,
            }
        """
        if not isinstance(message, dict):
            return {
                "ok": False,
                "command": "",
                "request_id": "",
                "result": {},
                "error": "TrixelWorldZWRouter exception: message must be a dict",
            }

        command = str(message.get("command", "") or "")
        payload = message.get("payload", {}) or {}
        meta = message.get("meta", {}) or {}

        if not isinstance(payload, dict):
            payload = {}
        if not isinstance(meta, dict):
            meta = {}

        request_id = str(meta.get("request_id", "") or "")

        try:
            result = self._dispatch(command, payload)
            return {
                "ok": bool(result.get("ok", False)),
                "command": command,
                "request_id": request_id,
                "result": result,
                "error": "",
            }
        except Exception as exc:
            return {
                "ok": False,
                "command": command,
                "request_id": request_id,
                "result": {},
                "error": f"TrixelWorldZWRouter exception: {exc}",
            }

    def _dispatch(self, command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Map ZW command strings onto adapter handler calls."""
        if command == "!zw/world.set_terrain":
            return self._cmd_set_terrain(payload)

        if command == "!zw/world.fill_region":
            return self._cmd_fill_region(payload)

        if command == "!zw/world.add_feature":
            return self._cmd_add_feature(payload)

        if command == "!zw/world.assign_feature":
            return self._cmd_assign_feature(payload)

        if command == "!zw/world.set_skin":
            return self._cmd_set_skin(payload)

        if command == "!zw/world.add_override":
            return self._cmd_add_override(payload)

        if command == "!zw/world.remove_override":
            return self._cmd_remove_override(payload)

        if command == "!zw/world.set_state_flag":
            return self._cmd_set_state_flag(payload)

        if command == "!zw/world.clear_state_flag":
            return self._cmd_clear_state_flag(payload)

        if command == "!zw/world.register_skin":
            return self._cmd_register_skin(payload)

        if command == "!zw/world.get_snapshot":
            return self._cmd_get_snapshot(payload)

        if command == "!zw/world.get_cell":
            return self._cmd_get_cell(payload)

        if command == "!zw/world.get_cells_by_terrain":
            return self._cmd_get_cells_by_terrain(payload)

        if command == "!zw/world.get_walkable_cells":
            return self._cmd_get_walkable_cells(payload)

        if command == "!zw/world.build_scene_shell":
            return self._cmd_build_scene_shell(payload)

        return {
            "ok": False,
            "accepted_ids": [],
            "alerts": [],
            "message": f"Unknown TrixelWorld command: {command}",
        }

    def _normalize_terrain_type(self, terrain_type: Any) -> Any:
        """Accept enum instances, enum names, or raw values."""
        if isinstance(terrain_type, TerrainType):
            return terrain_type.value
        if isinstance(terrain_type, str) and terrain_type in TerrainType.__members__:
            return TerrainType[terrain_type].value
        return terrain_type

    def _cmd_set_terrain(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        cell_ids = payload.get("cell_ids", []) or []
        terrain_type = self._normalize_terrain_type(payload.get("terrain_type", ""))
        return self._adapter.handle_set_terrain(cell_ids, terrain_type)

    def _cmd_fill_region(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        x_min = int(payload.get("x_min", 0))
        y_min = int(payload.get("y_min", 0))
        x_max = int(payload.get("x_max", 0))
        y_max = int(payload.get("y_max", 0))
        terrain_type = self._normalize_terrain_type(payload.get("terrain_type", ""))
        skin_id = payload.get("skin_id")

        return self._adapter.handle_fill_region(
            x_min=x_min,
            y_min=y_min,
            x_max=x_max,
            y_max=y_max,
            terrain_type=terrain_type,
            skin_id=skin_id,
        )

    def _cmd_add_feature(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        feature_id = payload.get("feature_id", "")
        feature_type = payload.get("feature_type", "")
        cell_ids = payload.get("cell_ids", []) or []
        narrative_source = payload.get("narrative_source", "")
        confidence = payload.get("confidence", "inferred_medium")
        activation_conditions = payload.get("activation_conditions", []) or []

        return self._adapter.handle_add_feature(
            feature_id=feature_id,
            feature_type=feature_type,
            cell_ids=cell_ids,
            narrative_source=narrative_source,
            confidence=confidence,
            activation_conditions=activation_conditions,
        )

    def _cmd_assign_feature(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        feature_id = payload.get("feature_id", "")
        cell_ids = payload.get("cell_ids", []) or []
        return self._adapter.handle_assign_feature(feature_id, cell_ids)

    def _cmd_set_skin(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        cell_ids = payload.get("cell_ids", []) or []
        skin_id = payload.get("skin_id", "")
        return self._adapter.handle_set_skin(cell_ids, skin_id)

    def _cmd_add_override(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        cell_ids = payload.get("cell_ids", []) or []
        tag = payload.get("tag", "")
        return self._adapter.handle_add_override(cell_ids, tag)

    def _cmd_remove_override(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        cell_ids = payload.get("cell_ids", []) or []
        tag = payload.get("tag", "")
        return self._adapter.handle_remove_override(cell_ids, tag)

    def _cmd_set_state_flag(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        cell_ids = payload.get("cell_ids", []) or []
        flag = payload.get("flag", "")
        return self._adapter.handle_set_state_flag(cell_ids, flag)

    def _cmd_clear_state_flag(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        cell_ids = payload.get("cell_ids", []) or []
        flag = payload.get("flag", "")
        return self._adapter.handle_clear_state_flag(cell_ids, flag)

    def _cmd_register_skin(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        skin_id = payload.get("skin_id", "")
        terrain_type = self._normalize_terrain_type(payload.get("terrain_type", ""))
        module_family = payload.get("module_family", "")
        autotile_role = payload.get("autotile_role", "center")
        asset_ref = payload.get("asset_ref", "")
        style_tags = payload.get("style_tags", []) or []
        supports_variants = bool(payload.get("supports_variants", True))
        variant_count = int(payload.get("variant_count", 1))
        variant_rules = payload.get("variant_rules", "")

        return self._adapter.handle_register_skin(
            skin_id=skin_id,
            terrain_type=terrain_type,
            module_family=module_family,
            autotile_role=autotile_role,
            asset_ref=asset_ref,
            style_tags=style_tags,
            supports_variants=supports_variants,
            variant_count=variant_count,
            variant_rules=variant_rules,
        )

    def _cmd_get_snapshot(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        snapshot = self._adapter.get_snapshot()
        return {
            "ok": True,
            "accepted_ids": [],
            "alerts": [],
            "message": "snapshot",
            "snapshot": snapshot,
        }

    def _cmd_get_cell(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        cell_id = payload.get("cell_id", "")
        raw_cell = self._adapter.get_cell(cell_id)
        if raw_cell is None:
            return {
                "ok": False,
                "accepted_ids": [],
                "alerts": [],
                "message": f"Unknown cell_id: {cell_id}",
            }

        cell = self._adapter.get_cell_with_skin(cell_id)
        if cell is None:
            cell = dict(raw_cell)
            cell["skin_binding"] = None

        return {
            "ok": True,
            "accepted_ids": [],
            "alerts": [],
            "message": "cell",
            "cell": cell,
        }

    def _cmd_get_cells_by_terrain(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        terrain_type = self._normalize_terrain_type(payload.get("terrain_type", ""))
        ids = self._adapter.get_cells_by_terrain(terrain_type)
        return {
            "ok": True,
            "accepted_ids": [],
            "alerts": [],
            "message": "cells_by_terrain",
            "cell_ids": ids,
        }

    def _cmd_get_walkable_cells(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        ids = self._adapter.get_walkable_cells()
        return {
            "ok": True,
            "accepted_ids": [],
            "alerts": [],
            "message": "walkable_cells",
            "cell_ids": ids,
        }

    def _cmd_build_scene_shell(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        ZW command: !zw/world.build_scene_shell

        Returns proposed deltas ONLY — does not apply them to the world.
        The caller decides whether to feed them back through the adapter.
        """
        scene_id = str(payload.get("scene_id", "") or "").strip()
        chapter_text = str(payload.get("chapter_text", "") or "")
        corpus_hints = payload.get("corpus_hints") or {}
        world_tags = payload.get("world_tags") or []

        if not isinstance(corpus_hints, dict):
            return {
                "ok": False, "accepted_ids": [], "alerts": [],
                "message": "corpus_hints must be a dict",
                "scene_id": scene_id, "deltas": [],
            }
        if not isinstance(world_tags, list):
            return {
                "ok": False, "accepted_ids": [], "alerts": [],
                "message": "world_tags must be a list",
                "scene_id": scene_id, "deltas": [],
            }
        if not scene_id:
            return {
                "ok": False, "accepted_ids": [], "alerts": [],
                "message": "Missing scene_id",
                "scene_id": "", "deltas": [],
            }
        if not chapter_text.strip():
            return {
                "ok": False, "accepted_ids": [], "alerts": [],
                "message": "Missing chapter_text",
                "scene_id": scene_id, "deltas": [],
            }

        cfg_override = payload.get("grid_config") or {}
        if not isinstance(cfg_override, dict):
            return {
                "ok": False, "accepted_ids": [], "alerts": [],
                "message": "grid_config must be a dict",
                "scene_id": scene_id, "deltas": [],
            }

        try:
            cfg = WorldGridConfig(
                grid_width=int(cfg_override.get("grid_width", 64)),
                grid_height=int(cfg_override.get("grid_height", 64)),
                tile_size=int(cfg_override.get("tile_size", 16)),
            )
        except (TypeError, ValueError) as exc:
            return {
                "ok": False, "accepted_ids": [], "alerts": [],
                "message": f"Invalid grid_config values: {exc}",
                "scene_id": scene_id, "deltas": [],
            }

        try:
            deltas = build_scene_shell(
                scene_id=scene_id,
                chapter_text=chapter_text,
                config=cfg,
                corpus_hints=corpus_hints,
                world_tags=world_tags,
            )
        except Exception as exc:
            return {
                "ok": False, "accepted_ids": [], "alerts": [],
                "message": f"scene_shell_builder error: {exc}",
                "scene_id": scene_id, "deltas": [],
            }

        return {
            "ok": True,
            "accepted_ids": [],
            "alerts": [],
            "message": "scene_shell_built",
            "scene_id": scene_id,
            "deltas": deltas,
        }


if __name__ == "__main__":
    """
    Quick manual test:
    - Construct router (with its own adapter)
    - Send a fill_region + register_skin + set_skin sequence
    - Fetch snapshot and one sample cell
    """
    router = TrixelWorldZWRouter()

    msg = {
        "command": "!zw/world.fill_region",
        "payload": {
            "x_min": 2,
            "y_min": 2,
            "x_max": 5,
            "y_max": 5,
            "terrain_type": TerrainType.SAND.value,
        },
        "meta": {"request_id": "test_fill"},
    }
    print("fill_region:", router.handle_zw(msg))

    msg = {
        "command": "!zw/world.register_skin",
        "payload": {
            "skin_id": "beach_primordial_v1",
            "terrain_type": TerrainType.SAND.value,
            "module_family": "sand_base",
            "autotile_role": "center",
            "asset_ref": "res://tiles/beach_primordial_v1.png",
            "style_tags": ["pixel", "primordial"],
        },
        "meta": {"request_id": "test_skin"},
    }
    print("register_skin:", router.handle_zw(msg))

    sand_cells = router.handle_zw(
        {
            "command": "!zw/world.get_cells_by_terrain",
            "payload": {"terrain_type": TerrainType.SAND.value},
            "meta": {"request_id": "get_sand"},
        }
    )["result"]["cell_ids"]

    msg = {
        "command": "!zw/world.set_skin",
        "payload": {"cell_ids": sand_cells, "skin_id": "beach_primordial_v1"},
        "meta": {"request_id": "set_skin"},
    }
    print("set_skin:", router.handle_zw(msg))

    if sand_cells:
        cid = sand_cells[0]
        msg = {
            "command": "!zw/world.get_cell",
            "payload": {"cell_id": cid},
            "meta": {"request_id": "get_cell"},
        }
        print("cell:", router.handle_zw(msg))
