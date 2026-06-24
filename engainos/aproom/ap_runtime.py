#!/usr/bin/env python3
"""
AP Runtime Integration

Historical runtime bridge location:
  godotengain/engainos/core/ap_runtime.py

Classification:
  GODOT_RUNTIME_BRIDGE

This file is not EngAInOS core authority.
It remains in godotengain until a relay boundary is proven.

It talks to the fenced root ZW AP engine:
  engainos.aproom.ap_zw_engine

Runtime safety rules:
  - simulate_tick is allowed as read/planning behavior
  - execute_tick requires explicit caller intent
  - timeline writing is disabled unless both runtime config and message intent allow it
  - scene loading is anchored to the EngAIn project root, not process cwd
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional


ENGAIN_ROOT = Path(__file__).resolve().parents[3]

if str(ENGAIN_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGAIN_ROOT))


from engainos.aproom.ap_zw_engine import (  # noqa: E402
    APInternalRule,
    StateProvider,
    ZWAPEngine,
)


class APRuntimeIntegration:
    """
    Runtime-facing AP bridge for sim_runtime.py / Godot messages.

    This class does not own EngAInOS authority.
    It is a historical runtime bridge that must later sit behind an EngAInOS relay.
    """

    def __init__(
        self,
        scenes_dir: Optional[str] = None,
        project_root: Optional[str] = None,
        enable_timeline_write: bool = False,
        timeline_root: Optional[str] = None,
    ):
        self.project_root = Path(project_root).resolve() if project_root else ENGAIN_ROOT
        self.scenes_dir = self._resolve_scenes_dir(scenes_dir)
        self.enable_timeline_write = enable_timeline_write
        self.timeline_root = str(Path(timeline_root).resolve()) if timeline_root else None

        self.engine: Optional[ZWAPEngine] = None
        self.state_provider: Optional[StateProvider] = None
        self.loaded_scenes: Dict[str, Any] = {}

    def _resolve_scenes_dir(self, scenes_dir: Optional[str]) -> Path:
        """
        Resolve scenes_dir safely.

        Historical code used bare 'scenes', which depended on process cwd.
        This version anchors relative paths to the EngAIn project root.
        """
        if scenes_dir is None:
            return self.project_root / "scenes"

        path = Path(scenes_dir)

        if not path.is_absolute():
            path = self.project_root / path

        return path.resolve()

    def initialize(
        self,
        initial_state: Optional[Dict[str, Any]] = None,
        rules: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        """
        Initialize AP runtime bridge with state and rules.
        """
        if initial_state is None:
            initial_state = {
                "flags": {},
                "stats": {},
                "locations": {},
                "inventory": {},
                "entropy": {},
                "time_dilation": {},
            }

        self.state_provider = StateProvider(initial_state)

        if rules is None:
            rules = self._load_all_rules()

        self.engine = ZWAPEngine(
            rules,
            self.state_provider,
            enable_timeline_write=self.enable_timeline_write,
            timeline_root=self.timeline_root,
        )

        print(f"[APRuntime] Initialized with {len(rules)} rules")

    def _load_all_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all AP rules from scene files in the configured scenes directory.
        """
        rules: Dict[str, Dict[str, Any]] = {}

        if not self.scenes_dir.exists():
            print(f"[APRuntime] Warning: scenes directory not found: {self.scenes_dir}")
            return rules

        for ext in ["*.zonj", "*.json"]:
            for scene_file in self.scenes_dir.glob(ext):
                if not self._validate_scene_file_path(scene_file):
                    continue
                if scene_file.name == "game_scenes.json":
                    continue

                scene_rules = self._extract_rules_from_zonj(scene_file)
                rules.update(scene_rules)
                print(f"[APRuntime] Loaded {len(scene_rules)} rules from {scene_file.name}")

        game_scenes = self.scenes_dir / "game_scenes.json"
        if game_scenes.exists():
            if not self._validate_scene_file_path(game_scenes):
                return rules
            data = self._load_json_scene_file(game_scenes)

            for scene in data.get("scenes", []):
                if not self._validate_scene_dict(scene):
                    continue
                scene_rules = self._extract_rules_from_scene_dict(scene)
                rules.update(scene_rules)

        return rules

    def _validate_scene_file_path(self, scene_file: Path) -> bool:
        """
        Validate that a candidate scene file is anchored inside self.scenes_dir
        and has a known scene-file suffix before any JSON parse or rule extract.
        """
        try:
            resolved = scene_file.resolve()
            resolved.relative_to(self.scenes_dir)
            scene_file.relative_to(self.scenes_dir)
        except ValueError:
            print(f"[APRuntime] Rejected unanchored scene path: {scene_file}")
            return False

        if resolved.suffix not in {".zonj", ".json"}:
            print(f"[APRuntime] Rejected unsupported scene suffix: {scene_file}")
            return False

        if not resolved.is_file():
            print(f"[APRuntime] Rejected non-file scene path: {scene_file}")
            return False

        return True

    def _load_json_scene_file(self, scene_file: Path) -> Dict[str, Any]:
        """
        Load a JSON scene file only after path validation and root-schema check.
        Invalid files are rejected fail-closed by returning an empty scene dict.
        """
        if not self._validate_scene_file_path(scene_file):
            return {}

        try:
            with open(scene_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            print(f"[APRuntime] Rejected invalid JSON scene file {scene_file}: {exc}")
            return {}

        if not isinstance(data, dict):
            print(f"[APRuntime] Rejected scene file with non-object root: {scene_file}")
            return {}

        if scene_file.name == "game_scenes.json":
            scenes = data.get("scenes", [])
            if not isinstance(scenes, list):
                print(f"[APRuntime] Rejected game_scenes.json with non-list scenes: {scene_file}")
                return {}
            return data

        if not self._validate_scene_dict(data):
            return {}

        return data

    def _validate_scene_dict(self, scene: Any) -> bool:
        """
        Validate the minimum schema used by AP rule extraction.
        """
        if not isinstance(scene, dict):
            return False

        if "id" in scene and not isinstance(scene["id"], str):
            return False

        if "rules" in scene and not isinstance(scene["rules"], dict):
            return False

        if "events" in scene and not isinstance(scene["events"], list):
            return False

        for event in scene.get("events", []):
            if not isinstance(event, dict):
                return False
            if "conditions" in event and not isinstance(event["conditions"], list):
                return False
            if "actions" in event and not isinstance(event["actions"], list):
                return False

        return True

    def _extract_rules_from_zonj(self, zonj_path: Path) -> Dict[str, Dict[str, Any]]:
        zonj_data = self._load_json_scene_file(zonj_path)

        rules: Dict[str, Dict[str, Any]] = {}

        if "rules" in zonj_data:
            rules.update(zonj_data["rules"])

        for event in zonj_data.get("events", []):
            rule = self._event_to_rule(event, zonj_data.get("id", "unknown"))
            if rule:
                rules[rule["id"]] = rule

        return rules

    def _extract_rules_from_scene_dict(self, scene: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        rules: Dict[str, Dict[str, Any]] = {}

        if "rules" in scene:
            rules.update(scene["rules"])

        for event in scene.get("events", []):
            rule = self._event_to_rule(event, scene.get("id", "unknown"))
            if rule:
                rules[rule["id"]] = rule

        return rules

    def _event_to_rule(self, event: Dict[str, Any], scene_id: str) -> Optional[Dict[str, Any]]:
        event_id = event.get("id", f"event_{len(self.loaded_scenes)}")

        requires = []
        for cond in event.get("conditions", []):
            pred = self._condition_to_predicate(cond)
            if pred:
                requires.append(pred)

        effects = []
        for action in event.get("actions", []):
            effect = self._action_to_effect(action)
            if effect:
                effects.append(effect)

        if not requires and not effects:
            return None

        rule = {
            "id": f"{scene_id}_{event_id}",
            "tags": event.get("tags", []),
            "requires": requires,
            "effects": effects,
            "priority": event.get("priority", 0),
            "inputs": event.get("inputs", []),
        }

        self._compute_rule_sets(rule)
        return rule

    def _compute_rule_sets(self, rule: Dict[str, Any]) -> None:
        read_set = set()
        write_set = set()

        re_flag = re.compile(r'flag\((?P<e>[^,]+),\s*["\'](?P<f>[^"\']+)["\']\)')
        re_stat = re.compile(r'stat\((?P<e>[^,]+),\s*["\'](?P<s>[^"\']+)["\']\)')
        re_loc = re.compile(r"location\((?P<e>[^)]+)\)")
        re_inv = re.compile(r'inventory_has\((?P<e>[^,]+),\s*["\'](?P<i>[^"\']+)["\']')
        re_res = re.compile(r'resonance\((?P<e1>[^,]+),\s*(?P<e2>[^,]+),\s*["\'](?P<s>[^"\']+)["\']\)')
        re_har = re.compile(r"vrel_harmony\((?P<e1>[^,]+),\s*(?P<e2>[^,]+)\)")
        re_td = re.compile(r"time_dilation\((?P<e>[^)]+)\)")

        re_set_flag = re.compile(r'set_flag\((?P<e>[^,]+),\s*["\'](?P<f>[^"\']+)["\']')
        re_set_stat = re.compile(r'(?:set|change)_stat\((?P<e>[^,]+),\s*["\'](?P<s>[^"\']+)["\']')
        re_set_loc = re.compile(r"set_location\((?P<e>[^,]+)")
        re_add_inv = re.compile(r'add_inventory\((?P<e>[^,]+),\s*["\'](?P<i>[^"\']+)["\']')
        re_set_td = re.compile(r"set_time_dilation\((?P<e>[^,]+)")

        for pred in rule.get("requires", []) + rule.get("conflicts", []):
            m = re_flag.search(pred)
            if m:
                read_set.add(f"flag.{m.group('e')}.{m.group('f')}")

            m = re_stat.search(pred)
            if m:
                read_set.add(f"stat.{m.group('e')}.{m.group('s')}")

            m = re_loc.search(pred)
            if m:
                read_set.add(f"location.{m.group('e')}")

            m = re_inv.search(pred)
            if m:
                read_set.add(f"inventory.{m.group('e')}.{m.group('i')}")

            m = re_res.search(pred)
            if m:
                read_set.add(f"stat.{m.group('e1')}.{m.group('s')}")
                read_set.add(f"stat.{m.group('e2')}.{m.group('s')}")

            m = re_har.search(pred)
            if m:
                read_set.add(f"stat.{m.group('e1')}.vrel")
                read_set.add(f"stat.{m.group('e2')}.vrel")

            m = re_td.search(pred)
            if m:
                read_set.add(f"time_dilation.{m.group('e')}")

        for effect in rule.get("effects", []):
            m = re_set_flag.search(effect)
            if m:
                write_set.add(f"flag.{m.group('e')}.{m.group('f')}")

            m = re_set_stat.search(effect)
            if m:
                write_set.add(f"stat.{m.group('e')}.{m.group('s')}")

            m = re_set_loc.search(effect)
            if m:
                write_set.add(f"location.{m.group('e')}")

            m = re_add_inv.search(effect)
            if m:
                write_set.add(f"inventory.{m.group('e')}.{m.group('i')}")

            m = re_set_td.search(effect)
            if m:
                write_set.add(f"time_dilation.{m.group('e')}")

        rule["read_set"] = sorted(read_set)
        rule["write_set"] = sorted(write_set)

    def _condition_to_predicate(self, cond: Dict[str, Any]) -> Optional[str]:
        cond_type = cond.get("type")

        if cond_type == "flag":
            entity = cond.get("entity", "player")
            flag = cond.get("flag", "")
            value = cond.get("value", True)
            op = cond.get("op", "==")

            if op == "==" and value is True:
                return f'flag({entity}, "{flag}")'

            return None

        if cond_type == "stat":
            entity = cond.get("entity", "player")
            stat = cond.get("stat", "")
            op = cond.get("op", ">=")
            value = cond.get("value", 0)
            return f'stat({entity}, "{stat}") {op} {value}'

        if cond_type == "location":
            entity = cond.get("entity", "player")
            location = cond.get("location", "")
            return f'location({entity}) == "{location}"'

        if cond_type == "inventory":
            entity = cond.get("entity", "player")
            item = cond.get("item", "")
            count = cond.get("count", 1)
            return f'inventory_has({entity}, "{item}", {count})'

        if cond_type == "time_dilation":
            entity = cond.get("entity", "player")
            op = cond.get("op", ">=")
            value = cond.get("value", 1.0)
            return f"time_dilation({entity}) {op} {value}"

        return None

    def _action_to_effect(self, action: Dict[str, Any]) -> Optional[str]:
        action_type = action.get("type")

        if action_type == "set_flag":
            entity = action.get("entity", "player")
            flag = action.get("flag", "")
            value = str(action.get("value", True)).lower()
            return f'set_flag({entity}, "{flag}", {value})'

        if action_type == "change_stat":
            entity = action.get("entity", "player")
            stat = action.get("stat", "")
            delta = action.get("delta", 0)
            return f'change_stat({entity}, "{stat}", {delta})'

        if action_type == "set_location":
            entity = action.get("entity", "player")
            location = action.get("location", "")
            return f'set_location({entity}, "{location}")'

        if action_type == "add_inventory":
            entity = action.get("entity", "player")
            item = action.get("item", "")
            count = action.get("count", 1)
            return f'add_inventory({entity}, "{item}", {count})'

        if action_type == "set_time_dilation":
            entity = action.get("entity", "player")
            value = action.get("value", 1.0)
            return f"set_time_dilation({entity}, {value})"

        return None

    def update_state(self, state_delta: Dict[str, Any]) -> None:
        if not self.state_provider:
            return

        for entity, flags in state_delta.get("flags", {}).items():
            for flag, value in flags.items():
                self.state_provider.set_flag(entity, flag, value)

        for entity, stats in state_delta.get("stats", {}).items():
            for stat, value in stats.items():
                self.state_provider.set_stat(entity, stat, value)

        for entity, location in state_delta.get("locations", {}).items():
            self.state_provider.set_location(entity, location)

        for entity, inventory in state_delta.get("inventory", {}).items():
            for item, count in inventory.items():
                current = self.state_provider.get_inventory_count(entity, item)
                if count != current:
                    self.state_provider.add_inventory(entity, item, count - current)

        for entity, value in state_delta.get("time_dilation", {}).items():
            self.state_provider.set_time_dilation(entity, value)

    def handle_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        msg_type = msg.get("type")

        if msg_type == "ap_evaluate_rule":
            return self._handle_evaluate_rule(msg)

        if msg_type == "ap_simulate_tick":
            return self._handle_simulate_tick(msg)

        if msg_type == "ap_execute_tick":
            return self._handle_execute_tick(msg)

        if msg_type == "ap_execution_history":
            return self._handle_execution_history(msg)

        if msg_type == "ap_list_rules":
            return self._handle_list_rules(msg)

        if msg_type == "ap_get_rule":
            return self._handle_get_rule(msg)

        return {"error": "unknown_ap_message_type", "type": msg_type}

    def _handle_evaluate_rule(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        if not self.engine:
            return {"error": "ap_not_initialized"}

        rule_id = msg.get("rule_id")
        context = msg.get("context", {})

        if not rule_id:
            return {"error": "missing_rule_id"}

        return self.engine.evaluate_rule_explain(rule_id, context)

    def _handle_simulate_tick(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        if not self.engine:
            return {"error": "ap_not_initialized"}

        context = msg.get("context", {})
        result = self.engine.simulate_tick(context)

        return {
            "type": "ap_simulate_result",
            "result": result,
        }

    def _handle_execute_tick(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        if not self.engine:
            return {"error": "ap_not_initialized"}

        if msg.get("allow_execute") is not True:
            return {
                "error": "execution_intent_required",
                "message": "ap_execute_tick requires allow_execute: true",
            }

        requested_timeline_write = msg.get("enable_timeline_write") is True

        if requested_timeline_write and not self.enable_timeline_write:
            return {
                "error": "timeline_write_not_allowed",
                "message": "Runtime was not initialized with enable_timeline_write=True",
            }

        old_write_flag = self.engine.enable_timeline_write

        try:
            self.engine.enable_timeline_write = bool(
                self.enable_timeline_write and requested_timeline_write
            )
            context = msg.get("context", {})
            return self.engine.execute_tick(context)
        finally:
            self.engine.enable_timeline_write = old_write_flag

    def _handle_execution_history(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        if not self.engine:
            return {"error": "ap_not_initialized"}

        if msg.get("allow_history_read") is not True:
            return {
                "error": "history_read_intent_required",
                "message": "ap_execution_history requires allow_history_read: true",
            }

        limit = msg.get("limit", 20)
        entries = self.engine.read_execution_history(limit)

        return {
            "type": "ap_execution_history",
            "entries": entries,
        }

    def _handle_list_rules(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        if not self.engine:
            return {"error": "ap_not_initialized"}

        return {
            "type": "ap_rules_list",
            "rules": self.engine.list_rules(),
        }

    def _handle_get_rule(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        if not self.engine:
            return {"error": "ap_not_initialized"}

        rule_id = msg.get("rule_id")
        if not rule_id:
            return {"error": "missing_rule_id"}

        return {
            "type": "ap_rule_details",
            "rule": self.engine.get_rule(rule_id),
        }


if __name__ == "__main__":
    raise SystemExit(
        "APRuntimeIntegration is a historical bridge, not a standalone entrypoint. "
        "AP_RUNTIME_BLOCKER_LANE blocks direct execution until the HTTP/Godot "
        "bridge proves EngAInOS authority compliance."
    )
