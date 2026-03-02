cat > /home/burdens/burdens_of_a_forgotten_past/EngAIn/tools/which_ap_engine_is_live.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail

REPO="/home/burdens/burdens_of_a_forgotten_past/EngAIn"
cd "$REPO"

python3 - <<'PY'
import importlib, sys
from pathlib import Path

# Ensure repo root is importable even when running from elsewhere
repo = Path("/home/burdens/burdens_of_a_forgotten_past/EngAIn").resolve()
if str(repo) not in sys.path:
    sys.path.insert(0, str(repo))

m = importlib.import_module("godotengain.engainos.core.ap_engine")
print("godotengain.engainos.core.ap_engine ->", getattr(m, "__file__", None))

print("\nsys.path (top 10):")
for p in sys.path[:10]:
    print(" ", p)
PY
SH

chmod +x /home/burdens/burdens_of_a_forgotten_past/EngAIn/tools/which_ap_engine_is_live.sh
