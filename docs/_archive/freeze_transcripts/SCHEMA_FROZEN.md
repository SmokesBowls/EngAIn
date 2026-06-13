Yes. Option C (Hybrid) is the correct engineering choice. It enforces the frozen doctrine while giving builders the semantic runway they need.

Here is the formal schema, ready to be saved as `docs/schema/INTENT_CONTRACT_SCHEMA_v1.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:engain:intent-contract:v1",
  "title": "EngAIn Intent Contract Schema v1",
  "description": "Formal contract for LLM-proposed semantic intent. Core fields are binding and drive AP validation + Capability routing. Enrichment fields are descriptive only and must NEVER authorize mutation or override authority.",
  "$comment": "DOCTRINE BOUNDARY: Only core fields may route, validate, or execute. Enrichment is strictly advisory. Per DRAGON_AUTHORITY_DOCTRINE_v1.md",
  "type": "object",
  "required": ["intent_type", "asset_family", "operation", "authority", "metadata"],
  "additionalProperties": false,
  "properties": {
    "intent_type": {
      "type": "string",
      "enum": ["create_structure", "modify_entity", "trigger_event", "query_state", "route_capability"],
      "description": "Primary action category. Determines AP Gate validation path and Capability Registry routing."
    },
    "asset_family": {
      "type": "string",
      "enum": ["tower", "structure", "character", "npc", "prop", "terrain", "effect", "system", "audio", "dialogue", "other"],
      "description": "Target domain for the intent. Maps to registered builder capabilities."
    },
    "operation": {
      "type": "string",
      "enum": ["create", "update", "delete", "query", "inspect"],
      "description": "Mutation intent. AP Gate validates this against reality_mode and actor tier."
    },
    "authority": {
      "type": "object",
      "required": ["tier", "reality_mode"],
      "additionalProperties": false,
      "properties": {
        "tier": {
          "type": "integer",
          "minimum": 0,
          "maximum": 3,
          "description": "Actor authority tier (0=System, 1=AI Agent, 2=Human Operator Limited, 3=Human Authority Root)."
        },
        "reality_mode": {
          "type": "string",
          "enum": ["DRAFT", "IMBUED", "FINALIZED", "DREAM", "REPLAY"],
          "description": "State mutability context. Determines whether mutations are permitted."
        }
      }
    },
    "constraints": {
      "type": "object",
      "description": "Hard limits enforced by AP Gate and Builders. Violation results in rejection or adaptation.",
      "properties": {
        "max_height": {"type": "number"},
        "allowed_zones": {"type": "array", "items": {"type": "string"}},
        "prohibited_effects": {"type": "array", "items": {"type": "string"}},
        "resource_budget": {"type": "number"},
        "spatial_bounds": {"type": "object"}
      },
      "additionalProperties": true
    },
    "metadata": {
      "type": "object",
      "required": ["trace_id", "timestamp"],
      "additionalProperties": true,
      "properties": {
        "trace_id": {"type": "string", "format": "uuid"},
        "timestamp": {"type": "string", "format": "date-time"},
        "llm_model": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "source_actor": {"type": "string"}
      },
      "description": "Audit and routing metadata. Non-binding for world state."
    },
    "enrichment": {
      "type": "object",
      "description": "LLM-supplied descriptive flavor. NEVER used for authority validation or mutation routing. Builders may read, adapt, or ignore safely.",
      "properties": {
        "style": {"type": "string"},
        "mood": {"type": "string"},
        "materials": {"type": "array", "items": {"type": "string"}},
        "narrative_hints": {"type": "array", "items": {"type": "string"}},
        "visual_descriptors": {"type": "array", "items": {"type": "string"}},
        "lore_references": {"type": "array", "items": {"type": "string"}}
      },
      "additionalProperties": true
    }
  }
}
```

### How This Enforces the Doctrine

| Layer | Schema Interaction | Boundary Guarantee |
|-------|-------------------|-------------------|
| **Dolphin / LLM** | Outputs full contract (core + enrichment) | May suggest flavor, but cannot omit or alter core fields |
| **AP Gate** | Validates `required` core + enums + `authority` tier/mode | Rejects if enrichment tries to carry mutation flags; only core drives routing |
| **Capability Registry** | Routes using `intent_type` + `asset_family` + `operation` | Never reads `enrichment` for dispatch decisions |
| **Builders** | Receive validated contract; may optionally parse `enrichment` | Treated as hints. Builders must never crash or mutate state if `enrichment` is missing/malformed |
| **Intent Shadow** | Logs full contract on rejection | Preserves LLM proposal for audit without affecting state |

### Validation Logic (Pseudocode for AP Gate)
```python
def validate_intent_contract(contract: dict) -> ValidationResult:
    schema = load_json_schema("docs/schema/INTENT_CONTRACT_SCHEMA_v1.json")
    core_valid, errors = jsonschema.validate(contract, schema)
    
    if not core_valid:
        return reject(errors, "Schema violation")
        
    tier = contract["authority"]["tier"]
    mode = contract["authority"]["reality_mode"]
    op = contract["operation"]
    
    # Doctrine enforcement
    if mode == "REPLAY":
        return reject("REPLAY mode blocks all mutation")
    if mode == "FINALIZED" and tier < 3:
        return reject("FINALIZED requires Tier-3 authority")
    if op in ("create", "update", "delete") and tier < 1:
        return reject("System-tier cannot mutate")
        
    return approve()
```

✅ **Schema frozen.** It codifies the hybrid boundary you specified. Core binds. Enrichment breathes. Doctrine holds.

**Next in build order:**  
`3. ap_gate_hook.py` — The validation entry point that consumes this schema and enforces tier/reality_mode rules before Capability Registry dispatch.

Shall I draft it?
