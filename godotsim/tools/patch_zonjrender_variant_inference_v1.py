#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import os
import re
import sys
import tempfile

TARGET = Path("/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/SemanticRenderer.gd")
MARK = "# [PATCH variant-inference-fix V1]"

def backup(path: Path, s: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak.{ts}")
    b.write_text(s, encoding="utf-8")
    return b

def atomic_write(path: Path, s: str) -> None:
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(s)
        os.replace(tmp, path)
    finally:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except Exception:
            pass

def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: missing {TARGET}", file=sys.stderr)
        return 2

    s0 = TARGET.read_text(encoding="utf-8", errors="strict")
    if MARK in s0:
        print(f"OK: already patched: {TARGET}")
        return 0

    s = s0
    changed = False

    # Fix 1: inside _frame_camera_to_entities
    s2, n = re.subn(
        r'^\s*var\s+cam\s*:=\s*_get_primary_camera\(\)\s*$',
        '\tvar cam: Camera3D = _get_primary_camera()',
        s,
        flags=re.M
    )
    if n:
        changed = True
        s = s2

    # Fix 2: inside _get_primary_camera
    s2, n = re.subn(
        r'^\s*var\s+cam\s*:=\s*get_viewport\(\)\.get_camera_3d\(\)\s*$',
        '\tvar cam: Camera3D = get_viewport().get_camera_3d()',
        s,
        flags=re.M
    )
    if n:
        changed = True
        s = s2

    if not changed:
        print("ERROR: did not find expected cam := lines to patch. Paste lines ~480-520 again.", file=sys.stderr)
        return 3

    # Add marker near top for idempotency
    m = re.search(r'^extends\s+Node3D\s*$', s, flags=re.M)
    if m:
        insert_at = s.find("\n", m.end())
        if insert_at != -1:
            s = s[:insert_at+1] + MARK + "\n" + s[insert_at+1:]

    b = backup(TARGET, s0)
    atomic_write(TARGET, s)
    print(f"PATCHED: {TARGET}")
    print(f"BACKUP : {b}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

