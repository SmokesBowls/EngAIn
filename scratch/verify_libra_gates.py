import sys
from pathlib import Path

# Add project root and parent workspace folder to python path
sys.path.insert(0, "/home/mytruelove/Desktop/burdens_of_a_forgotten_past")
sys.path.insert(0, "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/conductor")

from trixel.libresprite.gates import gate_libresprite_starter_set

gates = [
    gate_libresprite_starter_set.gate_conductor_shape_available,
    gate_libresprite_starter_set.gate_libra_payload_conforms,
    gate_libresprite_starter_set.gate_libra_no_authority_leaks,
    gate_libresprite_starter_set.gate_conductor_accepts_valid_payload,
    gate_libresprite_starter_set.gate_conductor_rejects_leak_payload,
    gate_libresprite_starter_set.gate_conductor_wraps_packet
]

all_passed = True
print("=== Running LibreSprite Starter Set Gates ===")
for gate in gates:
    result = gate({})
    print(f"[{result.passed}] {result.gate_name}: {result.message}")
    if result.passed != "TRUE":
        all_passed = False

print(f"\nALL GATES PASSED: {all_passed}")
sys.exit(0 if all_passed else 1)
