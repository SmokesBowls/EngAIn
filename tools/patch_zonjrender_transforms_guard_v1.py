#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import os
import re
import sys
import tempfile

TARGET = Path("/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/SemanticRenderer.gd")
MARK = "# [PATCH transforms-inflight-guard V1]"

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

    # 1) Add _pending_transforms flag near _pending_fetch
    if "var _pending_transforms" not in s:
        m = re.search(r"^var _pending_fetch: bool = false\s*$", s, flags=re.M)
        if not m:
            print("ERROR: could not find '_pending_fetch' var anchor.", file=sys.stderr)
            return 3
        insert_at = s.find("\n", m.end())
        if insert_at == -1:
            insert_at = len(s)
        s = s[:insert_at+1] + "var _pending_transforms: bool = false\n" + s[insert_at+1:]
        changed = True

    # 2) Patch _poll_transforms to guard inflight + reset on request failure
    pat_poll = re.compile(
        r"^func _poll_transforms\(\) -> void:\n(?P<body>(?:\t.*\n)+)",
        flags=re.M
    )
    m = pat_poll.search(s)
    if not m:
        print("ERROR: could not locate func _poll_transforms().", file=sys.stderr)
        return 4

    body = m.group("body")
    # Replace the existing request line with guarded version
    if 'request("%s/transforms" % runtime_url)' not in body:
        print("ERROR: expected transforms request line not found inside _poll_transforms().", file=sys.stderr)
        return 5

    new_body = body
    # Insert guard before request
    if "\tif _pending_transforms" not in new_body:
        new_body = new_body.replace(
            '\tif _entity_nodes.is_empty():\n\t\treturn\n',
            '\tif _entity_nodes.is_empty():\n\t\treturn\n\tif _pending_transforms:\n\t\treturn\n\t_pending_transforms = true\n',
            1
        )

    # Replace request call to capture error + reset flag if it fails to start
    new_body = re.sub(
        r'^\t_http_transforms\.request\("%s/transforms" % runtime_url\)\s*# 👈 NEW ENDPOINT\s*$',
        '\tvar err = _http_transforms.request("%s/transforms" % runtime_url)\n\tif err != OK:\n\t\t_pending_transforms = false',
        new_body,
        flags=re.M
    )

    if new_body == body:
        print("ERROR: failed to modify _poll_transforms body (unexpected formatting).", file=sys.stderr)
        return 6

    s = s[:m.start("body")] + new_body + s[m.end("body"):]
    changed = True

    # 3) Patch _on_transform_update to clear inflight flag ASAP
    # Insert _pending_transforms = false right at the top of the function body.
    m2 = re.search(r"^func _on_transform_update\([^\)]*\) -> void:\s*$", s, flags=re.M)
    if not m2:
        print("ERROR: could not locate func _on_transform_update().", file=sys.stderr)
        return 7

    line_end = s.find("\n", m2.end())
    if line_end == -1:
        line_end = len(s)

    # Only insert if not already present near top
    head_chunk = s[line_end+1:line_end+200]
    if "_pending_transforms = false" not in head_chunk:
        s = s[:line_end+1] + "\t_pending_transforms = false\n" + s[line_end+1:]
        changed = True

    # 4) Mark file
    if changed and MARK not in s:
        m3 = re.search(r"^extends\s+Node3D\s*$", s, flags=re.M)
        if m3:
            ins = s.find("\n", m3.end())
            if ins != -1:
                s = s[:ins+1] + MARK + "\n" + s[ins+1:]

    b = backup(TARGET, s0)
    atomic_write(TARGET, s)
    print(f"PATCHED: {TARGET}")
    print(f"BACKUP : {b}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

