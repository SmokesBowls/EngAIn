"""ZON Binary Pack/Unpack (ZONB)"""

import json
import struct
from typing import Any, Tuple

MAGIC = b"ZONB"
VERSION = 1

TYPE_NULL = 0x00
TYPE_BOOL = 0x01
TYPE_INT  = 0x02
TYPE_FLOAT= 0x03
TYPE_STRING=0x04
TYPE_ARRAY= 0x05
TYPE_DICT = 0x06
TYPE_ROOT_ARRAY = 0x07  # reserved

FIELD_IDS = {
    "type": 0x01,
    "id": 0x02,
    "name": 0x03,
    "value": 0x04,
    "description": 0x05,
    "conditions": 0x06,
    "actions": 0x07,
    "triggers": 0x08,
    "enabled": 0x09,
    "priority": 0x0A,
    "tags": 0x0B,
    "metadata": 0x0C,
    "timestamp": 0x0D,
    "version": 0x0E,
    "author": 0x0F,
    "source": 0x10,
    "target": 0x11,
    "data": 0x12,
    "children": 0x13,
    "parent": 0x14,
    "ref": 0x15,
    "refs": 0x16,
    "content": 0x17,
    "format": 0x18,
    "encoding": 0x19,
    "size": 0x1A,
    "count": 0x1B,
    "index": 0x1C,
    "key": 0x1D,
    "label": 0x1E,
    "status": 0x1F,
    "state": 0x20,
    "config": 0x21,
    "settings": 0x22,
    "options": 0x23,
    "params": 0x24,
    "weight": 0x25,
    "root": 0x26,
    "all_of": 0x27,
    "any_of": 0x28,
    "nested": 0x29,
}
REVERSE_FIELD_IDS = {v: k for k, v in FIELD_IDS.items()}


def write_varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("Negative varint not supported")
    out = bytearray()
    while value > 0x7F:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value & 0x7F)
    return bytes(out)


def read_varint(data: bytes, ptr: int) -> Tuple[int, int]:
    result = 0
    shift = 0
    while True:
        if ptr >= len(data):
            raise ValueError("Truncated varint")
        b = data[ptr]
        ptr += 1
        result |= (b & 0x7F) << shift
        if (b & 0x80) == 0:
            return result, ptr
        shift += 7


class _FieldRegistry:
    def __init__(self):
        self.next_id = 0x80
        self.name_to_id = {}
        self.id_to_name = {}

    def get_id_for_name(self, name: str) -> int:
        if name in FIELD_IDS:
            return FIELD_IDS[name]
        if name in self.name_to_id:
            return self.name_to_id[name]
        fid = self.next_id
        self.next_id += 1
        self.name_to_id[name] = fid
        self.id_to_name[fid] = name
        return fid

    def get_name_for_id(self, fid: int) -> str:
        if fid in REVERSE_FIELD_IDS:
            return REVERSE_FIELD_IDS[fid]
        if fid in self.id_to_name:
            return self.id_to_name[fid]
        return f"field_{fid}"

    def encode_table(self) -> bytes:
        items = list(self.name_to_id.items())
        buf = bytearray()
        buf += write_varint(len(items))
        for name, fid in items:
            nb = name.encode("utf-8")
            buf += write_varint(fid)
            buf += write_varint(len(nb))
            buf += nb
        return bytes(buf)

    def decode_table(self, table: bytes) -> None:
        ptr = 0
        count, ptr = read_varint(table, ptr)
        for _ in range(count):
            fid, ptr = read_varint(table, ptr)
            nlen, ptr = read_varint(table, ptr)
            name = table[ptr:ptr+nlen].decode("utf-8")
            ptr += nlen
            self.id_to_name[fid] = name


def _write_value(value: Any, reg: _FieldRegistry) -> bytes:
    if value is None:
        return bytes([TYPE_NULL])

    if isinstance(value, bool):
        return bytes([TYPE_BOOL, 1 if value else 0])

    if isinstance(value, int) and not isinstance(value, bool):
        return bytes([TYPE_INT]) + write_varint(value)

    if isinstance(value, float):
        # 64-bit float for exact JSON-ish roundtrip
        return bytes([TYPE_FLOAT]) + struct.pack("<d", value)

    if isinstance(value, str):
        b = value.encode("utf-8")
        return bytes([TYPE_STRING]) + write_varint(len(b)) + b

    if isinstance(value, list):
        out = bytearray([TYPE_ARRAY])
        out += write_varint(len(value))
        for item in value:
            out += _write_value(item, reg)
        return bytes(out)

    if isinstance(value, dict):
        out = bytearray([TYPE_DICT])
        out += write_varint(len(value))
        for k, v in value.items():
            fid = reg.get_id_for_name(str(k))
            out += write_varint(fid)
            out += _write_value(v, reg)
        return bytes(out)

    return _write_value(str(value), reg)


def _read_value(data: bytes, ptr: int, reg: _FieldRegistry) -> Tuple[Any, int]:
    if ptr >= len(data):
        raise ValueError("Unexpected EOF while reading value")
    t = data[ptr]
    ptr += 1

    if t == TYPE_NULL:
        return None, ptr

    if t == TYPE_BOOL:
        return bool(data[ptr]), ptr + 1

    if t == TYPE_INT:
        return read_varint(data, ptr)

    if t == TYPE_FLOAT:
        return struct.unpack("<d", data[ptr:ptr+8])[0], ptr + 8

    if t == TYPE_STRING:
        n, ptr = read_varint(data, ptr)
        s = data[ptr:ptr+n].decode("utf-8")
        return s, ptr + n

    if t == TYPE_ARRAY or t == TYPE_ROOT_ARRAY:
        n, ptr = read_varint(data, ptr)
        arr = []
        for _ in range(n):
            v, ptr = _read_value(data, ptr, reg)
            arr.append(v)
        return arr, ptr

    if t == TYPE_DICT:
        n, ptr = read_varint(data, ptr)
        d = {}
        for _ in range(n):
            fid, ptr = read_varint(data, ptr)
            key = reg.get_name_for_id(fid)
            v, ptr = _read_value(data, ptr, reg)
            d[key] = v
        return d, ptr

    raise ValueError(f"Unknown type byte 0x{t:02x} at position {ptr-1}")


def pack_zonj(obj: Any) -> bytes:
    reg = _FieldRegistry()
    body = _write_value(obj, reg)
    table = reg.encode_table()
    header = bytearray()
    header += MAGIC
    header.append(VERSION)
    header += write_varint(len(table))
    header += table
    return bytes(header) + body


def unpack_zonb(blob: bytes, auto_unwrap: bool = True) -> Any:
    if len(blob) < 6:
        raise ValueError("Data too short")
    if blob[:4] != MAGIC:
        raise ValueError("Bad magic")
    if blob[4] != VERSION:
        raise ValueError(f"Unsupported version {blob[4]}")

    ptr = 5
    table_len, ptr = read_varint(blob, ptr)
    table = blob[ptr:ptr+table_len]
    ptr += table_len

    reg = _FieldRegistry()
    reg.decode_table(table)

    value, ptr = _read_value(blob, ptr, reg)
    return value

def pack_to_zonb(obj) -> bytes:
    """Backward-compatible helper: pack Python object to ZONB bytes."""
    # If your pack_zonj already returns bytes:
    return pack_zonj(obj)

def unpack_from_zonb(data: bytes):
    """Backward-compatible helper: unpack ZONB bytes to Python object."""
    return unpack_zonb(data)

def pack_file(input_path: str, output_path: str) -> int:
    with open(input_path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    blob = pack_zonj(obj)
    with open(output_path, "wb") as f:
        f.write(blob)
    return len(blob)


def unpack_file(input_path: str, output_path: str, auto_unwrap: bool = True) -> Any:
    with open(input_path, "rb") as f:
        blob = f.read()
    obj = unpack_zonb(blob, auto_unwrap=auto_unwrap)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    return obj
