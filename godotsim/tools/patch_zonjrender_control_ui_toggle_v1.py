#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import os
import re
import sys
import tempfile

TARGET = Path("/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/scenes/control.gd")
MARK = "# [PATCH ui-toggle V1]"

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

    # 1) Add exports/state right after runtime_url export
    needle = '@export var runtime_url: String = "http://localhost:8080"\n'
    if needle not in s:
        print("ERROR: expected runtime_url export not found; refusing to patch.", file=sys.stderr)
        return 3

    insert = (
        needle +
        "\n" +
        f"{MARK}\n"
        "@export var hide_search_ui_on_start: bool = true\n"
        "var _search_ui_visible: bool = true\n"
    )
    s = s.replace(needle, insert, 1)

    # 2) In _ready(), after panel.visible = false, apply initial UI visibility
    m_ready = re.search(r"^func _ready\(\)\s*->\s*void:\s*$", s, flags=re.M)
    if not m_ready:
        print("ERROR: func _ready() not found.", file=sys.stderr)
        return 4

    m_panel = re.search(r"^\s*panel\.visible\s*=\s*false\s*$", s, flags=re.M)
    if not m_panel:
        print("ERROR: panel.visible = false not found (unexpected file shape).", file=sys.stderr)
        return 5

    # Insert immediately after that line (preserve indentation)
    line_end = s.find("\n", m_panel.end())
    if line_end == -1:
        line_end = len(s)
    indent = re.match(r"^(\s*)", m_panel.group(0)).group(1)
    add_ready = (
        "\n"
        f"{indent}_search_ui_visible = not hide_search_ui_on_start\n"
        f"{indent}_set_search_ui_visible(_search_ui_visible)\n"
    )
    s = s[:line_end] + add_ready + s[line_end:]

    # 3) Inject F1 toggle at top of _unhandled_input
    m_ui = re.search(r"^func _unhandled_input\(event:\s*InputEvent\)\s*->\s*void:\s*$", s, flags=re.M)
    if not m_ui:
        print("ERROR: func _unhandled_input(...) not found.", file=sys.stderr)
        return 6

    inject_point = s.find("\n", m_ui.end())
    if inject_point == -1:
        inject_point = len(s)

    # Determine indentation of the first code line after the function signature
    # Default to 4 spaces if we can't detect.
    after = s[inject_point+1:inject_point+200]
    m_indent = re.search(r"^(\s+)\S", after, flags=re.M)
    ind = m_indent.group(1) if m_indent else "    "

    key_block = (
        "\n"
        f"{ind}if event is InputEventKey and event.pressed and not event.echo:\n"
        f"{ind}    if event.keycode == KEY_F1:\n"
        f"{ind}        _search_ui_visible = not _search_ui_visible\n"
        f"{ind}        _set_search_ui_visible(_search_ui_visible)\n"
        f"{ind}        if not _search_ui_visible:\n"
        f"{ind}            panel.visible = false\n"
        f"{ind}            _deselect()\n"
        f"{ind}        accept_event()\n"
        f"{ind}        return\n"
    )
    s = s[:inject_point+1] + key_block + s[inject_point+1:]

    # 4) Add helper function at end if missing
    if "func _set_search_ui_visible(" not in s:
        s = s.rstrip() + "\n\n" + (
            "func _set_search_ui_visible(v: bool) -> void:\n"
            "    var p := get_parent()\n"
            "    if p == null:\n"
            "        return\n"
            "    var sr := p.get_node_or_null(\"SearchRow\")\n"
            "    if sr:\n"
            "        sr.visible = v\n"
            "    var body := p.get_node_or_null(\"Body\")\n"
            "    if body:\n"
            "        body.visible = v\n"
        ) + "\n"

    b = backup(TARGET, s0)
    atomic_write(TARGET, s)
    os.chmod(TARGET, 0o664)

    print(f"PATCHED: {TARGET}")
    print(f"BACKUP : {b}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

