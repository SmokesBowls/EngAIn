import fileinput
import re

filepath = "godotsim/sim_runtime.py"
marker = "# === VAULT AUTO-RELINK (persistent config survives restarts) ==="
new_block = f'''{marker}
# This is the new configuration that survives restarts
AUTO_RELINK_CONFIG = {{
    "enabled": True,
    "retry_attempts": 3,
}}
'''

with fileinput.FileInput(filepath, inplace=True, backup=".bak") as f:
    inside_block = False
    for line in f:
        if marker in line:
            # Start of the block – replace everything until the next blank line or end?
            print(new_block, end="")
            inside_block = True
        elif inside_block and line.strip() == "":
            # End of block (blank line) – print it and exit block mode
            print(line, end="")
            inside_block = False
        elif inside_block:
            # Skip old lines inside the block
            continue
        else:
            print(line, end="")
