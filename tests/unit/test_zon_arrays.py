import pytest
import json
import os
from core.zon.zon_binary_pack import pack_zonj, unpack_zonb, pack_file, unpack_file

def compare_with_tolerance(a, b, tolerance=1e-10):
    """Compare two values with tolerance for floating-point differences."""
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        for key in a:
            if not compare_with_tolerance(a[key], b[key], tolerance):
                return False
        return True
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        for ai, bi in zip(a, b):
            if not compare_with_tolerance(ai, bi, tolerance):
                return False
        return True
    elif isinstance(a, float) and isinstance(b, float):
        return abs(a - b) <= tolerance
    else:
        return a == b

def test_root_array():
    """Test array structure preservation through pack/unpack."""
    test_array = [1, "hello", {"nested": True}, None]
    packed = pack_zonj(test_array)
    unpacked = unpack_zonb(packed)
    assert compare_with_tolerance(unpacked, test_array)

def test_roundtrip_file():
    """Test full file pack → unpack roundtrip."""
    test_files = [
        "zork/test_unpack_fixed.zonj.json",
        "door_rule.zonj.json",
        "mettaext/pipeline_test_output/out_pass1_test_narrative.zonj.json"
    ]

    for test_file in test_files:
        if not os.path.exists(test_file):
            continue

        # Create temp output paths
        bin_file = test_file + ".tmp.zonb"
        rt_file = test_file + ".rt.json"

        # Pack
        pack_file(test_file, bin_file)

        # Unpack
        unpack_file(bin_file, rt_file)

        # Load and compare with tolerance
        with open(test_file, 'r') as f:
            original = json.load(f)
        with open(rt_file, 'r') as f:
            roundtrip = json.load(f)

        # Clean up temp files
        os.unlink(bin_file)
        os.unlink(rt_file)

        assert compare_with_tolerance(original, roundtrip), f"Roundtrip failed for {test_file}"
