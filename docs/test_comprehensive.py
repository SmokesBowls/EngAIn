import json
from core.zon.zon_binary_pack import pack_zonj, unpack_zonb, pack_file, unpack_file
import tempfile
import os

test_cases = [
    # Simple array
    [1, "hello", {"nested": True}, None],
    
    # Dict with root array
    {"root": [1, "hello", {"nested": True}, None]},
    
    # Complex nested structure
    {
        "type": "test",
        "id": 42,
        "data": {
            "items": ["a", "b", "c"],
            "config": {"enabled": True, "count": 3}
        }
    },
    
    # With field_N patterns
    {
        "field_1": "value1",
        "field_2": 123,
        "field_100": [1, 2, 3]
    }
]

print("Running comprehensive tests...")
for i, test_data in enumerate(test_cases):
    print(f"\nTest case {i+1}: {type(test_data).__name__}")
    
    # Test pack/unpack functions
    packed = pack_zonj(test_data)
    unpacked = unpack_zonb(packed)
    
    if test_data == unpacked:
        print(f"  ✓ Direct pack/unpack: PASS")
    else:
        print(f"  ✗ Direct pack/unpack: FAIL")
        print(f"    Original: {test_data}")
        print(f"    Roundtrip: {unpacked}")
    
    # Test file roundtrip
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        input_file = f.name
    
    try:
        bin_file = input_file.replace('.json', '.zonb')
        output_file = input_file.replace('.json', '_rt.json')
        
        pack_file(input_file, bin_file)
        unpack_file(bin_file, output_file)
        
        with open(output_file, 'r') as f:
            file_roundtrip = json.load(f)
        
        if test_data == file_roundtrip:
            print(f"  ✓ File roundtrip: PASS")
        else:
            print(f"  ✗ File roundtrip: FAIL")
        
        # Clean up
        os.unlink(bin_file)
        os.unlink(output_file)
    finally:
        os.unlink(input_file)

print("\n✅ All tests completed!")
