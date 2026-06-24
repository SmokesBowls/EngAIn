#!/usr/bin/env python3
"""scene_manager.py - Scene loading, extraction, and activation for EngAIn Runtime.

Owns: scene registry, entity extraction, interactive entity commands.
Reads/writes: runtime.snapshot (for scene activation)
Used by: command_dispatcher.py, http_handlers.py
"""

from typing import Dict, Any, List, TYPE_CHECKING
import os
import sys

if TYPE_CHECKING:
    from runtime_core import EngAInRuntime

# ── Scene identity canonicalizer ─────────────────────────────────
try:
    _ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _ROOT_DIR not in sys.path:
        sys.path.insert(0, _ROOT_DIR)
    from tier3.mettaext.scene_identity import canonical_scene_id, scene_id_aliases
except Exception:
    def canonical_scene_id(raw):
        return str(raw or "unknown")

    def scene_id_aliases(raw):
        v = str(raw or "unknown")
        return {v}

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
        self.scene_alias_to_canonical: Dict[str, str] = {}
        self.entity_cards: Dict[str, Any] = {}

    # ── Scene Loading ────────────────────────────────────────────

    def load_scene(self, scene_doc: Dict[str, Any], activate: bool = False, override_id: str = None) -> str:
        """
        Parse scene data and store in registry.
        Returns status: "accepted_new" | "overwritten"
        """
        raw_scene_id = override_id or scene_doc.get("@id") or scene_doc.get("scene_id") or "unknown"
        scene_id = canonical_scene_id(raw_scene_id)
        source_path = scene_doc.get("source_path")
        file_meta = scene_doc.get("file")
        if not isinstance(file_meta, dict):
            file_meta = {}
        source_path = source_path or file_meta.get("source_path")
        in_entities = scene_doc.get("@entities") or scene_doc.get("entities", [])
        in_segments = scene_doc.get("=segments") or scene_doc.get("segments", [])
        print(
            f"[TRACE_SCENE030][SCENE_MANAGER_LOAD_ENTER] raw_scene_id={raw_scene_id} canonical={scene_id} "
            f"override_id={override_id} activate={activate} source_path={source_path} "
            f"input_entities={len(in_entities) if isinstance(in_entities, (list, dict)) else 0} "
            f"input_segments={len(in_segments) if isinstance(in_segments, (list, dict)) else 0}"
        )

        # Build normalized view
        norm = {
            "scene_id": scene_id,
            "where": scene_doc.get("@where") or scene_doc.get("where"),
            "when": scene_doc.get("@when") or scene_doc.get("when"),
            "environment": scene_doc.get("environment", {}),
            "exits": scene_doc.get("exits", []),
            "entities": scene_doc.get("@entities") or scene_doc.get("entities", []),
            "segments": scene_doc.get("=segments") or scene_doc.get("segments", []),
            # semantic compiler pass-through (must survive /scene/load -> /snapshot)
            "spatial_hints": scene_doc.get("spatial_hints", []),
            "zon_blocks": scene_doc.get("zon_blocks", []),
            "compiler_report": scene_doc.get("compiler_report", {}),
            "validation": scene_doc.get("validation", {}),
        }

        if isinstance(norm["entities"], dict):
            norm["entities"] = list(norm["entities"].values())
        
        # Ensure lists are lists
        for key in ["entities", "segments", "exits", "spatial_hints", "zon_blocks"]:
            if norm[key] is None:
                norm[key] = []

        if norm["compiler_report"] is None:
            norm["compiler_report"] = {}
        if norm["validation"] is None:
            norm["validation"] = {}
        
        if not isinstance(norm["environment"], dict):
            norm["environment"] = {}

        status = "overwritten" if scene_id in self.scenes else "accepted_new"

        self.scenes[scene_id] = {"raw": scene_doc, "norm": norm}
        print(
            f"[TRACE_SCENE030][SCENE_MANAGER_REGISTERED] scene_id={scene_id} status={status} "
            f"norm_entities={len(norm['entities']) if isinstance(norm.get('entities'), list) else 0} "
            f"norm_segments={len(norm['segments']) if isinstance(norm.get('segments'), list) else 0}"
        )
        for alias in scene_id_aliases(raw_scene_id):
            self.scene_alias_to_canonical[alias] = scene_id
        # Ensure canonical self-alias always exists.
        self.scene_alias_to_canonical[scene_id] = scene_id

        if activate:
            self.select_active_scene(scene_id)

        return status

    def select_active_scene(self, scene_id: str) -> bool:
        """Activates a scene from the registry into the runtime snapshot."""
        canonical_id = self.scene_alias_to_canonical.get(scene_id) or canonical_scene_id(scene_id)
        print(f"[TRACE_SCENE030][SELECT_ACTIVE_ENTER] requested={scene_id} canonical={canonical_id} registered={canonical_id in self.scenes}")
        if canonical_id not in self.scenes:
            print(f"[TRACE_SCENE030][SELECT_ACTIVE_RETURN_FALSE] requested={scene_id} canonical={canonical_id} reason=not_registered")
            return False

        info = self.scenes[canonical_id]
        self.runtime.snapshot["scene_raw"] = info["raw"]
        self.runtime.snapshot["scene"] = info["norm"]
        self.runtime.snapshot["scene_id"] = canonical_id
        # Preserve semantic compiler outputs as first-class snapshot fields.
        self.runtime.snapshot["spatial_hints"] = info["norm"].get("spatial_hints", [])
        self.runtime.snapshot["zon_blocks"] = info["norm"].get("zon_blocks", [])
        self.runtime.snapshot["compiler_report"] = info["norm"].get("compiler_report", {})
        self.runtime.snapshot["validation"] = info["norm"].get("validation", {})

        # ── Flush kernels and reset state ────────────────────────
        # This prevents characters/states from previous scenes from leaking
        self.runtime.snapshot["entities"] = {}
        self.runtime.snapshot["spatial"] = {}
        self.runtime.snapshot["perception"] = {}
        self.runtime.snapshot["behavior"] = {}
        self.runtime.snapshot["events"] = []

        # Sync entities into snapshot
        entities_dict = {}
        for ent in info["norm"]["entities"]:
            if isinstance(ent, dict):
                eid = ent.get("@id") or ent.get("id") or ent.get("entity_id") or str(ent.get("name"))
                if eid:
                    entities_dict[eid] = ent
                    # Ensure position exists in the sim state
                    if "pos" not in ent and "position" in ent:
                        ent["pos"] = ent["position"]
                    elif "pos" not in ent and "spawn_pos" in ent:
                        ent["pos"] = ent["spawn_pos"]
                    elif "pos" not in ent:
                        ent["pos"] = [0.0, 0.0, 0.0]

        # Extract interactive entities (updates self.entity_cards)
        self._extract_entities_for_scene()

        # Merge extracted entities into simulation snapshot
        # This ensuring narrative-discovered characters are also simulated
        for key, card in self.entity_cards.items():
            if key not in entities_dict:
                if (
                    card.extracted["mention_count"] >= 5
                    or card.extracted["dialogue"]
                    or card.extracted["type"]
                    or card.extracted["role"]
                ):
                    entities_dict[key] = {
                        "entity_id": key,
                        "name": card.name,
                        "archetype": card.get("type"),
                        "role": card.get("role"),
                        "pos": [0.0, 0.0, 0.0],
                        "presence": "visible",
                        "importance": 50,
                        "dialogue": {
                            "dialogue_id": f"{key}_extracted",
                            "nodes": [{"id": "start", "text": card.get_description()}]
                        }
                    }

        self.runtime.snapshot["entities"] = entities_dict

        # Resolve entities through semantic bridge for Godot rendering
        self._bridge_entities_for_scene()
        bridge_entities = self.runtime.snapshot.get("bridge_entities") or []
        print(
            f"[TRACE_SCENE030][BRIDGE_READY] scene_id={canonical_id} "
            f"snapshot_scene_id={self.runtime.snapshot.get('scene_id')} "
            f"bridge_entities_scene_id={self.runtime.snapshot.get('bridge_entities_scene_id')} "
            f"bridge_entities={len(bridge_entities) if isinstance(bridge_entities, (list, dict)) else 0}"
        )

        print(f"[SCENE] Activated '{canonical_id}' with {len(entities_dict)} total entities (including {len(self.entity_cards)} extracted).")
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
        """Run semantic bridge on active scene → snapshot[bridge_entities] for Godot.
        Also seed runtime entity positions from bridge transforms so runtime_core
        does not flatten everything back to origin.
        """
        if not _HAS_BRIDGE:
            return
        scene_doc = self.runtime.snapshot.get("scene")
        if not scene_doc:
            return
        try:
            def _entity_values(value):
                if isinstance(value, dict):
                    return list(value.values())
                if isinstance(value, list):
                    return value
                return []

            def _entity_names(value):
                names = []
                for entity in _entity_values(value):
                    if isinstance(entity, dict):
                        name = (
                            entity.get("name")
                            or entity.get("@name")
                            or entity.get("entity_id")
                            or entity.get("@id")
                            or entity.get("id")
                        )
                        if name:
                            names.append(str(name))
                    elif isinstance(entity, str):
                        names.append(entity)
                return names

            def _entity_id_from(key, entity):
                if isinstance(entity, dict):
                    return str(
                        entity.get("entity_id")
                        or entity.get("@id")
                        or entity.get("id")
                        or entity.get("name")
                        or key
                        or ""
                    )
                return str(key or "")

            def _has_position(value):
                return isinstance(value, dict) or (isinstance(value, (list, tuple)) and len(value) >= 3)

            def _is_origin_position(value):
                if isinstance(value, dict):
                    return (
                        float(value.get("x", 0.0)) == 0.0
                        and float(value.get("y", 0.0)) == 0.0
                        and float(value.get("z", 0.0)) == 0.0
                    )
                if isinstance(value, (list, tuple)) and len(value) >= 3:
                    return float(value[0]) == 0.0 and float(value[1]) == 0.0 and float(value[2]) == 0.0
                return False

            def _bridge_entity_from_snapshot(key, entity, spatial_entities):
                if not isinstance(entity, dict):
                    return entity

                bridge_entity = dict(entity)
                eid = _entity_id_from(key, entity)
                spatial_entry = spatial_entities.get(eid) if isinstance(spatial_entities, dict) else None
                spatial_pos = spatial_entry.get("pos") if isinstance(spatial_entry, dict) else None

                if _has_position(spatial_pos):
                    bridge_entity["pos"] = spatial_pos
                    bridge_entity["placement_source"] = "spatial3d"
                elif _has_position(entity.get("spawn_pos")):
                    bridge_entity["pos"] = entity.get("spawn_pos")
                    bridge_entity["placement_source"] = "spawn_pos"
                elif _has_position(entity.get("position")):
                    bridge_entity["pos"] = entity.get("position")
                    bridge_entity["placement_source"] = "authored_pos"
                elif _has_position(entity.get("pos")) and not _is_origin_position(entity.get("pos")):
                    bridge_entity["placement_source"] = "authored_pos"
                else:
                    bridge_entity["pos"] = None
                    bridge_entity["placement_source"] = "unplaced"

                return bridge_entity

            scene_id = self.runtime.snapshot.get("scene_id") or scene_doc.get("scene_id") or scene_doc.get("@id") or "unknown"
            scene_doc_entities = scene_doc.get("entities") or scene_doc.get("@entities") or []
            entities_dict = self.runtime.snapshot.get("entities", {})
            spatial = self.runtime.snapshot.get("spatial", {})
            spatial_entities = spatial.get("entities", {}) if isinstance(spatial, dict) else {}

            bridge_scene_doc = dict(scene_doc)
            if isinstance(entities_dict, dict) and entities_dict:
                bridge_scene_doc["entities"] = [
                    _bridge_entity_from_snapshot(key, entity, spatial_entities)
                    for key, entity in entities_dict.items()
                ]

            bridge_input_entities = bridge_scene_doc.get("entities") or bridge_scene_doc.get("@entities") or []

            print(f"[BRIDGE_ENTITY_AUDIT] scene_id={scene_id}")
            print(f"[BRIDGE_ENTITY_AUDIT] scene_doc.entities count={len(_entity_values(scene_doc_entities))} names={_entity_names(scene_doc_entities)}")
            print(f"[BRIDGE_ENTITY_AUDIT] snapshot.entities count={len(_entity_values(entities_dict))} names={_entity_names(entities_dict)}")
            print(f"[BRIDGE_ENTITY_AUDIT] bridge_input.entities count={len(_entity_values(bridge_input_entities))} names={_entity_names(bridge_input_entities)}")

            bridge_data = bridge_entities_for_scene(bridge_scene_doc, self.entity_cards)
            self.runtime.snapshot["bridge_entities"] = bridge_data
            self.runtime.snapshot["bridge_entities_scene_id"] = scene_id
            print(f"[BRIDGE_ENTITY_AUDIT] snapshot.bridge_entities count={len(_entity_values(bridge_data))} names={_entity_names(bridge_data)}")

            if isinstance(entities_dict, dict):
                for be in bridge_data:
                    if not isinstance(be, dict):
                        continue

                    eid = str(be.get("entity_id") or be.get("id") or "")
                    if not eid or eid not in entities_dict:
                        continue
                    if not isinstance(entities_dict[eid], dict):
                        continue

                    tr = be.get("transform")
                    if not isinstance(tr, dict):
                        continue

                    pos = tr.get("position")
                    if not isinstance(pos, dict):
                        continue

                    x = float(pos.get("x", 0.0))
                    y = float(pos.get("y", 0.0))
                    z = float(pos.get("z", 0.0))

                    current = entities_dict[eid].get("pos")
                    is_placeholder = (
                        not isinstance(current, (list, tuple))
                        or len(current) < 3
                        or (
                            float(current[0]) == 0.0
                            and float(current[1]) == 0.0
                            and float(current[2]) == 0.0
                        )
                    )

                    if is_placeholder:
                        entities_dict[eid]["pos"] = [x, y, z]

                    entities_dict[eid]["position"] = {"x": x, "y": y, "z": z}

                self.runtime.snapshot["entities"] = entities_dict

        except Exception as e:
            print(f"[BRIDGE] Error: {e}")
            self.runtime.snapshot["bridge_entities"] = []

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
