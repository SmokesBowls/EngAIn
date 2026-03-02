#!/usr/bin/env python3
"""scene_manager.py - Scene loading, extraction, and activation for EngAIn Runtime.

Owns: scene registry, entity extraction, interactive entity commands.
Reads/writes: runtime.snapshot (for scene activation)
Used by: command_dispatcher.py, http_handlers.py
"""

from typing import Dict, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from runtime_core import EngAInRuntime

# ── SceneExtractor (optional interactive entity system) ──────────
try:
    from scene_extractor import SceneExtractor
    _scene_extractor = SceneExtractor()
    print("[BOOT] SceneExtractor loaded (via SceneManager)")
except ImportError:
    _scene_extractor = None
    print("[BOOT] SceneExtractor not found — interactive entity commands disabled")

# ── Semantic Bridge (optional visual placeholder system) ─────────
try:
    from bridge_integration import bridge_entities_for_scene
    _HAS_BRIDGE = True
    print("[BOOT] SemanticBridge loaded (via SceneManager)")
except ImportError:
    _HAS_BRIDGE = False
    print("[BOOT] SemanticBridge not found — placeholder visuals disabled")


class SceneManager:
    """
    Manages scene loading, entity extraction, and interactive commands.
    
    Owns:
        - self.scenes: scene registry {scene_id -> {raw, norm}}
        - self.entity_cards: extracted entity cards from SceneExtractor
    
    Writes to:
        - runtime.snapshot["scene"], ["scene_raw"], ["scene_id"], ["entities"]
    """

    def __init__(self, runtime: 'EngAInRuntime'):
        self.runtime = runtime
        self.scenes: Dict[str, Dict[str, Any]] = {}
        self.entity_cards: Dict[str, Any] = {}

    # ── Scene Loading ────────────────────────────────────────────

    def load_scene(self, scene_doc: Dict[str, Any], activate: bool = False) -> str:
        """
        Parse scene data and store in registry.
        Returns status: "accepted_new" | "overwritten"
        """
        scene_id = scene_doc.get("@id") or scene_doc.get("scene_id") or "unknown"

        # Build normalized view
        norm = {
            "scene_id": scene_id,
            "where": scene_doc.get("@where") or scene_doc.get("where"),
            "when": scene_doc.get("@when") or scene_doc.get("when"),
            "entities": scene_doc.get("@entities") or scene_doc.get("entities", []),
            "segments": scene_doc.get("=segments") or scene_doc.get("segments", []),
        }

        if isinstance(norm["entities"], dict):
            norm["entities"] = list(norm["entities"].values())
        if norm["entities"] is None:
            norm["entities"] = []
        if norm["segments"] is None:
            norm["segments"] = []

        status = "overwritten" if scene_id in self.scenes else "accepted_new"

        self.scenes[scene_id] = {"raw": scene_doc, "norm": norm}

        if activate:
            self.select_active_scene(scene_id)

        return status

    def select_active_scene(self, scene_id: str) -> bool:
        """Activates a scene from the registry into the runtime snapshot."""
        if scene_id not in self.scenes:
            return False

        info = self.scenes[scene_id]
        self.runtime.snapshot["scene_raw"] = info["raw"]
        self.runtime.snapshot["scene"] = info["norm"]
        self.runtime.snapshot["scene_id"] = scene_id

        # Sync entities into snapshot
        entities_dict = {}
        for ent in info["norm"]["entities"]:
            if isinstance(ent, dict):
                eid = ent.get("@id") or ent.get("id") or str(ent.get("name"))
                if eid:
                    entities_dict[eid] = ent

        if entities_dict:
            self.runtime.snapshot["entities"] = entities_dict

        # Extract interactive entities
        self._extract_entities_for_scene()

        # Resolve entities through semantic bridge for Godot rendering
        self._bridge_entities_for_scene()

        return True

    def _extract_entities_for_scene(self):
        """Run SceneExtractor on the active scene, populate entity_cards."""
        if _scene_extractor is None:
            return
        if not self.runtime.snapshot.get("scene"):
            return
        scene_doc = self.runtime.snapshot["scene"]
        try:
            self.entity_cards = _scene_extractor.extract(scene_doc)
            names = [c.name for c in self.entity_cards.values()]
            print(f"[EXTRACT] {len(self.entity_cards)} entities: {names}")
        except Exception as e:
            print(f"[EXTRACT] Error: {e}")
            self.entity_cards = {}

    def _bridge_entities_for_scene(self):
        """Run semantic bridge on active scene → snapshot['bridge_entities'] for Godot."""
        if not _HAS_BRIDGE:
            return
        scene_doc = self.runtime.snapshot.get("scene")
        if not scene_doc:
            return
        try:
            bridge_data = bridge_entities_for_scene(scene_doc, self.entity_cards)
            self.runtime.snapshot["bridge_entities"] = bridge_data
        except Exception as e:
            print(f"[BRIDGE] Error: {e}")
            self.runtime.snapshot["bridge_entities"] = []

    # ── Text Command Handler (for dispatcher delegation) ─────────

    def handle_text_command(self, text: str) -> Dict[str, Any]:
        """Process natural-language commands: look, examine, status, segments."""
        scene = self.runtime.snapshot.get("scene")

        if text in ("look", "l"):
            if not scene:
                return {"type": "result", "command": text, "text": "You see nothing. No scene is loaded."}

            sid = scene.get("scene_id", "unknown")
            where = scene.get("where") or "an unknown place"
            when_val = scene.get("when") or "an unknown time"
            entities = scene.get("entities", [])
            segments = scene.get("segments", [])

            desc_lines = []
            for seg in segments[:5]:
                if isinstance(seg, dict):
                    line = seg.get("text") or seg.get("narration") or seg.get("dialogue") or ""
                    if isinstance(line, str) and line.strip():
                        desc_lines.append(line.strip())
                elif isinstance(seg, str) and seg.strip():
                    desc_lines.append(seg.strip())

            description = " ".join(desc_lines) if desc_lines else "The scene stretches before you."

            entity_names = []
            for e in entities[:10]:
                if isinstance(e, dict):
                    name = e.get("name") or e.get("@id") or e.get("id") or "?"
                    entity_names.append(str(name))
                elif isinstance(e, str):
                    entity_names.append(e)

            return {
                "type": "result", "command": text,
                "scene_id": sid, "where": where, "when": when_val,
                "text": description,
                "entities_present": entity_names,
                "total_segments": len(segments),
            }

        elif text.startswith("examine ") or text.startswith("x "):
            target = text.split(" ", 1)[1].strip()
            if not scene:
                return {"type": "result", "command": text, "text": "Nothing to examine. No scene loaded."}

            entities = scene.get("entities", [])
            for e in entities:
                if isinstance(e, dict):
                    eid = str(e.get("name") or e.get("@id") or e.get("id") or "")
                    if target.lower() in eid.lower():
                        return {"type": "result", "command": text, "text": f"You examine {eid}.", "entity": e}

            return {"type": "result", "command": text, "text": f"You don't see '{target}' here."}

        elif text in ("status", "stat"):
            entity_count = len(self.runtime.snapshot.get("entities", {}))
            world = self.runtime.snapshot.get("world", {})
            scene_id = (scene.get("scene_id") or scene.get("@id") or "none") if scene else "none"
            return {
                "type": "result", "command": text,
                "scene_id": scene_id,
                "entities_active": entity_count,
                "world_time": world.get("time", 0.0),
                "weather": world.get("weather", "unknown"),
            }

        elif text in ("segments", "seg"):
            if not scene:
                return {"type": "result", "command": text, "text": "No scene loaded."}
            segs = scene.get("segments", [])
            return {"type": "result", "command": text, "total": len(segs), "preview": [str(s)[:120] for s in segs[:10]]}

        else:
            return {
                "type": "result", "command": text,
                "text": f"Unknown command: '{text}'",
                "hint": "Try: look, examine <entity>, status, segments, entities, talk to <entity>",
            }

    # ── Interactive Entity Commands ──────────────────────────────

    def handle_entities(self, args: List[str]) -> Dict[str, Any]:
        """List all interactive entities in the current scene."""
        if not self.entity_cards:
            return {"text": "No entities extracted for this scene. Load a scene first.", "entities": []}

        lines = []
        entities_list = []
        for key, card in sorted(self.entity_cards.items(), key=lambda x: -x[1].extracted["mention_count"]):
            c = card.to_dict()
            mood_str = c["mood"]
            type_str = c["type"] or "?"
            role_str = c["role"] or "?"
            marker = " *" if c["has_override"] else ""
            lines.append(f"  [{c['name']}] {type_str}/{role_str} — mood: {mood_str}{marker}")
            entities_list.append(c)

        header = f"=== Entities in scene ({len(self.entity_cards)}) ==="
        footer = "\n  (* = has override)"
        return {"text": header + "\n" + "\n".join(lines) + footer, "entities": entities_list}

    def handle_examine(self, args: List[str]) -> Dict[str, Any]:
        """Examine an entity: show description, type, mood, knowledge."""
        if not args:
            return {"text": "Examine what? Try: examine <name>"}
        target = " ".join(args).lower().strip()

        if not self.entity_cards:
            return {"text": "No entities in this scene."}

        card = self._find_entity(target)
        if not card:
            return {"text": f"You don't see '{target}' here."}

        c = card.to_dict()
        desc = card.get_description()
        knowledge = ", ".join(c["knowledge"]) if c["knowledge"] else "unknown"

        lines = [
            f"=== {c['name']} ===",
            f"  Type: {c['type'] or 'unknown'}",
            f"  Role: {c['role'] or 'unknown'}",
            f"  Mood: {c['mood']}",
            f"  Knowledge: {knowledge}",
            f"  Mentions: {c['mention_count']}",
            "",
            f"  {desc}",
        ]

        if c["has_override"]:
            lines.append("\n  [has designer override]")

        return {"text": "\n".join(lines), "entity": c, "description": desc}

    def handle_talk(self, args: List[str]) -> Dict[str, Any]:
        """Talk to an entity: show dialogue (override first, then extracted)."""
        if not args:
            return {"text": "Talk to whom? Try: talk to <name>"}

        if args[0].lower() == "to" and len(args) > 1:
            args = args[1:]
        target = " ".join(args).lower().strip()

        if not self.entity_cards:
            return {"text": "No entities in this scene."}

        card = self._find_entity(target)
        if not card:
            return {"text": f"You don't see '{target}' here."}

        dialogue = card.get_dialogue()
        mood = card.get_mood()

        if not dialogue:
            return {
                "text": f"{card.name} is here, but has no dialogue yet.\n"
                        f"  Mood: {mood}\n"
                        f"  Knowledge: {', '.join(card.extracted['knowledge']) or 'unknown'}\n"
                        f"  [dialogue slot — ready for authoring]",
                "entity": card.to_dict(),
                "dialogue": [],
                "has_slot": True,
            }

        lines = [f"=== {card.name} ({mood}) ===", ""]
        for d in dialogue:
            source = d.get("source", "extracted")
            marker = "[override] " if source == "override" else ""
            lines.append(f'  {marker}"{d["line"]}"')

        return {"text": "\n".join(lines), "entity": card.to_dict(), "dialogue": dialogue}

    def handle_mood(self, args: List[str]) -> Dict[str, Any]:
        """Show or describe an entity's mood."""
        if not args:
            return {"text": "Whose mood? Try: mood <name>"}
        target = " ".join(args).lower().strip()

        if not self.entity_cards:
            return {"text": "No entities in this scene."}

        card = self._find_entity(target)
        if not card:
            return {"text": f"You don't see '{target}' here."}

        mood = card.get_mood()
        all_moods = card.extracted["moods"]
        override_mood = card.override.get("mood")

        lines = [f"=== {card.name} — Mood ==="]
        lines.append(f"  Current: {mood}")
        if override_mood:
            lines.append("  (set by override)")
        if all_moods:
            lines.append(f"  Detected across text: {', '.join(set(all_moods))}")

        return {"text": "\n".join(lines), "mood": mood}

    def handle_override(self, args: List[str]) -> Dict[str, Any]:
        """Set an override on an entity. Usage: override <name> <field> <value>"""
        if len(args) < 3:
            return {
                "text": "Usage: override <name> <field> <value>\n"
                        "  Fields: type, role, mood, description\n"
                        "  Example: override torhh mood protective"
            }

        target = args[0].lower()
        field = args[1].lower()
        value = " ".join(args[2:])

        if not self.entity_cards:
            return {"text": "No entities in this scene."}

        card = self._find_entity(target)
        if not card:
            return {"text": f"Entity '{target}' not found."}

        if field not in ("type", "role", "mood", "description"):
            return {"text": f"Unknown field '{field}'. Use: type, role, mood, description"}

        card.override[field] = value

        # Save to disk
        scene_id = (
            self.runtime.snapshot.get("scene", {}).get("@id")
            or self.runtime.snapshot.get("scene", {}).get("scene_id", "unknown")
        )
        if _scene_extractor:
            _scene_extractor.save_overrides(scene_id, self.entity_cards)

        return {"text": f"Override set: {card.name}.{field} = {value}\n  (saved to disk)", "entity": card.to_dict()}

    # ── Entity Finder ────────────────────────────────────────────

    def _find_entity(self, target: str):
        """Fuzzy-find entity by name (case-insensitive, partial match)."""
        if not self.entity_cards:
            return None
        if target in self.entity_cards:
            return self.entity_cards[target]
        for key, card in self.entity_cards.items():
            if target in key or key in target:
                return card
        return None
