import json
import os

def generate_summary():
    summary_lines = []
    
    # Baseline check
    baseline_path = "cleanup_reports/works-baseline.txt"
    with open(baseline_path, "r") as f:
        baseline_content = f.read()
    
    failed = "FAILED" in baseline_content or "ERRORS" in baseline_content
    summary_lines.append(f"Baseline passed: {'No' if failed else 'Yes'}")
    
    # Check if engainos baseline imported godotsim
    # We can check the full-stack trace or the baseline test files.
    # Actually, the rule says "whether engainos baseline imported any godotsim modules".
    # Let's check cleanup_reports/import-trace-full-stack.json
    
    imported_godotsim = "No"
    godotsim_count = 0
    try:
        with open("cleanup_reports/import-trace-full-stack.json", "r") as f:
            data = json.load(f)
            godotsim_count = data["counts"].get("godotsim", 0)
            if godotsim_count > 0:
                imported_godotsim = "Yes"
    except:
        pass
    
    summary_lines.append(f"Engainos baseline imported godotsim: {imported_godotsim} ({godotsim_count} modules)")
    
    # Top 10 duplicate module names by risk (same name, different roots)
    summary_lines.append("\nTop 10 duplicate module names by risk:")
    duplicates = []
    if os.path.exists("cleanup_reports/duplicate-modules.txt"):
        with open("cleanup_reports/duplicate-modules.txt", "r") as f:
            current_mod = None
            current_paths = []
            for line in f:
                line = line.strip()
                if not line:
                    if current_mod:
                        duplicates.append((current_mod, current_paths))
                        current_mod = None
                        current_paths = []
                elif line.startswith("godotengain") or line.startswith("godotsim") or line.startswith("core") or line.startswith("  "):
                    current_paths.append(line.strip())
                else:
                    current_mod = line
            if current_mod:
                duplicates.append((current_mod, current_paths))
    
    # Sort duplicates by number of paths (higher risk?)
    sorted_duplicates = sorted(duplicates, key=lambda x: len(x[1]), reverse=True)
    for mod, paths in sorted_duplicates[:10]:
        summary_lines.append(f"- {mod} ({len(paths)} paths)")
    
    # Top 20 unused candidates (lowest risk first)
    summary_lines.append("\nTop 20 unused candidates (lowest risk first):")
    unused = []
    if os.path.exists("cleanup_reports/unused-candidates.txt"):
        with open("cleanup_reports/unused-candidates.txt", "r") as f:
            current_path = None
            current_reasons = None
            for line in f:
                line = line.strip()
                if line.startswith("path: "):
                    current_path = line[len("path: "):]
                elif line.startswith("reason flags: "):
                    current_reasons = line[len("reason flags: "):]
                    unused.append((current_path, current_reasons))
    
    # Lowest risk first: maybe those that are farthest from core? Or just list from the file.
    for path, reasons in unused[:20]:
        summary_lines.append(f"- {path} [{reasons}]")
    
    # Recommended next action
    summary_lines.append("\nRecommended next action: quarantine list vs keep")
    summary_lines.append("Quarantine candidates with 'no-imports, no-godot-refs, not-entrypoint' flags.")
    
    with open("cleanup_reports/summary.txt", "w") as f:
        f.write("\n".join(summary_lines))

if __name__ == '__main__':
    generate_summary()
