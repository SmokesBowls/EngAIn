#!/usr/bin/env python3
"""
ZW Parser - Unified parser for ZiegelWagga format
Handles both dialects:
  1. Brace-based S-expression: {container {type object} {id CHEST} ...}
  2. Indentation-based packets: ZW-REQUEST: / SCOPE: / CONTEXT: / ...

Place in: godotengain/engainos/core/zw/zw_parser.py

Public API:
    parse_zw(text: str) -> dict
"""

import re
import json
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# DIALECT DETECTION
# ============================================================================

def parse_zw(text: str) -> dict:
    """
    Parse ZW content - auto-detects dialect.

    Args:
        text: Raw ZW string (brace-format or indent-format)

    Returns:
        dict representation of the ZW content

    Raises:
        ZWParseError on malformed input
    """
    text = text.strip()
    if not text:
        return {}

    # Detect dialect
    if text.startswith("{"):
        return _parse_brace(text)
    elif re.match(r'^ZW-\w+:', text) or re.match(r'^\w[\w_-]*:', text):
        return _parse_indent(text)
    elif text.startswith("{") or "{" in text.split("\n")[0]:
        return _parse_brace(text)
    else:
        # Fallback: try indent, then brace
        try:
            return _parse_indent(text)
        except Exception:
            return _parse_brace(text)


class ZWParseError(Exception):
    """Raised when ZW content cannot be parsed."""
    pass


# ============================================================================
# DIALECT 1: BRACE-BASED S-EXPRESSION PARSER
# {container {type object} {id CHEST} {flags [OPENBIT TRANSBIT]} ...}
# ============================================================================

class _BraceTokenizer:
    """Tokenize brace-format ZW into a stream of tokens."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.length = len(text)

    def peek(self) -> Optional[str]:
        self._skip_whitespace()
        if self.pos >= self.length:
            return None
        return self.text[self.pos]

    def _skip_whitespace(self):
        while self.pos < self.length and self.text[self.pos] in ' \t\n\r':
            self.pos += 1

    def read_token(self) -> Optional[str]:
        """Read next token: {, }, [, ], quoted string, or bare word."""
        self._skip_whitespace()
        if self.pos >= self.length:
            return None

        ch = self.text[self.pos]

        # Single-char delimiters
        if ch in '{}[]':
            self.pos += 1
            return ch

        # Quoted string
        if ch == '"':
            return self._read_quoted()

        # Bare word / number / boolean
        return self._read_bare()

    def _read_quoted(self) -> str:
        """Read a double-quoted string, handling escapes."""
        assert self.text[self.pos] == '"'
        self.pos += 1
        start = self.pos
        result = []

        while self.pos < self.length:
            ch = self.text[self.pos]
            if ch == '\\' and self.pos + 1 < self.length:
                next_ch = self.text[self.pos + 1]
                if next_ch == '"':
                    result.append('"')
                    self.pos += 2
                    continue
                elif next_ch == 'n':
                    result.append('\n')
                    self.pos += 2
                    continue
                elif next_ch == 't':
                    result.append('\t')
                    self.pos += 2
                    continue
                elif next_ch == '\\':
                    result.append('\\')
                    self.pos += 2
                    continue
            if ch == '"':
                self.pos += 1
                return ''.join(result)
            result.append(ch)
            self.pos += 1

        raise ZWParseError(f"Unterminated string starting at position {start - 1}")

    def _read_bare(self) -> str:
        """Read a bare word (unquoted value)."""
        start = self.pos
        while self.pos < self.length and self.text[self.pos] not in ' \t\n\r{}[]':
            self.pos += 1
        return self.text[start:self.pos]


def _coerce_value(raw: str) -> Any:
    """Coerce a bare token to int, float, bool, None, or keep as str."""
    if raw.lower() == 'true':
        return True
    if raw.lower() == 'false':
        return False
    if raw.lower() == 'null' or raw.lower() == 'none':
        return None
    # Integer
    try:
        return int(raw)
    except ValueError:
        pass
    # Float
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def _parse_brace(text: str) -> dict:
    """Parse brace-format ZW into a dict."""
    tok = _BraceTokenizer(text)
    result = _parse_brace_value(tok)

    # If top-level is a single block, return it
    if isinstance(result, dict):
        return result
    # If multiple top-level blocks, wrap in list
    if isinstance(result, list):
        # Check for more top-level blocks
        extras = []
        while tok.peek() is not None:
            extras.append(_parse_brace_value(tok))
        if extras:
            return {"_blocks": [result] + extras}
        if len(result) == 1 and isinstance(result[0], dict):
            return result[0]
        return {"_items": result}
    return {"_value": result}


def _parse_brace_value(tok: _BraceTokenizer) -> Any:
    """Parse one value from the token stream."""
    ch = tok.peek()
    if ch is None:
        return None

    if ch == '{':
        return _parse_brace_block(tok)
    if ch == '[':
        return _parse_brace_array(tok)

    token = tok.read_token()
    return _coerce_value(token)


def _parse_brace_block(tok: _BraceTokenizer) -> dict:
    """
    Parse a {key ...} block.

    Pattern: {tag {k1 v1} {k2 v2} ...}
    The first bare word after { is the block tag/type.
    Subsequent {k v} pairs become dict entries.
    """
    opening = tok.read_token()
    assert opening == '{'

    result = {}

    # Read the block tag (first bare word)
    first = tok.peek()
    if first is None or first == '}':
        tok.read_token()  # consume }
        return result

    if first != '{' and first != '[':
        tag = tok.read_token()
        result['_tag'] = _coerce_value(tag)

    # Read key-value pairs until }
    while True:
        ch = tok.peek()
        if ch is None:
            raise ZWParseError("Unexpected end of input inside { } block")
        if ch == '}':
            tok.read_token()
            break

        if ch == '{':
            # Nested {key value} pair
            inner = _parse_brace_kv_or_block(tok)
            if isinstance(inner, tuple):
                key, val = inner
                result[key] = val
            elif isinstance(inner, dict):
                # Anonymous nested block — merge or append
                tag = inner.get('_tag', None)
                if tag and tag not in result:
                    # Promote: {item {id X}} → result['item'] = {id: X, ...}
                    inner_copy = {k: v for k, v in inner.items() if k != '_tag'}
                    result[tag] = inner_copy if inner_copy else inner
                else:
                    result.setdefault('_children', []).append(inner)
        elif ch == '[':
            arr = _parse_brace_array(tok)
            result.setdefault('_items', []).extend(arr)
        else:
            # Bare value inside block (uncommon)
            token = tok.read_token()
            result.setdefault('_values', []).append(_coerce_value(token))

    return result


def _parse_brace_kv_or_block(tok: _BraceTokenizer) -> Any:
    """
    Parse {key value} — returns (key, value) tuple if it's a simple pair,
    or a full dict if it's a nested block.
    """
    opening = tok.read_token()
    assert opening == '{'

    first_peek = tok.peek()
    if first_peek is None or first_peek == '}':
        tok.read_token()
        return {}

    # Read the key / tag
    if first_peek in '{[':
        # No bare key — it's a nested structure
        val = _parse_brace_value(tok)
        # Consume until }
        while tok.peek() != '}':
            if tok.peek() is None:
                break
            _parse_brace_value(tok)  # discard? shouldn't happen often
        tok.read_token()  # consume }
        if isinstance(val, dict):
            return val
        return ('_anon', val)

    key = tok.read_token()

    # Check what follows
    next_peek = tok.peek()

    if next_peek == '}':
        # {key} with no value — treat as flag
        tok.read_token()
        return (key, True)

    # Read the value
    value = _parse_brace_value(tok)

    # There might be more pairs inside (nested block style)
    if tok.peek() not in ('}', None):
        # Multi-value block: {tag {k1 v1} {k2 v2}}
        # Reinterpret: key is tag, value is first child, gather rest
        block = {'_tag': key}
        if isinstance(value, tuple):
            block[value[0]] = value[1]
        elif isinstance(value, dict):
            block.update(value)
        else:
            block['_first'] = value

        while tok.peek() not in ('}', None):
            child = _parse_brace_value(tok)
            if isinstance(child, tuple):
                block[child[0]] = child[1]
            elif isinstance(child, dict):
                tag = child.get('_tag')
                if tag:
                    child_clean = {k: v for k, v in child.items() if k != '_tag'}
                    block[tag] = child_clean if child_clean else True
                else:
                    block.setdefault('_children', []).append(child)
            else:
                block.setdefault('_values', []).append(child)

        tok.read_token()  # consume }
        return block

    # Simple {key value}
    tok.read_token()  # consume }

    if isinstance(value, dict) and '_tag' in value:
        # {key {nested_tag ...}} — keep nested structure
        return (key, value)

    return (key, value)


def _parse_brace_array(tok: _BraceTokenizer) -> list:
    """Parse [...] array."""
    opening = tok.read_token()
    assert opening == '['

    items = []
    while True:
        ch = tok.peek()
        if ch is None:
            raise ZWParseError("Unexpected end of input inside [ ] array")
        if ch == ']':
            tok.read_token()
            break
        items.append(_parse_brace_value(tok))

    return items


# ============================================================================
# DIALECT 2: INDENTATION-BASED PACKET PARSER
# ZW-REQUEST:
#   SCOPE: Player
#   CONTEXT:
#     - Location: Kitchen
#     - Inventory: [BrassKey, Flashlight]
#   ACTION: open Oven
# ============================================================================

def _parse_indent(text: str) -> dict:
    """Parse indentation-based ZW packets."""
    lines = text.splitlines()
    result = {}
    current_section = None
    section_content = []
    base_indent = 0

    for raw_line in lines:
        # Skip empty lines
        if not raw_line.strip():
            continue

        line = raw_line.rstrip()
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        # Top-level packet header: ZW-REQUEST: or ZW-RESPONSE:
        pkt_match = re.match(r'^(ZW-\w+):\s*$', stripped)
        if pkt_match:
            result['_packet_type'] = pkt_match.group(1)
            base_indent = indent
            continue

        # Section header with inline value: KEY: value
        kv_match = re.match(r'^(\w[\w_\-]*)\s*:\s*(.+)$', stripped)
        if kv_match and not stripped.startswith('- '):
            key = kv_match.group(1)
            value = kv_match.group(2).strip()

            # Flush previous section
            if current_section and section_content:
                result[current_section] = _process_indent_section(section_content)
                section_content = []

            result[key] = _parse_indent_value(value)
            current_section = None
            continue

        # Section header without value: KEY:
        section_match = re.match(r'^(\w[\w_\-]*)\s*:\s*$', stripped)
        if section_match and indent <= base_indent + 2:
            # Flush previous section
            if current_section and section_content:
                result[current_section] = _process_indent_section(section_content)
                section_content = []

            current_section = section_match.group(1)
            continue

        # Content under a section
        if current_section is not None:
            section_content.append(stripped)
            continue

        # Standalone key: value at root level
        if ':' in stripped and not stripped.startswith('-'):
            parts = stripped.split(':', 1)
            key = parts[0].strip()
            value = parts[1].strip()
            if key:
                result[key] = _parse_indent_value(value)

    # Flush final section
    if current_section and section_content:
        result[current_section] = _process_indent_section(section_content)

    return result


def _process_indent_section(lines: List[str]) -> Any:
    """Process lines under an indented section into a list or dict."""
    items = []
    dict_mode = True

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith('- '):
            content = line[2:].strip()

            # Key-value inside list: - Location: Kitchen
            if ':' in content and not content.startswith('['):
                parts = content.split(':', 1)
                key = parts[0].strip()
                value = _parse_indent_value(parts[1].strip())
                items.append({key: value})
            else:
                dict_mode = False
                items.append(_parse_indent_value(content))
        elif ':' in line:
            parts = line.split(':', 1)
            key = parts[0].strip()
            value = _parse_indent_value(parts[1].strip())
            items.append({key: value})
        else:
            dict_mode = False
            items.append(_parse_indent_value(line))

    # If all items are single-key dicts, merge into one dict
    if dict_mode and items and all(isinstance(i, dict) and len(i) == 1 for i in items):
        merged = {}
        for item in items:
            merged.update(item)
        return merged

    # If single item, unwrap
    if len(items) == 1:
        return items[0]

    return items


def _parse_indent_value(raw: str) -> Any:
    """Parse a scalar value from indent-format ZW."""
    raw = raw.strip()

    if not raw:
        return ""

    # Bracketed inline array: [BrassKey, Flashlight]
    if raw.startswith('[') and raw.endswith(']'):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        # Split on commas, strip each
        return [_coerce_value(item.strip()) for item in inner.split(',')]

    # Quoted string
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]

    # Coerce to typed value
    return _coerce_value(raw)


# ============================================================================
# CONVENIENCE / COMPAT
# ============================================================================

def parse_zw_file(filepath: str) -> dict:
    """Parse a .zw file from disk."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return parse_zw(f.read())


def zw_to_json(text: str, indent: int = 2) -> str:
    """Parse ZW and return JSON string."""
    return json.dumps(parse_zw(text), indent=indent, ensure_ascii=False)


# Allow running as a quick CLI tool
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        for path in sys.argv[1:]:
            result = parse_zw_file(path)
            print(json.dumps(result, indent=2))
    else:
        # Interactive: read from stdin
        print("Paste ZW content (Ctrl+D to parse):")
        text = sys.stdin.read()
        result = parse_zw(text)
        print(json.dumps(result, indent=2))
