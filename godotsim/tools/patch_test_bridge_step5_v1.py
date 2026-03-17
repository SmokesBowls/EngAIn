#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import os
import sys


TARGET = Path("/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotsim/test_bridge.sh")


NEW_BLOCK = r'''echo ""
echo "5. Checking snapshot for bridge_entities..."

# Pull snapshot and parse payload.bridge_entities (retry briefly in case of timing jitter)
snap=""
for i in $(seq 1 10); do
  snap="$(curl -sS http://127.0.0.1:8080/snapshot || true)"
  count="$(python3 -c 'import sys,json; 
d=json.loads(sys.stdin.read() or "{}"); 
p=d.get("payload",{}); 
be=p.get("bridge_entities") or []; 
print(len(be))' <<<"$snap" 2>/dev/null || echo 0)"
  if [ "$count" -gt 0 ]; then
    break
  fi
  sleep 0.2
done

python3 - <<'PY'
import json, sys

try:
    d = json.loads(sys.stdin.read() or "{}")
except Exception:
    d = {}

p = d.get("payload", {}) if isinstance(d, dict) else {}
scene_id = p.get("scene_id") or "none"
scene_ok = isinstance(p.get("scene"), dict)
be = p.get("bridge_entities") or []
entities_map = p.get("entities") or {}
spatial_map = (p.get("spatial") or {}).get("entities") or {}

print(f"  Scene: {scene_id}")
print(f"  Has payload.scene: {scene_ok}")
print(f"  Bridge entities: {len(be)}")
print(f"  payload.entities map: {len(entities_map) if isinstance(entities_map, dict) else 0}")
print(f"  payload.spatial.entities map: {len(spatial_map) if isinstance(spatial_map, dict) else 0}")

if not be:
    print("")
    print("  ✗ No bridge_entities in snapshot")
    print("    (This script reads payload.bridge_entities. If it stays empty, check sim_runtime snapshot hydration.)")
else:
    e = be[0] if isinstance(be[0], dict) else {}
    print(f"  Sample: {e.get('entity_id')} {e.get('placeholder_mesh')} {e.get('position')}")
PY <<<"$snap"
'''

def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: not found: {TARGET}", file=sys.stderr)
        return 2

    s = TARGET.read_text(encoding="utf-8")

    start_key = "5. Checking snapshot for bridge_entities"
    end_key = "6. Quick look command"

    start = s.find(start_key)
    if start == -1:
        print(f"ERROR: could not find '{start_key}' in {TARGET}", file=sys.stderr)
        return 3

    end = s.find(end_key, start)
    if end == -1:
        print(f"ERROR: could not find '{end_key}' after step 5 in {TARGET}", file=sys.stderr)
        return 4

    # Replace from the line that prints step 5 through just before step 6 header line.
    # Find the beginning of the line containing step 5
    line_start = s.rfind("\n", 0, start)
    line_start = 0 if line_start == -1 else line_start + 1

    # Find the beginning of the line containing step 6
    end_line_start = s.rfind("\n", 0, end)
    end_line_start = 0 if end_line_start == -1 else end_line_start + 1

    patched = s[:line_start] + NEW_BLOCK + "\n" + s[end_line_start:]

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_suffix(TARGET.suffix + f".bak.{ts}")
    backup.write_text(s, encoding="utf-8")
    TARGET.write_text(patched, encoding="utf-8")

    os.chmod(TARGET, 0o775)

    print(f"PATCHED: {TARGET}")
    print(f"BACKUP : {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

