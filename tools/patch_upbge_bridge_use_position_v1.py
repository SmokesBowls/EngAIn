# tools/patch_upbge_bridge_use_position_v1.py
#!/usr/bin/env python3
"""
Production-safe patcher for UPBGE bridge:
- Updates upbge/engain_upbge_bridge.py to prefer entity.position (UPBGE-space)
  then entity.transform_upbge.position, then legacy entity.transform.position.
- Creates a timestamped backup next to the target file.
- Idempotent (marker-based).

Run from repo root:
  python3 tools/patch_upbge_bridge_use_position_v1.py
"""

from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path


PATCH_MARKER = "# === UPBGE-POS v1 (prefer converted position) ==="


def _repo_root_from_this_file() -> Path:
    here = Path(__file__).resolve()
    return here.parent.parent


def main() -> int:
    root = _repo_root_from_this_file()
    target = root / "upbge" / "engain_upbge_bridge.py"

    if not target.exists():
        print(f"[PATCH] ERROR: cannot find {target}")
        return 2

    raw = target.read_text(encoding="utf-8")

    if PATCH_MARKER in raw:
        print("[PATCH] upbge/engain_upbge_bridge.py already patched (UPBGE-POS v1). Nothing to do.")
        return 0

    # Replace the exact pos assignment line your grep found.
    # Original:
    #   pos = _safe_get(ent, "transform.position", {}) or {}
    pat = re.compile(
        r'^(?P<indent>[ \t]*)pos\s*=\s*_safe_get\(\s*ent\s*,\s*"transform\.position"\s*,\s*\{\}\s*\)\s*or\s*\{\}\s*$',
        flags=re.M,
    )
    m = pat.search(raw)
    if not m:
        print('[PATCH] ERROR: did not find expected line: pos = _safe_get(ent, "transform.position", {}) or {}')
        return 3

    indent = m.group("indent")
    replacement = (
        f"{indent}{PATCH_MARKER}\n"
        f'{indent}pos = _safe_get(ent, "position", None)\n'
        f"{indent}if not isinstance(pos, dict):\n"
        f'{indent}    pos = _safe_get(ent, "transform_upbge.position", None)\n'
        f"{indent}if not isinstance(pos, dict):\n"
        f'{indent}    pos = _safe_get(ent, "transform.position", {}) or {}\n'
        f"{indent}# === END UPBGE-POS v1 ==="
    )

    patched = raw[: m.start()] + replacement + raw[m.end() :]

    # Compile check
    try:
        compile(patched, str(target), "exec")
    except SyntaxError as e:
        print("[PATCH] ERROR: patch produced invalid Python. Aborting.")
        print("        ", e)
        return 4

    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = target.with_suffix(target.suffix + f".bak.{ts}")
    backup.write_text(raw, encoding="utf-8")
    target.write_text(patched, encoding="utf-8")

    print("[PATCH] OK:", target)
    print("[PATCH] Backup:", backup)
    print("[PATCH] Verify with:")
    print('        grep -n "UPBGE-POS v1" -n upbge/engain_upbge_bridge.py')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
