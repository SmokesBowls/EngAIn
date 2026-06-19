"""
ZON Binary Packing Module

Handles serialization and deserialization of ZON files:
- .zonj.json (canonical JSON) → .zonb (binary packed)
- .zonb (binary packed) → .zonj.json (canonical JSON)

Type Encoding:
- 0x10: int
- 0x11: bool  
- 0x12: string
- 0x13: array
- 0x14: nested block (dict)
- 0x15: float
- 0x16: null

Field IDs (common fields get low IDs for efficiency):
- 0x01: type
- 0x02: name
- 0x03: value
- 0x04: children
- 0x05: position
- 0x06: compress
- 0x80+: custom fields (auto-assigned)

Binary Format:
  [Magic: "ZONB"][Field ID][Type Marker][Value Data]...
"""

import struct
from typing import Any, Dict, Tuple

# Define core field ID and type marker maps
# Field IDs: 0x01-0x7F (avoid 0x10-0x16 used by type markers)
DEFAULT_FIELD_IDS = {
    "type": 0x01,
    "name": 0x02,
    "value": 0x03,
    "children": 0x04,
    "position": 0x05,
    "compress": 0x06,
    "id": 0x07,
    "condition": 0x08,
    "requires": 0x09,
    "effect": 0x0A,
    "metadata": 0x0B,
    "description": 0x0C,
    "flags": 0x0D,
    "exits": 0x0E,
    "flag": 0x0F,
    "time": 0x17,
    "action": 0x18,
    "created": 0x19,
    "items": 0x1A,
    "_tag": 0x1B,
    "_values": 0x1C,
    "contents": 0x1D,
    "quantity": 0x1E,
    "objects": 0x1F,
    "dialogue": 0x20,
    "level": 0x21,
    "health": 0x22,
    "hostile": 0x23,
    "damage": 0x24,
    "weight": 0x25,
}

# Type markers: 0x10-0x1F range
TYPE_MARKERS = {
    int: 0x10,
    bool: 0x11,
    str: 0x12,
    list: 0x13,
    dict: 0x14,
    float: 0x15,
    type(None): 0x16,
}

# Reverse map for unpacking
REVERSE_TYPE_MARKERS = {v: k for k, v in TYPE_MARKERS.items()}
REVERSE_FIELD_IDS = {v: k for k, v in DEFAULT_FIELD_IDS.items()}

# Magic header
ZONB_MAGIC = b'ZONB'


def write_field(field_id: int, value: Any) -> bytes:
    """
    Write a single field with type marker and value data.
    
    Args:
        field_id: Numeric field identifier
        value: Value to encode
        
    Returns:
        Binary representation of field
    """
    # Handle bool before int since bool is subclass of int
    if isinstance(value, bool):
        type_marker = TYPE_MARKERS[bool]
    else:
        type_marker = TYPE_MARKERS[type(value)]
    
    data = bytes([field_id, type_marker])

    if isinstance(value, bool):
        data += b"\x01" if value else b"\x00"
    elif isinstance(value, int):
        data += struct.pack(">i", value)
    elif isinstance(value, float):
        data += struct.pack(">f", value)
    elif isinstance(value, str):
        encoded = value.encode("utf-8")
        data += struct.pack(">H", len(encoded)) + encoded
    elif isinstance(value, list):
        data += struct.pack(">H", len(value))
        for item in value:
            data += write_field(0x00, item)  # Anonymous items
    elif isinstance(value, dict):
        data += struct.pack(">H", len(value))
        for k, v in value.items():
            field_id_k = DEFAULT_FIELD_IDS.get(k, 0x80)  # custom fields > 127
            data += write_field(field_id_k, v)
    elif value is None:
        pass  # Already wrote the null marker
    else:
        raise TypeError(f"Unsupported type: {type(value)}")

    return data


def pack_zonj(json_data) -> bytes:
    """
    Pack a ZONJ (JSON) structure into binary ZONB format.
    
    Args:
        json_data: Dictionary or list representation of ZONJ file
        
    Returns:
        Binary packed data as bytes
        
    Example:
        >>> data = {"type": "room", "name": "KITCHEN"}
        >>> binary = pack_zonj(data)
        >>> binary[:4]
        b'ZONB'
    """
    binary = ZONB_MAGIC
    
    # Handle both dict and list
    if isinstance(json_data, dict):
        for key, value in json_data.items():
            field_id = DEFAULT_FIELD_IDS.get(key, 0x80)
            binary += write_field(field_id, value)
    elif isinstance(json_data, list):
        # Pack as a single array field
        binary += write_field(0x00, json_data)  # field_id 0x00 for root array
    else:
        raise TypeError(f"Expected dict or list, got {type(json_data)}")
    
    return binary


def read_value(binary_data: bytes, ptr: int) -> Tuple[Any, int]:
    """
    Read a single value from binary data starting at ptr.
    
    Args:
        binary_data: Full binary buffer
        ptr: Current read position
        
    Returns:
        Tuple of (decoded_value, new_ptr_position)
    """
    type_marker = binary_data[ptr]
    ptr += 1
    
    if type_marker not in REVERSE_TYPE_MARKERS:
        raise TypeError(f"Unknown type marker: 0x{type_marker:02x} at position {ptr-1}")
    
    type_type = REVERSE_TYPE_MARKERS[type_marker]
    
    if type_type == int:
        value = struct.unpack(">i", binary_data[ptr:ptr+4])[0]
        ptr += 4
    elif type_type == float:
        value = struct.unpack(">f", binary_data[ptr:ptr+4])[0]
        ptr += 4
    elif type_type == bool:
        value = binary_data[ptr] == 1
        ptr += 1
    elif type_type == str:
        strlen = struct.unpack(">H", binary_data[ptr:ptr+2])[0]
        ptr += 2
        value = binary_data[ptr:ptr+strlen].decode("utf-8")
        ptr += strlen
    elif type_type == list:
        listlen = struct.unpack(">H", binary_data[ptr:ptr+2])[0]
        ptr += 2
        value = []
        for _ in range(listlen):
            # Each item has field_id (we skip it for list items) + type + data
            ptr += 1  # Skip field_id (0x00 for anonymous)
            item_value, ptr = read_value(binary_data, ptr)
            value.append(item_value)
    elif type_type == dict:
        dictlen = struct.unpack(">H", binary_data[ptr:ptr+2])[0]
        ptr += 2
        value = {}
        for _ in range(dictlen):
            # Read field_id for this dict entry
            sub_field_id = binary_data[ptr]
            ptr += 1
            field_name = REVERSE_FIELD_IDS.get(sub_field_id, f"field_{sub_field_id}")
            # Read the value
            sub_value, ptr = read_value(binary_data, ptr)
            value[field_name] = sub_value
    elif type_type == type(None):
        value = None
    else:
        raise TypeError(f"Unhandled type: {type_type}")
    
    return value, ptr


def unpack_zonb(binary_data: bytes) -> Dict[str, Any]:
    """
    Unpack binary ZONB data back to ZONJ (JSON) structure.
    
    Args:
        binary_data: Binary packed ZONB data
        
    Returns:
        Dictionary representation of unpacked data
        
    Example:
        >>> binary = pack_zonj({"type": "room"})
        >>> data = unpack_zonb(binary)
        >>> data["type"]
        'room'
    """
    if len(binary_data) < 4 or binary_data[:4] != ZONB_MAGIC:
        raise ValueError("Invalid ZONB magic header")
    
    ptr = 4
    result = {}

    while ptr < len(binary_data):
        # Read field_id
        field_id = binary_data[ptr]
        ptr += 1
        
        field_name = REVERSE_FIELD_IDS.get(field_id, f"field_{field_id}")
        
        # Read value
        value, ptr = read_value(binary_data, ptr)
        result[field_name] = value

    return result
