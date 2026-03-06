#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import os
import re
import sys
import tempfile


MARK_SR = "# [PATCH payload-unpack V1]"
MARK_UI = "# [PATCH ui-toggle V1]"


def _atomic_write(path: Path, content: str) -> None:
    fd, tmp_path = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass


def _backup(path: Path, original: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak.{ts}")
    b.write_text(original, encoding="utf-8")
    return b


def _find_zonj_project(repo_root: Path) -> Path:
    # Try the canonical location first
    candidate = repo_root / "godotroot" / "zonjrender" / "project.godot"
    if candidate.exists():
        return candidate

    # Otherwise search a bit
    for p in repo_root.rglob("project.godot"):
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if 'config/name="zonjrender"' in txt:
            return p

    raise FileNotFoundError("Could not find zonjrender project.godot")


def patch_semantic_renderer(project_root: Path) -> str:
    sr = project_root / "SemanticRenderer.gd"
    if not sr.exists():
        return f"ERROR: missing {sr}"

    s0 = sr.read_text(encoding="utf-8", errors="strict")
    if MARK_SR in s0:
        return f"OK: already patched {sr}"

    # Anchor block in _on_lifecycle_snapshot
    anchor = (
        "\t# Unwrap protocol envelope\n"
        "\tvar snapshot: Dictionary = data.get(\"snapshot\", data)\n"
    )
    if anchor not in s0:
        return f"ERROR: anchor not found in {sr} (unexpected SemanticRenderer.gd shape)"

    replacement = (
        "\t# Unwrap protocol envelope (supports EngAIn payload envelope)\n"
        f"\t{MARK_SR}\n"
        "\tvar snapshot: Dictionary = {}\n"
        "\tif data.has(\"payload\") and data.get(\"payload\") is Dictionary:\n"
        "\t\tsnapshot = data.get(\"payload\")\n"
        "\telif data.has(\"snapshot\") and data.get(\"snapshot\") is Dictionary:\n"
        "\t\tsnapshot = data.get(\"snapshot\")\n"
        "\telse:\n"
        "\t\tsnapshot = data\n"
    )

    s1 = s0.replace(anchor, replacement, 1)
    _backup(sr, s0)
    _atomic_write(sr, s1)
    return f"PATCHED: {sr}"


def patch_entity_editor_control(project_root: Path) -> str:
    cg = project_root / "scenes" / "control.gd"
    if not cg.exists():
        return f"ERROR: missing {cg}"

    s0 = cg.read_text(encoding="utf-8", errors="strict")
    if MARK_UI in s0:
        return f"OK: already patched {cg}"

    # Insert export + state near the runtime_url export
    needle = '@export var runtime_url: String = "http://localhost:8080"\n'
    if needle not in s0:
        return f"ERROR: expected runtime_url export not found in {cg}"

    insert = (
        needle +
        "\n" +
        f"{MARK_UI}\n" +
        "@export var hide_search_ui_on_start: bool = true\n" +
        "var _search_ui_visible: bool = true\n"
    )
    s1 = s0.replace(needle, insert, 1)

    # In _ready(), after panel.visible = false, hide Search UI if configured
    ready_anchor = "\tpanel.visible = false\n"
    if ready_anchor not in s1:
        return f"ERROR: expected panel.visible anchor not found in {cg}"

    ready_insert = (
        ready_anchor +
        "\n" +
        "\t_search_ui_visible = not hide_search_ui_on_start\n" +
        "\t_set_search_ui_visible(_search_ui_visible)\n"
    )
    s2 = s1.replace(ready_anchor, ready_insert, 1)

    # Add key handling to _unhandled_input
    # We inject at the top of _unhandled_input before mouse handling.
    pat = re.compile(r"^func _unhandled_input\(event: InputEvent\) -> void:\n", re.M)
    m = pat.search(s2)
    if not m:
        return f"ERROR: could not find _unhandled_input in {cg}"

    # Find the first line after func signature
    func_start = m.end()
    injection = (
        "\tif event is InputEventKey and event.pressed and not event.echo:\n"
        "\t\tif event.keycode == KEY_F1:\n"
        "\t\t\t_search_ui_visible = not _search_ui_visible\n"
        "\t\t\t_set_search_ui_visible(_search_ui_visible)\n"
        "\t\t\tif not _search_ui_visible:\n"
        "\t\t\t\tpanel.visible = false\n"
        "\t\t\t\t_deselect()\n"
        "\t\t\taccept_event()\n"
        "\t\t\treturn\n\n"
    )
    s3 = s2[:func_start] + injection + s2[func_start:]

    # Append helper function at end (idempotent-ish)
    if "func _set_search_ui_visible(" not in s3:
        s3 = s3.rstrip() + "\n\n" + (
            "func _set_search_ui_visible(v: bool) -> void:\n"
            "\tvar p := get_parent()\n"
            "\tif p == null:\n"
            "\t\treturn\n"
            "\tvar sr := p.get_node_or_null(\"SearchRow\")\n"
            "\tif sr:\n"
            "\t\tsr.visible = v\n"
            "\tvar body := p.get_node_or_null(\"Body\")\n"
            "\tif body:\n"
            "\t\tbody.visible = v\n"
        ) + "\n"

    _backup(cg, s0)
    _atomic_write(cg, s3)
    return f"PATCHED: {cg}"


def main() -> int:
    repo_root = Path("/home/burdens/burdens_of_a_forgotten_past/EngAIn")
    try:
        proj = _find_zonj_project(repo_root)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    project_root = proj.parent
    print(f"Found zonjrender project: {proj}")
    print(patch_semantic_renderer(project_root))
    print(patch_entity_editor_control(project_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

