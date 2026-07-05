# gate_player_movement_proof.py
"""
Godot Player Movement Proof Gate - Validates player movement in a Godot scene.
"""

import subprocess
import sys
from pathlib import Path

def run_godot_script(script_path, output_file):
    """Run the Godot script and capture stdout."""
    try:
        result = subprocess.run(
            ["godot", "--headless", "--script", str(script_path)],
            check=True,
            text=True,
            capture_output=True
        )
        with open(output_file, "w") as f:
            f.write(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Godot script failed: {e}")
        return False, str(e)

def main():
    script_path = Path(__file__).parent / "scripts/player_movement.gd"
    output_file = Path(__file__).parent / "player_movement_output.txt"

    success, stdout = run_godot_script(script_path, output_file)
    
    if success:
        print("gate_player_movement_proof: TRUE")
        sys.exit(0)
    else:
        print(f"gate_player_movement_proof: FALSE - {stdout}")
        sys.exit(1)

if __name__ == "__main__":
    main()
