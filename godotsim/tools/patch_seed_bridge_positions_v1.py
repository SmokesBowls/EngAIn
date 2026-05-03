#!/usr/bin/env python3
from pathlib import Path
import re
import sys

TARGET = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotsim/scene_manager.py")

NEW_METHOD = '''
    def _bridge_entities_for_scene(self):
        """Run semantic bridge on active scene → snapshot['bridge_entities'] for Godot.
        Also seed runtime entity positions from bridge transforms so runtime_core
        does not flatten everything back to origin.
        """
        if not _HAS_BRIDGE:
            return

        scene_doc = self.runtime.snapshot.get("scene")
        if not scene_doc:
            return

        try:
            bridge_data = bridge_entities_for_scene(scene_doc, self.entity_cards)
            self.runtime.snapshot["bridge_entities"] = bridge_data

            entities_dict = self.runtime.snapshot.get("entities", {})
            if isinstance(entities_dict, dict):
                for be in bridge_data:
                    if not isinstance(be, dict):
                        continue

                    eid = str(be.get("entity_id") or be.get("id") or "")
                    if not eid:
                        continue
                    if eid not in entities_dict:
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
'''

def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: target not found: {TARGET}")
        return 1

    original = TARGET.read_text(encoding="utf-8")
    backup = TARGET.with_name(TARGET.name + ".bak_seed_bridge_positions_v1")
    backup.write_text(original, encoding="utf-8")

    pattern = re.compile(
        r"(?ms)^    def _bridge_entities_for_scene\(self\):.*?(?=^    def handle_text_command\(self, text: str\) -> Dict\[str, Any\]:)"
    )

    if not pattern.search(original):
        print("ERROR: could not find _bridge_entities_for_scene method block.")
        return 2

    updated = pattern.sub(NEW_METHOD.rstrip() + "\n\n", original, count=1)
    TARGET.write_text(updated, encoding="utf-8")

    print(f"Patched: {TARGET}")
    print(f"Backup:  {backup}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
