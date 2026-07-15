#!/usr/bin/env python3
import os, sys
from pathlib import Path
import importlib

ENGAIN_ROOT = Path("/home/burdens/burdens_of_a_forgotten_past/EngAIn").resolve()
os.environ.setdefault("ENGAIN_ROOT", str(ENGAIN_ROOT))
if str(ENGAIN_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGAIN_ROOT))

core = importlib.import_module("godotengain.engainos.core.ap_engine")
print("ENGAIN_ROOT:", ENGAIN_ROOT)
print("core file :", core.__file__)

# list any loaded ap_engine.py modules (should be exactly one)
copies = []
for name, mod in sys.modules.items():
    p = getattr(mod, "__file__", "") or ""
    if p.endswith("ap_engine.py"):
        copies.append((name, p))

print("\nap_engine.py copies loaded:")
for n, p in sorted(copies):
    print(" ", n, "->", p)

if len(copies) != 1:
    raise SystemExit("WARN: More than one ap_engine.py loaded (path leak).")

