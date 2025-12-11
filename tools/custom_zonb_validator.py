#!/usr/bin/env python3
import sys
import struct

MAGIC = b"ZONB"

TYPE_STRING = 0x12
TYPE_INT    = 0x13
TYPE_BOOL   = 0x14

def read_value(data, ptr):
    """Read a single value at ptr according to EngAIn ZONB layout.

    Format:
        [field_id][type_tag][len_hi][len_lo][data...]
    We are called *after* field_id (ptr points at type_tag).
    """
    if ptr + 3 > len(data):
        raise ValueError("Truncated value header")

    type_tag = data[ptr]
    ptr += 1

    length = struct.unpack(">H", data[ptr:ptr+2])[0]
    ptr += 2

    if ptr + length > len(data):
        raise ValueError("Truncated value payload")

    raw = data[ptr:ptr+length]
    ptr += length

    # strings only is your priority; we still decode ints/bools sanely
    if type_tag == TYPE_STRING:
        try:
            return ("string", raw.decode("utf-8")), ptr
        except UnicodeDecodeError:
            return ("string", raw.decode("utf-8", errors="replace")), ptr

    elif type_tag == TYPE_INT:
        # Interpret as big-endian integer of variable length
        val = int.from_bytes(raw, byteorder="big", signed=False)
        return ("int", val), ptr

    elif type_tag == TYPE_BOOL:
        # Any nonzero byte is True
        val = any(b != 0 for b in raw)
        return ("bool", val), ptr

    else:
        # Unknown type, but structurally valid
        return (f"unknown(0x{type_tag:02x})", raw), ptr


def validate(path):
    with open(path, "rb") as f:
        data = f.read()

    if len(data) < 4 or data[:4] != MAGIC:
        print("ERROR: Not a ZONB file (magic mismatch).")
        return

    print(f"File: {path}")
    print("Magic: ZONB")
    print("Format: EngAIn legacy ZONB (no global version byte)")
    ptr = 4
    errors = 0
    field_index = 0

    while ptr < len(data):
        if ptr >= len(data):
            break

        field_index += 1
        field_id = data[ptr]
        ptr += 1

        try:
            (t, value), ptr = read_value(data, ptr)
            print(f"Field #{field_index}  id={field_id}  type={t}  value={value}")
        except Exception as e:
            print(f"Validation error at offset 0x{ptr:04x}: {e}")
            errors += 1
            break

    if errors == 0:
        print("✔ STRUCTURALLY VALID ZONB (EngAIn legacy layout)")
    else:
        print("❌ INVALID / CORRUPTED ZONB STRUCTURE")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: custom_zonb_validator.py file.zonb")
        sys.exit(1)
    validate(sys.argv[1])
