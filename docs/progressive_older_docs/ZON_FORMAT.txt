# ZON Binary Format Specification v1.0

**Status**: Draft  
**Date**: 2025-11-27  
**Authors**: EngAIn Project

---

## Overview

ZON (ZW Object Notation) Binary Format is a platform-agnostic, type-safe binary serialization format designed for efficient storage and transmission of game logic, narrative data, and AI-readable semantic structures.

---

## Design Principles

1. **Platform Independence**: Format is defined independent of implementation language
2. **Type Safety**: Explicit type markers for all values
3. **Versioning**: Built-in version byte for format evolution
4. **Efficiency**: Compact binary representation with minimal overhead
5. **Semantic Clarity**: Field IDs map to human-readable names

---

## Binary Structure

### File Header

```
Offset  Size  Type     Description
------  ----  -------  -----------
0x00    4     ASCII    Magic: "ZONB"
0x04    1     uint8    Format version (currently 0x01)
0x05    1     uint8    Flags (reserved, must be 0x00)
0x06    2     uint16   Reserved (must be 0x0000)
0x08    ...   ...      Data blocks
```

### Data Block Structure

Each data block consists of:
```
[Field ID: 1 byte][Type Marker: 1 byte][Value Data: variable]
```

---

## Type Markers

Type markers occupy the range `0x10-0x1F`:

| Marker | Type    | Size     | Encoding                          |
|--------|---------|----------|-----------------------------------|
| 0x10   | int32   | 4 bytes  | Big-endian signed integer         |
| 0x11   | bool    | 1 byte   | 0x00=false, 0x01=true            |
| 0x12   | string  | variable | [length:2][UTF-8 bytes]          |
| 0x13   | array   | variable | [count:2][items...]              |
| 0x14   | dict    | variable | [count:2][key-value pairs...]    |
| 0x15   | float32 | 4 bytes  | Big-endian IEEE 754              |
| 0x16   | null    | 0 bytes  | Null/None value                  |

---

## Field IDs

Field IDs occupy ranges:
- `0x01-0x0F`: Core system fields
- `0x17-0x7F`: Common game fields (avoid 0x10-0x16, reserved for type markers)
- `0x80-0xFF`: Custom/dynamic fields

### Predefined Field IDs

| ID   | Name        | Description                    |
|------|-------------|--------------------------------|
| 0x01 | type        | Entity type identifier         |
| 0x02 | name        | Entity name                    |
| 0x03 | value       | Generic value field            |
| 0x04 | children    | Child entities                 |
| 0x05 | position    | Spatial position               |
| 0x06 | compress    | Compression flag               |
| 0x07 | id          | Unique identifier              |
| 0x08 | condition   | Conditional expression         |
| 0x09 | requires    | Requirement list               |
| 0x0A | effect      | Effect/action list             |
| 0x0B | metadata    | Metadata dictionary            |
| 0x0C | description | Text description               |
| 0x0D | flags       | Flag array                     |
| 0x0E | exits       | Exit/connection dictionary     |
| 0x0F | flag        | Single flag (bool or string)   |
| 0x17 | time        | Time value/constraint          |
| 0x18 | action      | Action identifier              |
| 0x19 | created     | Creation timestamp             |

---

## Value Encoding Details

### Integer (0x10)
```
Bytes:  [type:0x10][b3 b2 b1 b0]
Range:  -2,147,483,648 to 2,147,483,647
Format: Big-endian two's complement
```

### Boolean (0x11)
```
Bytes:  [type:0x11][value]
Values: 0x00 = false, 0x01 = true
```

### String (0x12)
```
Bytes:  [type:0x12][length_hi][length_lo][utf8_bytes...]
Length: 0-65535 bytes (uint16 big-endian)
Encoding: UTF-8
```

### Array (0x13)
```
Bytes:  [type:0x13][count_hi][count_lo][item1...][item2...]...
Count:  0-65535 items (uint16 big-endian)
Items:  Each item is: [field_id:0x00][type][value]
```

### Dictionary (0x14)
```
Bytes:  [type:0x14][count_hi][count_lo][entry1...][entry2...]...
Count:  0-65535 entries (uint16 big-endian)
Entry:  [field_id][type][value]
```

### Float (0x15)
```
Bytes:  [type:0x15][b3 b2 b1 b0]
Format: Big-endian IEEE 754 single-precision
```

### Null (0x16)
```
Bytes:  [type:0x16]
No value data follows
```

---

## Root Structure

A ZONB file contains either:

### Root Dictionary
```
[ZONB][version][flags][reserved]
[field_id][type][value]...
```

### Root Array
```
[ZONB][version][flags][reserved]
[0x00][0x13][count][items...]
```

---

## Version Evolution

### Version 0x01 (Current)
- Initial format specification
- Basic type support (int, bool, string, array, dict, float, null)
- Fixed field ID mappings

### Future Versions (Planned)
- 0x02: Add compression support via 'compress' field
- 0x03: Add extended type markers (int64, float64, binary blobs)
- 0x04: Add schema validation references

**Backward Compatibility Promise:**
- Parsers MUST reject files with unsupported version bytes
- Version byte changes indicate breaking changes
- Minor format additions use flags byte

---

## Example Encoding

### Input (JSON representation):
```json
{
  "type": "room",
  "id": "KITCHEN",
  "description": "A cozy kitchen"
}
```

### Binary Output:
```
Offset  Hex                              Description
------  -------------------------------  -----------
0x00    5A 4F 4E 42                     Magic "ZONB"
0x04    01                               Version 1
0x05    00                               Flags
0x06    00 00                            Reserved
0x08    01                               Field ID: type (0x01)
0x09    12                               Type: string (0x12)
0x0A    00 04                            Length: 4
0x0C    72 6F 6F 6D                      "room"
0x10    07                               Field ID: id (0x07)
0x11    12                               Type: string (0x12)
0x12    00 07                            Length: 7
0x14    4B 49 54 43 48 45 4E             "KITCHEN"
0x1B    0C                               Field ID: description (0x0C)
0x1C    12                               Type: string (0x12)
0x1D    00 0E                            Length: 14
0x1F    41 20 63 6F 7A 79 20 6B...      "A cozy kitchen"
```

---

## Implementation Requirements

### Encoder (Packer)
1. MUST write magic header "ZONB"
2. MUST write version byte 0x01
3. MUST write flags as 0x00
4. MUST write reserved bytes as 0x0000
5. MUST encode all integers as big-endian
6. MUST encode strings as UTF-8
7. MUST use defined type markers
8. MUST handle boolean before integer (bool is subclass of int in Python)

### Decoder (Unpacker)
1. MUST verify magic header is "ZONB"
2. MUST check version byte and reject unknown versions
3. MUST decode all integers as big-endian signed
4. MUST decode strings as UTF-8
5. MUST handle recursive structures (arrays, dicts)
6. MUST map field IDs to names using defined table
7. MUST handle unknown field IDs gracefully (field_N format)

---

## Validation

### Valid ZONB File Checklist
- [ ] Starts with "ZONB" magic (4 bytes)
- [ ] Version byte is 0x01
- [ ] All type markers are in range 0x10-0x16
- [ ] String lengths match actual byte count
- [ ] Array/dict counts match actual item count
- [ ] No truncated values (file size matches expected data)
- [ ] UTF-8 strings are valid
- [ ] Integers fit in int32 range

### Invalid Files
Parsers MUST reject files that:
- Have incorrect magic header
- Have unsupported version byte
- Contain unknown type markers
- Have mismatched lengths/counts
- Are truncated/incomplete

---

## Test Vectors

### Test 1: Simple Integer
```
Input:  {"value": 42}
Bytes:  5A4F4E42 01 00 0000 03 10 0000002A
```

### Test 2: Boolean Array
```
Input:  {"flags": [true, false, true]}
Bytes:  5A4F4E42 01 00 0000 0D 13 0003 00 11 01 00 11 00 00 11 01
```

### Test 3: Nested Dictionary
```
Input:  {"metadata": {"author": "AI", "version": 1}}
Bytes:  5A4F4E42 01 00 0000 0B 14 0002 80 12 0006 417574686F72 ...
```

---

## Conformance

An implementation is **conformant** if it:
1. Passes all test vectors
2. Successfully round-trips all valid inputs
3. Rejects all invalid inputs with clear errors
4. Produces byte-identical output for identical input (deterministic)

---

## References

- **Python Reference Implementation**: `core/zon/zon_binary_pack.py`
- **GDScript Reference Implementation**: `godot/addons/engain/ZONBinary.gd`
- **Test Suite**: `tests/unit/test_zon_pack.py`

---

## Change Log

### v1.0 (2025-11-27)
- Initial specification
- Defined all type markers
- Defined field ID ranges
- Added version byte and evolution plan

---

**This specification is the single source of truth for ZON binary format.**

All implementations MUST conform to this specification, not to each other.
