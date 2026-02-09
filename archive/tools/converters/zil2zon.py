#!/usr/bin/env python3
"""
ZIL to ZON Converter

Parses Zork Implementation Language (ZIL) files and converts them to ZON format.

ZIL is a LISP-like language using S-expressions:
    <ROOM LIVING-ROOM (DESC "...") (FLAGS LIGHT)>

ZON is JSON-based declarative memory:
    {"type": "room", "id": "LIVING-ROOM", ...}

Usage:
    python3 zil2zon.py input.zil output.zonj.json
"""

import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple


class ZILParser:
    """Parse ZIL S-expressions into Python structures."""
    
    def __init__(self):
        self.tokens = []
        self.position = 0
    
    def tokenize(self, text: str) -> List[str]:
        """Break ZIL source into tokens."""
        # Remove comments
        text = re.sub(r';.*$', '', text, flags=re.MULTILINE)
        
        # Tokenize
        pattern = r'[<>()]|"[^"]*"|[^\s<>()"]+'
        tokens = re.findall(pattern, text)
        
        return tokens
    
    def parse(self, text: str) -> List[Any]:
        """Parse ZIL text into nested structures."""
        self.tokens = self.tokenize(text)
        self.position = 0
        
        expressions = []
        while self.position < len(self.tokens):
            expr = self.parse_expression()
            if expr is not None:
                expressions.append(expr)
        
        return expressions
    
    def parse_expression(self) -> Any:
        """Parse a single S-expression."""
        if self.position >= len(self.tokens):
            return None
        
        token = self.tokens[self.position]
        
        if token == '<':
            # Start of form
            self.position += 1
            return self.parse_form()
        
        elif token == '(':
            # Start of list
            self.position += 1
            return self.parse_list()
        
        elif token in ('>', ')'):
            # End markers
            self.position += 1
            return None
        
        else:
            # Atom
            self.position += 1
            return self.parse_atom(token)
    
    def parse_form(self) -> Dict[str, Any]:
        """Parse a <FORM ...> structure."""
        form_type = self.tokens[self.position]
        self.position += 1
        
        form_name = self.tokens[self.position]
        self.position += 1
        
        properties = {}
        
        while self.position < len(self.tokens) and self.tokens[self.position] != '>':
            prop = self.parse_expression()
            if isinstance(prop, list) and len(prop) >= 2:
                key = prop[0]
                value = prop[1:] if len(prop) > 2 else prop[1]
                properties[key] = value
        
        if self.position < len(self.tokens):
            self.position += 1  # Skip '>'
        
        return {
            'type': form_type.lower(),
            'name': form_name,
            'properties': properties
        }
    
    def parse_list(self) -> List[Any]:
        """Parse a (...) list."""
        items = []
        
        while self.position < len(self.tokens) and self.tokens[self.position] != ')':
            item = self.parse_expression()
            if item is not None:
                items.append(item)
        
        if self.position < len(self.tokens):
            self.position += 1  # Skip ')'
        
        return items
    
    def parse_atom(self, token: str) -> Any:
        """Parse an atomic value."""
        # String
        if token.startswith('"'):
            return token.strip('"')
        
        # Number
        try:
            if '.' in token:
                return float(token)
            else:
                return int(token)
        except ValueError:
            pass
        
        # Symbol
        return token


class ZONConverter:
    """Convert parsed ZIL structures to ZON format."""
    
    def convert_room(self, zil_form: Dict) -> Dict[str, Any]:
        """Convert ROOM form to ZON."""
        props = zil_form.get('properties', {})
        
        zon = {
            "type": "room",
            "id": zil_form['name'],
        }
        
        # Description
        if 'DESC' in props:
            zon['description'] = props['DESC']
        
        # Flags
        if 'FLAGS' in props:
            flags = props['FLAGS']
            zon['flags'] = flags if isinstance(flags, list) else [flags]
        
        # Exits
        if 'EXITS' in props:
            exits = {}
            exit_list = props['EXITS']
            if isinstance(exit_list, list):
                for i in range(0, len(exit_list), 2):
                    if i + 1 < len(exit_list):
                        direction = exit_list[i].lower()
                        destination = exit_list[i + 1]
                        exits[direction] = destination
            zon['exits'] = exits
        
        return zon
    
    def convert_object(self, zil_form: Dict) -> Dict[str, Any]:
        """Convert OBJECT form to ZON."""
        props = zil_form.get('properties', {})
        
        zon = {
            "type": "object",
            "id": zil_form['name'],
        }
        
        if 'DESC' in props:
            zon['description'] = props['DESC']
        
        if 'FLAGS' in props:
            flags = props['FLAGS']
            zon['flags'] = flags if isinstance(flags, list) else [flags]
        
        return zon
    
    def convert(self, zil_forms: List[Dict]) -> List[Dict[str, Any]]:
        """Convert list of ZIL forms to ZON structures."""
        zon_items = []
        
        for form in zil_forms:
            if not isinstance(form, dict):
                continue
            
            form_type = form.get('type', '').upper()
            
            if form_type == 'ROOM':
                zon_items.append(self.convert_room(form))
            elif form_type == 'OBJECT':
                zon_items.append(self.convert_object(form))
            # Add more form types as needed
        
        return zon_items


def main():
    if len(sys.argv) != 3:
        print("Usage: zil2zon.py <input.zil> <output.zonj.json>")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found")
        sys.exit(1)
    
    # Read ZIL source
    print(f"Reading {input_path}...")
    with open(input_path, 'r') as f:
        zil_source = f.read()
    
    # Parse
    print("Parsing ZIL...")
    parser = ZILParser()
    zil_forms = parser.parse(zil_source)
    
    # Convert
    print("Converting to ZON...")
    converter = ZONConverter()
    zon_items = converter.convert(zil_forms)
    
    # Write output
    print(f"Writing {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(zon_items, f, indent=2)
    
    print(f"✅ Converted {len(zon_items)} items")
    print(f"   {input_path} → {output_path}")


if __name__ == "__main__":
    main()
