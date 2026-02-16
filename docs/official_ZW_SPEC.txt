# ZW (Ziegel Wagga) Language Specification

**Version:** 0.1  
**Status:** Draft  
**Last Updated:** 2025-11-29
---

**ZW is a semantic data notation built for AI, not humans.** By eliminating JSON's syntactic overhead—colons, comma separators, quoted keys—ZW achieves 25-35% compression while preserving complete semantic meaning. Whether defining game logic, TTS configurations, workflow automation, or calculator operations, ZW's minimal syntax lets AI agents read, write, and reason about declarative systems with dramatically fewer tokens. It's not about making data smaller—it's about making meaning clearer.


---

## 1. Overview

ZW is a semantic data notation designed for AI-readable game logic. It achieves compression through syntax minimalism while preserving complete semantic meaning.

**Design Goals:**
- Eliminate redundant punctuation (colons, quotes on keys, commas)
- Maintain full semantic structure
- Enable direct AI consumption without transformation
- Support declarative game logic representation

**Compression Metrics:**
- ~25% fewer characters vs JSON
- ~11-20% fewer whitespace-delimited tokens
- Estimated 1.5-2x fewer LLM tokens (via BPE tokenization)

---

## 2. Syntax Rules

### 2.1 Blocks

**Definition:** A block is a key-value pair enclosed in braces.

**Syntax:**
```zw
{key value}
{key {nested_key nested_value}}
```

**Rules:**
- Opens with `{`, closes with `}`
- First token after `{` is the **key** (bareword, no quotes required)
- Remaining tokens until `}` are the **value(s)**
- Keys may not contain whitespace or special characters `{}[]"`
- Values may be:
  - Bareword (e.g., `true`, `CHEST`, `42`)
  - Quoted string (e.g., `"a wooden chest"`)
  - Nested block (e.g., `{flags {locked true}}`)
  - Array (e.g., `[OPENBIT TRANSBIT]`)
  - Multiple values (becomes nested object, see §4.1)

**Examples:**
```zw
{type object}                           # Simple key-value
{id CHEST}                              # Bareword value
{description "a wooden chest"}          # Quoted string value
{flags {locked true} {weight 15}}       # Multiple nested blocks
```

### 2.2 Arrays

**Definition:** An ordered collection of values.

**Syntax:**
```zw
[value1 value2 value3]
```

**Rules:**
- Opens with `[`, closes with `]`
- Contains zero or more values separated by whitespace
- Values may be any valid ZW type (barewords, strings, blocks, nested arrays)
- No commas between elements

**Examples:**
```zw
{flags [OPENBIT TRANSBIT LOCKED]}
{inventory [
  {item {id SWORD} {damage 15}}
  {item {id POTION} {healing 50}}
]}
{coordinates [10 20 30]}
```

### 2.3 Values

**Valid Value Types:**

1. **Bareword:** Any sequence without whitespace or special characters
   - Examples: `CHEST`, `true`, `42`, `3.14`, `player_has_key`

2. **Quoted String:** Text enclosed in double quotes
   - Examples: `"a wooden chest"`, `"The door creaks open"`
   - Escape sequences: Currently none (future: `\"`, `\n`, etc.)

3. **Block:** Nested `{key value}` structure

4. **Array:** Bracketed `[...]` collection

---

## 3. Tokenization

### 3.1 Token Delimiters

**Whitespace:** Any sequence of spaces, tabs, or newlines separates tokens.

**Special Characters:** Always separate tokens:
- `{` - Block open
- `}` - Block close
- `[` - Array open
- `]` - Array close

### 3.2 Token Recognition

**Pattern (Regex):**
```regex
[{}\[\]]|"[^"]*"|[^{}\[\]\s]+
```

**Processing:**
1. Match special characters as individual tokens
2. Match quoted strings as single tokens (remove quotes)
3. Match all other non-whitespace sequences as bareword tokens

**Example:**
```zw
{container {id CHEST} {flags [LOCKED]}}
```

**Tokens:**
```
['{', 'container', '{', 'id', 'CHEST', '}', '{', 'flags', '[', 'LOCKED', ']', '}', '}']
```

---

## 4. Semantic Rules

### 4.1 Multiple Values

When a block contains multiple child blocks with different keys, they merge into an object:

```zw
{flags {locked true} {weight 15}}
```

**Parses to:**
```json
{
  "flags": {
    "locked": true,
    "weight": 15
  }
}
```

### 4.2 Repeated Keys

When the same key appears multiple times at the same level, values merge into an array:

```zw
{contents
  {item {id GOLD} {amount 50}}
  {item {id SWORD} {name "iron sword"}}
}
```

**Parses to:**
```json
{
  "contents": {
    "item": [
      {"id": "GOLD", "amount": 50},
      {"id": "SWORD", "name": "iron sword"}
    ]
  }
}
```

### 4.3 Single Value Simplification

When a block contains exactly one simple (non-dict) value, it's stored directly:

```zw
{type object}
```

**Parses to:**
```json
{"type": "object"}
```

Not:
```json
{"type": {"value": "object"}}
```

---

## 5. Type Coercion

### 5.1 Boolean Literals

**Rule:** The barewords `true` and `false` coerce to boolean values.

```zw
{locked true}   → {"locked": true}
{visible false} → {"visible": false}
```

### 5.2 Numeric Literals

**Integers:** Sequences matching `^-?\d+$`
```zw
{health 100}   → {"health": 100}
{depth -50}    → {"depth": -50}
```

**Floats:** Sequences matching `^-?\d+\.\d+$`
```zw
{temperature 72.5}  → {"temperature": 72.5}
{light 0.2}         → {"light": 0.2}
```

### 5.3 String Preservation

All other barewords remain strings:
```zw
{id CHEST}          → {"id": "CHEST"}
{state open}        → {"state": "open"}
{direction north}   → {"direction": "north"}
```

**Quoted strings always remain strings:**
```zw
{value "123"}  → {"value": "123"}  # String, not number
{flag "true"}  → {"flag": "true"}  # String, not boolean
```

---

## 6. Validation Rules

### 6.1 Structural Validation

**Required:**
- Every `{` must have matching `}`
- Every `[` must have matching `]`
- Blocks must have at least a key (value optional)

**Invalid Examples:**
```zw
{type object      # Missing }
[LOCKED OPEN      # Missing ]
{                 # Missing key
```

### 6.2 Type-Specific Validation

**Object Type:**
```zw
{object
  {type object}        # Required
  {id IDENTIFIER}      # Required
  {description "..."}  # Required
}
```

**Container Type:**
```zw
{container
  {type object}        # Required
  {id IDENTIFIER}      # Required
  {contents [...]}     # Required
}
```

**Scene Type:**
```zw
{scene
  {id IDENTIFIER}      # Required
  {description "..."}  # Required
  {objects [...]}      # Optional
  {exits [...]}        # Optional
}
```

### 6.3 Depth Limits

**Default:** Maximum nesting depth of 20 levels

**Rationale:** Prevents stack overflow, encourages flatter data structures

**Configurable:** Via parser options

---

## 7. Reserved Keywords

### 7.1 Current Reserved Words

None currently reserved - all barewords are valid as keys or values.

### 7.2 Future Reserved Words (Planned)

- `@include` - File inclusion
- `@ref` - Cross-reference to other blocks
- `@if` - Conditional inclusion
- `null` - Explicit null value

---

## 8. Comments (Future)

**Status:** Not currently supported

**Planned Syntax:**
```zw
# Line comment to end of line
; Alternative line comment (Lisp-style)

{type object}  # Inline comment
```

---

## 9. Extended Features (Future)

### 9.1 Namespaced Keys

**Syntax:** Dot notation automatically creates nesting
```zw
{flags.locked true}
{flags.weight 15}
```

**Expands to:**
```zw
{flags {locked true} {weight 15}}
```

### 9.2 References

**Syntax:** `@ref:` prefix for cross-references
```zw
{container
  {id CHEST}
  {location @ref:ROOM_DUNGEON_1}
}
```

### 9.3 Includes

**Syntax:** Include external ZW files
```zw
@include "common/item_templates.zw"
```

---

## 10. Compatibility

### 10.1 ZW → ZON Conversion

**Process:**
1. Parse ZW to Python dict/list structures
2. Serialize to JSON (ZON format)
3. Optionally pack to binary ZONB

**Guarantees:**
- All semantic information preserved
- Type coercion maintained
- Array/object structure preserved

### 10.2 ZW → AP Rules

**Process:**
1. Parse ZW to declarative rule structures
2. Extract conditions, effects, and actions
3. Generate AP rule definitions

**Requirements:**
- Rules must follow ZW-AP schema (see AP_SPEC.md)

---

## 11. Implementation Notes

### 11.1 Parser Requirements

**Must Support:**
- Recursive descent parsing
- Token stream processing
- Type coercion (bool, int, float)
- Repeated key detection
- Proper array handling

### 11.2 Error Handling

**Fatal Errors:**
- Unmatched braces/brackets
- Invalid escape sequences (future)
- Depth limit exceeded

**Warnings:**
- Undefined keys (in strict mode)
- Type mismatches (in typed mode)
- Deprecated syntax

### 11.3 Performance Targets

- Parse 10,000 objects/second (Python)
- Parse 50,000 objects/second (GDScript/C++)
- Memory: O(n) where n = input size

---

## 12. Examples

### 12.1 Simple Object

**ZW:**
```zw
{object
  {type object}
  {id CHEST}
  {description "a wooden chest"}
  {flags [OPENBIT TRANSBIT]}
}
```

**Equivalent JSON:**
```json
{
  "object": {
    "type": "object",
    "id": "CHEST",
    "description": "a wooden chest",
    "flags": ["OPENBIT", "TRANSBIT"]
  }
}
```

### 12.2 Complex Scene

**ZW:**
```zw
{scene
  {id DUNGEON_LEVEL_1}
  {description "A dark and musty dungeon"}
  {ambient {light 0.2} {sound "dripping water"}}
  {exits [
    {direction north} {leads_to CORRIDOR_A}
    {direction east} {leads_to TREASURE_ROOM} {locked true}
  ]}
  {objects [
    {container
      {id CHEST_IRON}
      {contents [
        {item {id GOLD_COINS} {quantity 150}}
      ]}}
  ]}
}
```

### 12.3 Rule Definition

**ZW:**
```zw
{rule
  {type zon-memory}
  {id door_open_rule}
  {condition all_of}
  {requires [
    {flag "player_has_key"}
    {time "after_midnight"}
  ]}
  {effect [
    {action "open_door"}
    {sound "creaking_hinges"}
  ]}
}
```

---

## 13. Formal Grammar (EBNF)

```ebnf
document    ::= value
value       ::= block | array | bareword | string
block       ::= "{" bareword (value)* "}"
array       ::= "[" (value)* "]"
bareword    ::= [^{}\[\]\s"]+
string      ::= '"' [^"]* '"'
whitespace  ::= [ \t\n\r]+
```

---

## 14. Changelog

**v0.1 (2025-11-29):**
- Initial specification draft
- Core syntax rules defined
- Type coercion rules established
- Array and block semantics documented
- Examples added

---

## 15. References

- **ZON Format Specification:** See `ZON_FORMAT.md`
- **AP Rule System:** See `AP_SPEC.md` (planned)
- **Implementation:** See `core/zw/zw_parser.py`
- **Tests:** See `tests/zw/`

---

## Appendix A: Token Compression Analysis

**Test Case:** Container with nested objects

**ZW Format (146 tokens, 1408 chars):**
```zw
{world {id DUNGEON_LEVEL_1} {description "A dark dungeon"} ...}
```

**JSON Format (164 tokens, 1869 chars):**
```json
{"world": {"id": "DUNGEON_LEVEL_1", "description": "A dark dungeon", ...}}
```

**Compression:**
- Tokens: 1.12x (11% savings)
- Characters: 1.33x (24.7% savings)
- Estimated LLM tokens: 1.5-2.0x (based on BPE analysis)

**Key Savings:**
- No `:` after keys (saves 1 char per key)
- No `"` around keys (saves 2 chars per key)
- No `,` between elements (saves 1 char per element)
- Fewer `{}` in some cases due to implicit nesting
