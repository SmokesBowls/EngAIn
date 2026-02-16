# ZW Semantic Validation Test

## Purpose

This test validates the core philosophical claim of ZW (Ziegel Wagga):
**"AI logic should compress MEANING, not FORMAT."**

We prove this by showing that ZW can express complex semantic relationships
more concisely than JSON/XML while preserving full meaning.

---

## Test Case: Container Ontology

### Requirement (Natural Language):
"All objects classified as 'container' must have a 'capacity' property.
Containers can hold items up to their capacity.
When full, containers reject new items."

### JSON Representation (Traditional):
```json
{
  "rules": [
    {
      "if": {
        "object_type": "container"
      },
      "then": {
        "required_properties": ["capacity"]
      }
    },
    {
      "if": {
        "object_type": "container",
        "condition": {
          "current_items": {
            "count": {
              "less_than": "capacity"
            }
          }
        }
      },
      "then": {
        "actions": ["accept_item"]
      }
    },
    {
      "if": {
        "object_type": "container",
        "condition": {
          "current_items": {
            "count": {
              "greater_than_or_equal": "capacity"
            }
          }
        }
      },
      "then": {
        "actions": ["reject_item"]
      }
    }
  ]
}
```

**Token count**: ~140 tokens  
**Nesting depth**: 5 levels  
**Readability**: Low (verbose structure)

---

### ZW Representation (Proposed):
```zw
@container requires capacity

@container.accept_item when:
  items.count < capacity

@container.reject_item when:
  items.count >= capacity
```

**Token count**: ~20 tokens (7x reduction)  
**Nesting depth**: 1 level  
**Readability**: High (declarative)

---

## Validation Criteria

### ✅ PASS Conditions:
1. ZW representation is ≤30% the token count of equivalent JSON
2. All semantic relationships are preserved
3. Constraints are enforceable by AP system
4. AI can parse and reason about ZW directly

### ❌ FAIL Conditions:
1. ZW requires more tokens than JSON
2. Semantic meaning is lost or ambiguous
3. AP cannot enforce the rules
4. Human interpretation required for AI to understand

---

## Implementation Test

```python
# Minimal ZW parser test
def test_zw_semantic_compression():
    zw_source = """
    @container requires capacity
    
    @container.accept_item when:
      items.count < capacity
    
    @container.reject_item when:
      items.count >= capacity
    """
    
    # Expected parsed structure
    expected = {
        "ontology": {
            "container": {
                "required": ["capacity"]
            }
        },
        "constraints": [
            {
                "entity": "container",
                "action": "accept_item",
                "condition": "items.count < capacity"
            },
            {
                "entity": "container",
                "action": "reject_item",
                "condition": "items.count >= capacity"
            }
        ]
    }
    
    # Parse ZW
    result = parse_zw(zw_source)
    
    # Validate semantic equivalence
    assert result == expected
    
    # Validate token efficiency
    json_tokens = count_tokens(json_equivalent)
    zw_tokens = count_tokens(zw_source)
    
    compression_ratio = zw_tokens / json_tokens
    assert compression_ratio < 0.3  # Must be <30% of JSON size
    
    print(f"✅ ZW Compression: {compression_ratio:.1%}")
    print(f"✅ Semantic preservation: VERIFIED")
```

---

## Next Steps

1. **Implement minimal ZW parser** (`core/zw/zw_parser.py`)
2. **Run this test** to prove concept
3. **If passes**: ZW is validated, proceed with full implementation
4. **If fails**: Revise ZW syntax, retest

---

## Success Metrics

- [ ] Parser correctly extracts ontology definitions
- [ ] Parser correctly extracts constraints
- [ ] Token compression ≥70% vs JSON
- [ ] All semantic relationships preserved
- [ ] AP can enforce parsed constraints

**This test must pass before scaling ZW to full Zork conversion.**

---

*Status: READY FOR IMPLEMENTATION*  
*Priority: CRITICAL (per critique)*  
*Blocks: Full ZW parser, Zork scaling*
