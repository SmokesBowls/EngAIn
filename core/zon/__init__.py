"""
ZON - ZW Object Notation

4D declarative memory system with binary packing for efficient storage.

Components:
- zon_binary_pack: Pack/unpack .zonj.json ↔ .zonb
- zon_validator: Validate ZON structure and types
- types: ZON type definitions
"""

from .zon_binary_pack import pack_zonj, unpack_zonb

__all__ = ['pack_zonj', 'unpack_zonb']
