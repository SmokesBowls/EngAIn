#!/usr/bin/env python3
"""command_dispatcher.py - Command routing logic for EngAIn Runtime.

Routes incoming commands (HTTP, CLI, internal) to the appropriate handler.
Depends on: runtime_core.EngAInRuntime (for adapter calls), scene_manager.SceneManager (for entity commands)
"""

from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from runtime_core import EngAInRuntime
    from scene_manager import SceneManager


class CommandDispatcher:
    """
    Routes commands to the appropriate handler.

    Separation of concerns:
        - Scene/entity commands -> SceneManager
        - Adapter calls (combat, inventory, dialogue) -> Runtime subsystems
        - Simulation mutations -> Runtime command queue
        - Text fallback -> SceneManager.handle_text_command
    """

    def __init__(self, runtime: 'EngAInRuntime', scene_manager: 'SceneManager'):
        self.runtime = runtime
        self.scene_manager = scene_manager

    def dispatch(self, raw_input: Any) -> Dict[str, Any]:
        """Normalize and route commands from HTTP or internal sources."""
        print(f"\n[DISPATCH] Input type: {type(raw_input)}")

        if isinstance(raw_input, str):
            print(f"[DISPATCH] String command: '{raw_input}'")
            return self.scene_manager.handle_text_command(raw_input)

        if not isinstance(raw_input, dict):
            return {"type": "error", "message": f"Invalid request format: {type(raw_input)}"}

        # Normalize command/action keys
        command = (raw_input.get("command") or raw_input.get("action") or "").strip().lower()
        text = (raw_input.get("text") or "").strip().lower()

        # Effective command string: explicit command > text, but skip generic "command"/"action"
        if command in ("command", "action", ""):
            cmd_str = text or command
        else:
            cmd_str = command

        print(f"[DISPATCH] Normalized command string: '{cmd_str}' (from cmd='{command}', text='{text}')")

        base_cmd = cmd_str.split(" ", 1)[0] if cmd_str else ""

        # ── 1. Interactive Entity Commands (-> SceneManager) ─────

        if base_cmd in ("entities", "examine", "talk", "mood", "override"):
            args = cmd_str.split(" ")[1:] if " " in cmd_str else []
            handler_map = {
                "entities": self.scene_manager.handle_entities,
                "examine": self.scene_manager.handle_examine,
                "talk": self.scene_manager.handle_talk,
                "mood": self.scene_manager.handle_mood,
                "override": self.scene_manager.handle_override,
            }
            return handler_map[base_cmd](args)

        # ── 2. Text Commands (-> SceneManager) ──────────────────

        if base_cmd in ("look", "l", "status", "stat", "segments", "seg"):
            return self.scene_manager.handle_text_command(cmd_str)

        # ── 3. Direct Adapter Calls (Immediate) ─────────────────

        if cmd_str in ("damage", "combat/damage"):
            if not self.runtime.combat:
                return {"type": "error", "status": "combat_not_loaded"}
            self.runtime.combat.handle_delta(
                "combat3d/apply_damage",
                {
                    "source": raw_input.get("source", "unknown"),
                    "target": raw_input.get("target"),
                    "amount": raw_input.get("damage", 25),
                },
            )
            return {"type": "ack", "status": "damage_applied"}

        if cmd_str in ("take", "inventory/take"):
            if not self.runtime.inventory:
                return {"type": "error", "status": "inventory_not_loaded"}
            self.runtime.inventory.handle_delta(
                "inventory3d/take",
                {"actor": raw_input.get("actor"), "item": raw_input.get("item")},
            )
            return {"type": "ack", "status": "take_queued"}

        if cmd_str in ("drop", "inventory/drop"):
            if not self.runtime.inventory:
                return {"type": "error", "status": "inventory_not_loaded"}
            self.runtime.inventory.handle_delta(
                "inventory3d/drop",
                {
                    "actor": raw_input.get("actor"),
                    "item": raw_input.get("item"),
                    "location": raw_input.get("location", "world"),
                },
            )
            return {"type": "ack", "status": "drop_queued"}

        if cmd_str in ("wear", "inventory/wear"):
            if not self.runtime.inventory:
                return {"type": "error", "status": "inventory_not_loaded"}
            self.runtime.inventory.handle_delta(
                "inventory3d/wear",
                {"actor": raw_input.get("actor"), "item": raw_input.get("item")},
            )
            return {"type": "ack", "status": "wear_queued"}

        if cmd_str in ("ask", "dialogue/ask"):
            if not self.runtime.dialogue:
                return {"type": "error", "status": "dialogue_not_loaded"}
            self.runtime.dialogue.handle_delta("dialogue3d/ask", raw_input)
            return {"type": "ack", "status": "ask_queued"}

        # ── 4. Simulation Mutations (Queued) ─────────────────────

        if cmd_str in ("spawn_entity", "update_entity", "interact", "reload_blocks", "dump_state", "move_entity", "edit_dialogue", "load_scene_from_file", "select_scene"):

            self.runtime.add_command(raw_input)
            return {"type": "ack", "status": "queued", "command": cmd_str}

        # ── 5. Text Pipeline Fallback ────────────────────────────

        if cmd_str:
            print(f"[DISPATCH] Routing '{cmd_str}' to scene manager text pipeline (fallback)")
            return self.scene_manager.handle_text_command(cmd_str)

        return {"type": "error", "message": f"Unknown command: {cmd_str}"}
