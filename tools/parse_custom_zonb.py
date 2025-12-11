#!/usr/bin/env python3
import sys
import struct
import binascii

MAGIC = b"ZONB"

TYPE_STRING = 0x12
TYPE_INT    = 0x13
TYPE_BOOL   = 0x14

def read_value(data, ptr):
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

    if type_tag == TYPE_STRING:
        try:
            return ("string", raw.decode("utf-8")), ptr
        except UnicodeDecodeError:
            return ("string", raw.decode("utf-8", errors="replace")), ptr
    elif type_tag == TYPE_INT:
        val = int.from_bytes(raw, "big", signed=False)
        return ("int", val), ptr
    elif type_tag == TYPE_BOOL:
        val = any(b != 0 for b in raw)
        return ("bool", val), ptr
    else:
        return (f"unknown(0x{type_tag:02x})", raw), ptr

def parse(path):
    with open(path, "rb") as f:
        data = f.read()

    print(f"File: {path}")
    print("Hex dump (first 128 bytes):")
    print(binascii.hexlify(data[:128], b" ").decode())

    if len(data) < 4 or data[:4] != MAGIC:
        print("ERROR: Not ZONB")
        return

    print("Magic: ZONB")
    print("Format: EngAIn legacy ZONB (no global version)")
    ptr = 4
    field_index = 0

    while ptr < len(data):
        field_index += 1
        field_id = data[ptr]; ptr += 1

        try:
            (t, val), ptr = read_value(data, ptr)
        except Exception as e:
            print(f"Error at field #{field_index}, offset 0x{ptr:04x}: {e}")
            break

        print(f"[#{field_index}] id={field_id}  {t}: {val}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: parse_custom_zonb.py file.zonb")
        sys.exit(1)
    parse(sys.argv[1])
