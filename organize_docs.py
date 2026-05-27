#!/usr/bin/env python3
"""
Dry-run organizer for EngAIn/docs/
Classifies files by system based on filename + content, then moves them into docs/<system>/ folders.
SAFE: Runs as dry-run by default. Pass --execute to apply.
"""
import sys, os, shutil, re
from pathlib import Path
from collections import Counter

SYSTEMS = {
    "runtime": ["sim_runtime", "zw", "ZWR", "enforce", "tick", "delta", "state", "physics", "coherant", "pause", "softcode", "runtime"],
    "subsystems": ["faction", "combat", "inventory", "dialogue", "behavior", "adapter", "3d", "kernel", "vault", "slice", "spatial"],
    "trixel": ["trixel", "brush", "gbr", "gdyn", "gpl", "gtp", "palette", "world_tree", "gfig", "vbr", "pixel", "stroke"],
    "pipeline": ["metta", "pass1", "pass2", "pass3", "pass4", "pass5", "zonj", "narrative", "ingest", "compiler", "lore", "segment", "entity"],
    "godot": ["godot", "scene", "tscn", ".gd", "bridge", "spawn", "client", "render", "viewport", "autoload", "node_3d"],
    "blender": ["blender", "mcp", "addon", "export", "glb", "render_still", "list_objects", "bpy"],
    "upbge": ["upbge", "bge", "game_scenes"],
    "terrain": ["terrain", "threshold", "field", "nucleus", "biome"],
    "animation": ["mechanimation", "pose", "anim", "walk", "frame", "constraint", "studio", "keyframe"],
    "gui_tools": ["gui", "validator", "dashboard", "patch", "cleanup", "smoke", "audit", "test_", "pytest", "litmus", "requirements"],
    "architecture": ["okarchitect", "roadmap", "manifest", "structure", "brief", "design", "protocol", "canon", "architect"],
    "archive": ["old", "bak", "backup", "(copy)", "draft", "freeze", "log", "summary", "session", "transcribed", "todo", "feedback"]
}

PRIORITY = ["runtime", "subsystems", "trixel", "pipeline", "godot", "blender", "upbge", "terrain", "animation", "gui_tools", "architecture", "archive"]

def score_file(filepath):
    text = ""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read(4096).lower()  # Read first 4KB
    except Exception:
        text = ""
    
    fname = filepath.stem.lower() + " " + filepath.name.lower()
    scores = Counter()
    
    for sys_name, keywords in SYSTEMS.items():
        # Filename matches (higher weight)
        scores[sys_name] += sum(3 for kw in keywords if kw in fname)
        # Content matches
        scores[sys_name] += sum(1 for kw in keywords if kw in text)
        
    max_score = max(scores.values(), default=0)
    if max_score == 0:
        return "unclassified", 0
    
    # Break ties by priority
    candidates = [s for s, sc in scores.items() if sc == max_score]
    for p in PRIORITY:
        if p in candidates:
            return p, max_score
    return candidates[0], max_score

def main():
    docs_dir = Path("docs")
    if not docs_dir.exists():
        print("❌ 'docs/' directory not found.")
        sys.exit(1)

    execute = "--execute" in sys.argv
    dry_run = not execute
    
    print(f"🔍 Scanning files in: {docs_dir.absolute()}")
    print(f"📌 Mode: {'EXECUTE (will move files)' if execute else 'DRY-RUN (safe preview)'}\n")

    files = sorted([f for f in docs_dir.iterdir() if f.is_file() and not f.name.startswith(".")])
    plan = []

    for f in files:
        sys_name, conf = score_file(f)
        target_dir = docs_dir / sys_name
        plan.append((f, target_dir, sys_name, conf))

    # Group by target
    grouped = {}
    for src, tgt, sys_name, conf in plan:  # Fixed loop variable 'sys' -> 'sys_name'
        grouped.setdefault(sys_name, []).append((src, tgt, conf))

    print("📋 CLASSIFICATION PLAN")
    print("-" * 80)
    print(f"{'SYSTEM':<15} | {'FILES':<5} | EXAMPLES")
    print("-" * 80)
    
    # Fixed loop variable 'sys' -> 'system'
    for system in PRIORITY + ["unclassified"]:
        if system in grouped:
            examples = [f[0].name for f in grouped[system][:3]]
            print(f"{system:<15} | {len(grouped[system]):<5} | {', '.join(examples)}")
            
    print("-" * 80)
    print(f"\n✅ Dry-run complete. {sum(len(v) for v in grouped.values())} files would be organized.")
    
    if dry_run:
        print("💡 To actually move files, run:")
        print(f"   python3 {os.path.basename(__file__)} --execute")
        print("\n🔒 No files were modified.")
        sys.exit(0)

    # EXECUTE MODE
    print("\n🚀 EXECUTING MOVE OPERATIONS...")
    for sys_name, files_list in grouped.items():
        target_dir = docs_dir / sys_name
        target_dir.mkdir(exist_ok=True)
        for src, tgt, conf in files_list:
            dest = target_dir / src.name
            if dest.exists():
                print(f"⚠️  Skipping {src.name} (already exists in {sys_name}/)")
                continue
            shutil.move(str(src), str(dest))
            print(f"  📦 {src.name} → {sys_name}/")
            
    print("\n✅ Organization complete. Review with: tree docs/")
    print("💡 Commit before pushing: git add docs/ && git commit -m 'organize docs by system'")

if __name__ == "__main__":
    main()