#!/usr/bin/env python3
"""
ZON Binary Validator

Validates .zonb files against the ZON Format Specification v1.0
Ensures compliance independent of implementation.

Usage:
    python3 zon_validator.py file.zonb
"""

import sys
import struct
from pathlib import Path
from typing import Tuple, List, Dict, Any

# Constants from ZON_FORMAT.md
ZONB_MAGIC = b'ZONB'
ZONB_VERSION = 0x01

TYPE_INT = 0x10
TYPE_BOOL = 0x11
TYPE_STRING = 0x12
TYPE_ARRAY = 0x13
TYPE_BLOCK = 0x14
TYPE_FLOAT = 0x15
TYPE_NULL = 0x16

VALID_TYPE_MARKERS = {TYPE_INT, TYPE_BOOL, TYPE_STRING, TYPE_ARRAY, TYPE_BLOCK, TYPE_FLOAT, TYPE_NULL}

# Field IDs (from spec)
KNOWN_FIELD_IDS = {
    0x01: "type",
    0x02: "name",
    0x03: "value",
    0x04: "children",
    0x05: "position",
    0x06: "compress",
    0x07: "id",
    0x08: "condition",
    0x09: "requires",
    0x0A: "effect",
    0x0B: "metadata",
    0x0C: "description",
    0x0D: "flags",
    0x0E: "exits",
    0x0F: "flag",
    0x17: "time",
    0x18: "action",
    0x19: "created",
}


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class ZONValidator:
    """Validates ZONB files against specification."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.byte_position = 0
    
    def error(self, message: str):
        """Record an error."""
        self.errors.append(f"[Byte {self.byte_position}] {message}")
    
    def warning(self, message: str):
        """Record a warning."""
        self.warnings.append(f"[Byte {self.byte_position}] {message}")
    
    def validate_file(self, filepath: Path) -> bool:
        """
        Validate a ZONB file.
        
        Returns:
            True if valid, False otherwise
        """
        self.errors = []
        self.warnings = []
        self.byte_position = 0
        
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            
            if len(data) < 8:
                self.error(f"File too short: {len(data)} bytes (minimum 8 required)")
                return False
            
            # Validate header
            if not self.validate_header(data):
                return False
            
            # Validate data blocks
            self.byte_position = 8
            if not self.validate_data_blocks(data[8:]):
                return False
            
            return len(self.errors) == 0
            
        except Exception as e:
            self.error(f"Exception during validation: {e}")
            return False
    
    def validate_header(self, data: bytes) -> bool:
        """Validate ZONB header (first 8 bytes)."""
        # Check magic
        magic = data[0:4]
        if magic != ZONB_MAGIC:
            self.error(f"Invalid magic header: {magic} (expected {ZONB_MAGIC})")
            return False
        
        # Check version
        version = data[4]
        if version != ZONB_VERSION:
            self.error(f"Unsupported version: 0x{version:02x} (expected 0x{ZONB_VERSION:02x})")
            return False
        
        # Check flags (must be 0x00)
        flags = data[5]
        if flags != 0x00:
            self.warning(f"Non-zero flags byte: 0x{flags:02x}")
        
        # Check reserved (must be 0x0000)
        reserved = struct.unpack('>H', data[6:8])[0]
        if reserved != 0x0000:
            self.warning(f"Non-zero reserved bytes: 0x{reserved:04x}")
        
        return True
    
    def validate_data_blocks(self, data: bytes) -> bool:
        """Validate data blocks."""
        ptr = 0
        
        while ptr < len(data):
            # Read field ID
            if ptr >= len(data):
                break
            
            field_id = data[ptr]
            ptr += 1
            
            # Validate field ID range
            if field_id in KNOWN_FIELD_IDS:
                pass  # Known field
            elif 0x80 <= field_id <= 0xFF:
                self.warning(f"Custom field ID: 0x{field_id:02x}")
            else:
                self.error(f"Invalid field ID: 0x{field_id:02x}")
                return False
            
            # Read and validate value
            old_ptr = ptr
            ptr, valid = self.validate_value(data, ptr)
            
            if not valid:
                return False
            
            if ptr <= old_ptr:
                self.error(f"Parsing did not advance (stuck at byte {ptr})")
                return False
        
        return True
    
    def validate_value(self, data: bytes, ptr: int) -> Tuple[int, bool]:
        """
        Validate a single value.
        
        Returns:
            (new_ptr, is_valid)
        """
        if ptr >= len(data):
            self.error("Unexpected end of data")
            return ptr, False
        
        type_marker = data[ptr]
        ptr += 1
        
        if type_marker not in VALID_TYPE_MARKERS:
            self.error(f"Invalid type marker: 0x{type_marker:02x}")
            return ptr, False
        
        if type_marker == TYPE_INT:
            if ptr + 4 > len(data):
                self.error("Truncated int32")
                return ptr, False
            ptr += 4
        
        elif type_marker == TYPE_FLOAT:
            if ptr + 4 > len(data):
                self.error("Truncated float32")
                return ptr, False
            ptr += 4
        
        elif type_marker == TYPE_BOOL:
            if ptr >= len(data):
                self.error("Truncated bool")
                return ptr, False
            bool_val = data[ptr]
            if bool_val not in (0x00, 0x01):
                self.warning(f"Non-standard bool value: 0x{bool_val:02x}")
            ptr += 1
        
        elif type_marker == TYPE_STRING:
            if ptr + 2 > len(data):
                self.error("Truncated string length")
                return ptr, False
            
            strlen = struct.unpack('>H', data[ptr:ptr+2])[0]
            ptr += 2
            
            if ptr + strlen > len(data):
                self.error(f"Truncated string (expected {strlen} bytes)")
                return ptr, False
            
            # Validate UTF-8
            try:
                data[ptr:ptr+strlen].decode('utf-8')
            except UnicodeDecodeError as e:
                self.error(f"Invalid UTF-8 in string: {e}")
                return ptr, False
            
            ptr += strlen
        
        elif type_marker == TYPE_ARRAY:
            if ptr + 2 > len(data):
                self.error("Truncated array count")
                return ptr, False
            
            count = struct.unpack('>H', data[ptr:ptr+2])[0]
            ptr += 2
            
            for i in range(count):
                # Skip field_id (0x00 for array items)
                if ptr >= len(data):
                    self.error(f"Truncated array at item {i}")
                    return ptr, False
                ptr += 1
                
                ptr, valid = self.validate_value(data, ptr)
                if not valid:
                    return ptr, False
        
        elif type_marker == TYPE_BLOCK:
            if ptr + 2 > len(data):
                self.error("Truncated dict count")
                return ptr, False
            
            count = struct.unpack('>H', data[ptr:ptr+2])[0]
            ptr += 2
            
            for i in range(count):
                # Read field_id
                if ptr >= len(data):
                    self.error(f"Truncated dict at entry {i}")
                    return ptr, False
                ptr += 1
                
                # Read value
                ptr, valid = self.validate_value(data, ptr)
                if not valid:
                    return ptr, False
        
        elif type_marker == TYPE_NULL:
            pass  # No data follows
        
        return ptr, True
    
    def print_report(self):
        """Print validation report."""
        if self.errors:
            print(f"\n❌ VALIDATION FAILED ({len(self.errors)} errors)")
            for error in self.errors:
                print(f"  ERROR: {error}")
        else:
            print(f"\n✅ VALIDATION PASSED")
        
        if self.warnings:
            print(f"\n⚠️  {len(self.warnings)} warnings:")
            for warning in self.warnings:
                print(f"  WARN: {warning}")


def main():
    if len(sys.argv) != 2:
        print("Usage: zon_validator.py <file.zonb>")
        sys.exit(1)
    
    filepath = Path(sys.argv[1])
    
    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        sys.exit(1)
    
    print(f"Validating: {filepath}")
    print(f"Size: {filepath.stat().st_size} bytes")
    
    validator = ZONValidator()
    is_valid = validator.validate_file(filepath)
    
    validator.print_report()
    
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
