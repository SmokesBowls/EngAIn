from brushes.gflare_parser_mr import parse_gflare
import sys
from pathlib import Path
try:
    gflare = parse_gflare(Path("data/gflare/Default"))
    print(gflare)
except Exception as e:
    import traceback
    traceback.print_exc()
