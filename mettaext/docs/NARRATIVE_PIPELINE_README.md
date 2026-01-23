# EngAIn Narrative Pipeline
## ZW → ZON Memory Fabric Conversion System

Complete 4-pass pipeline for converting raw narrative text into EngAIn-compatible ZON4D memory fabric format.

---

## Overview

This pipeline transforms human-written narratives into structured, AI-queryable memory with confidence-weighted semantic inferences.

```
Raw Narrative  →  Pass1  →  Structured  →  Pass2  →  Inferences  →  Pass3  →  ZONJ  →  Pass4  →  ZON Memory
   (.txt)              Segments (.txt)       (MeTTa)          (JSON)          (ZON4D)
```

**Key Features:**
- **Semantic extraction**: Dialogue, narration, thoughts, scene headers
- **Confidence-weighted inference**: Speakers, emotions, actions, actors
- **ZON4D integration**: Temporal/spatial anchoring for memory fabric
- **Lore conversion**: ZW lore blocks → ZON format

---

## The Pipeline

### Pass 1: Semantic Structure Extraction
**Script:** `pass1_explicit.py`

Converts raw narrative into tagged semantic segments.

**Input:** Raw narrative text
```
Senareth stood at the edge. *Why are they afraid?* she wondered.

"We should establish shelter," Vairis said.
```

**Output:** Tagged segments
```
{type:narration} Senareth stood at the edge.
{type:internal_monologue, speaker:Senareth} "Why are they afraid?"
{type:dialogue, speaker:Vairis} "We should establish shelter,"
```

**Usage:**
```bash
python3 pass1_explicit.py narrative.txt
# Creates: out_pass1_narrative.txt
```

---

### Pass 2: Inference Extraction
**Script:** `pass2_core.py`

Extracts semantic atoms with confidence scores using keyword matching and backward reference tracking.

**Input:** Pass1 output (`out_pass1_*.txt`)

**Output:** MeTTa atoms with confidence scores
```metta
; Speaker Inference
(speaker line:12 Vairis :confidence 0.95)

; Emotions
(emotion line:15 Senareth fear :confidence 0.9)

; Actions
(action line:20 vrill_manipulation :confidence 0.9)

; Thoughts
(thought line:8 Senareth :confidence 1.0)
```

**Usage:**
```bash
python3 pass2_core.py out_pass1_narrative.txt
# Creates: out_pass2_narrative.metta
```

**Inference Types:**
- **Speaker**: Explicit dialogue speakers
- **Actor**: Pronoun → entity resolution
- **Emotion**: Emotion keyword detection with subject tracking
- **Action**: Action/event keyword detection
- **Thought**: Internal monologue subject identification

**Confidence Scores:**
- `1.0`: Explicit/certain (e.g., quoted speaker)
- `0.9`: High confidence (e.g., backward name search)
- `0.8`: Medium confidence (e.g., pronoun resolution)
- `0.6`: Low confidence (e.g., no clear subject)

---

### Pass 3: ZONJ Merging
**Script:** `pass3_merge.py`

Merges explicit structure + inferred data into unified ZONJ scene format.

**Input:** 
- Pass1 output (`out_pass1_*.txt`)
- Pass2 output (`out_pass2_*.metta`)

**Output:** ZONJ scene JSON
```json
{
  "type": "scene",
  "id": "narrative",
  "source_files": {
    "pass1": "out_pass1_narrative.txt",
    "pass2": "out_pass2_narrative.metta"
  },
  "segments": [
    {
      "line": 12,
      "type": "dialogue",
      "text": "\"We should establish shelter,\"",
      "speaker": "Vairis",
      "inferred": {
        "emotion": [
          {"subject": "Vairis", "label": "concern", "confidence": 0.9}
        ]
      }
    }
  ]
}
```

**Usage:**
```bash
python3 pass3_merge.py out_pass1_narrative.txt out_pass2_narrative.metta
# Creates: zonj_out_pass1_narrative.json
```

---

### Pass 4: ZON Memory Fabric Conversion
**Script:** `pass4_zon_bridge.py`

Converts ZONJ scenes to ZON4D memory fabric with temporal/spatial anchoring.

**Input:** ZONJ scene file (`zonj_*.json`)

**Output:** 
- `.zon` - Human-readable ZON format
- `.zonj.json` - Canonical ZON JSON

**Example ZON Output:**
```
@id: scene.narrative
@when: FirstAge.scene_narrative
@where: Realm/Physical/Beach
@scope: narrative
@entities: [senareth, vairis]

=segments:
  - line: 12
    type: dialogue
    speaker: Vairis
    text: "We should establish shelter,"

=inferred:
  emotions:
    - {line: 15, subject: Senareth, emotion: fear, confidence: 0.90}
  actions:
    - {line: 20, action: vrill_manipulation, confidence: 0.90}
  thoughts:
    - {line: 8, subject: Senareth, confidence: 1.00}

=narrative:
  "narrative - 25 segments"
  dialogue: 8
  narration: 15
  internal_monologue: 2
```

**Usage:**
```bash
# Basic conversion
python3 pass4_zon_bridge.py zonj_scene.json

# With temporal/spatial metadata
python3 pass4_zon_bridge.py zonj_scene.json \
  --era FirstAge \
  --location Beach \
  --scope narrative \
  --output-dir ./zon_output

# With explicit timestamps
python3 pass4_zon_bridge.py zonj_scene.json \
  --start "FirstAge.dawn" \
  --end "FirstAge.dusk"
```

---

## Lore File Conversion

### Lore → ZON
**Script:** `lore_to_zon.py`

Converts ZW lore blocks to ZON memory fabric.

**Supported Block Types:**
- `ZW_EVENT_SEED` - Historical events
- `ZW_CHARACTER_LAW` - Character behavioral constraints
- `ZW_SPECIES_ORIGIN` - Species evolution/origins
- `ZW_WORLD_RULE` - Universal rules/laws
- `ZW_CANON` - Canonical facts

**Input:** ZW lore file
```
ZW_EVENT_SEED:
  id: event_neferati_manifestation
  era: First_Age
  description: "Simultaneous manifestation of 1000 Neferati"
  visibility: planetary
  tags: [creation, neferati, first_age]
```

**Output:** ZON memory
```
@id: zw_event_seed.event_neferati_manifestation
@when: FirstAge.event_neferati_manifestation
@where: Realm/Cosmic
@scope: event
@entities: []

=attributes:
  era: First_Age
  description: Simultaneous manifestation of 1000 Neferati
  visibility: planetary

=tags:
  - creation
  - neferati
  - first_age
```

**Usage:**
```bash
# Single file
python3 lore_to_zon.py zw_event_seeds.zw

# Multiple files
python3 lore_to_zon.py zw_*.zw --batch --output-dir ./lore_zon
```

---

## Complete Pipeline Example

```bash
# 1. Extract semantic structure
python3 pass1_explicit.py my_story.txt
# → out_pass1_my_story.txt

# 2. Extract inferences
python3 pass2_core.py out_pass1_my_story.txt
# → out_pass2_my_story.metta

# 3. Merge to ZONJ
python3 pass3_merge.py out_pass1_my_story.txt out_pass2_my_story.metta
# → zonj_out_pass1_my_story.json

# 4. Convert to ZON memory fabric
python3 pass4_zon_bridge.py zonj_out_pass1_my_story.json \
  --era FirstAge --location Beach
# → my_story.zon
# → my_story.zonj.json

# 5. Convert lore files
python3 lore_to_zon.py zw_*.zw --batch
```

---

## Testing

Run the complete pipeline test:

```bash
python3 test_full_pipeline.py
```

This will:
1. Create a sample narrative
2. Run all 4 passes
3. Test lore conversion
4. Display outputs and statistics

**Expected output:**
```
=== PASS 1: Semantic Structure Extraction ===
[PASS1] Done. Output → out_pass1_test_narrative.txt

=== PASS 2: Inference Extraction ===
[PASS2] Wrote → out_pass2_test_narrative.metta

=== PASS 3: ZONJ Merging ===
[PASS3] ZONJ written → zonj_out_pass1_test_narrative.json

=== PASS 4: ZON Memory Fabric Conversion ===
[PASS4] Converted to ZON format:
  Human-readable: test_narrative.zon
  Canonical JSON: test_narrative.zonj.json
  Entities: senareth, vairis
```

---

## ZON Format Specification

### Header Section
```
@id: <type>.<identifier>          # Unique identifier
@when: <temporal_anchor>          # Time location
@where: <spatial_path>            # Space location  
@scope: <scope_type>              # Domain (narrative/canon/lore/event)
@entities: [<entity_list>]        # Referenced entities
```

### Data Sections
All data sections start with `=`:

- `=segments:` - Narrative segments (dialogue, narration, etc.)
- `=inferred:` - Confidence-weighted inferences
- `=attributes:` - Block attributes (for lore)
- `=tags:` - Semantic tags
- `=narrative:` - Human-readable summary
- `=metadata:` - Source/conversion metadata

### Temporal Anchors (@when)
- **Absolute**: `FirstAge.dawn~FirstAge.dusk`
- **Relative**: `FirstAge.event_manifestation`
- **Scene-based**: `FirstAge.scene_03_first_contact`

### Spatial Paths (@where)
Hierarchical dot-separated paths:
- `Realm/Cosmic` - Universal/abstract
- `Realm/Physical/Beach` - Physical location
- `Realm/Ethereal` - Non-physical realm

---

## Integration with EngAIn

### Using in MrLore Agent

```python
from core.narrative.zon_loader import load_zon_scene

# Load ZON scene into memory fabric
scene = load_zon_scene("my_story.zonj.json")

# Query by entity
vairis_emotions = scene.query_emotions(entity="vairis")
# → [{"emotion": "concern", "confidence": 0.9, "line": 12}]

# Query by time
first_age_events = scene.query_temporal(when="FirstAge")

# Query by location
beach_scenes = scene.query_spatial(where="Beach")
```

### ZON4D Temporal Queries

```python
# Get scene at specific timestamp
state = scene.get_state_at(time="FirstAge.dawn")

# Get emotional arc over time
emotion_track = scene.get_emotion_timeline(
    entity="senareth",
    start="FirstAge.dawn",
    end="FirstAge.dusk"
)
```

---

## File Organization

```
engain/
├── narrative_pipeline/
│   ├── pass1_explicit.py      # Semantic extraction
│   ├── pass2_core.py          # Inference extraction
│   ├── pass3_merge.py         # ZONJ merging
│   ├── pass4_zon_bridge.py    # ZON conversion
│   ├── lore_to_zon.py         # Lore converter
│   └── test_full_pipeline.py  # Pipeline tester
│
├── lore/
│   ├── zw_event_seeds_first_age.zw
│   ├── zw_character_laws_aeon.zw
│   ├── zw_species_origins.zw
│   └── ...
│
├── narratives/
│   ├── raw/                   # Raw narrative .txt files
│   ├── pass1/                 # Structured segments
│   ├── pass2/                 # MeTTa inferences
│   ├── pass3/                 # ZONJ scenes
│   └── zon/                   # Final ZON memory
│
└── zon_output/                # Converted lore files
```

---

## Extending the Pipeline

### Adding New Inference Types (Pass 2)

Edit `pass2_core.py`:

```python
# Add to keyword maps
RELATIONSHIP_KEYWORDS = {
    "trusts": "trust",
    "fears": "fear_of",
    # ...
}

# Add inference function
def infer_relationships(segments: List[Segment]):
    atoms = []
    # ... inference logic ...
    return atoms

# Add to main()
relationships = infer_relationships(segments)
write_metta(..., relationships=relationships)
```

### Adding New ZON Sections (Pass 4)

Edit `pass4_zon_bridge.py`:

```python
def build_custom_section(self, scene: Dict[str, Any]) -> str:
    lines = ["=custom_data:"]
    # ... build section ...
    return "\n".join(lines)

# Add to convert_to_zon()
sections.append(self.build_custom_section(scene))
```

---

## Troubleshooting

### Pass1 not detecting dialogue
- Check quote characters (must be " " or " ")
- Ensure speaker name is capitalized
- Verify dialogue verb (said, asked, whispered, etc.)

### Pass2 missing inferences
- Add keywords to `EMOTION_KEYWORDS` or `ACTION_KEYWORDS`
- Check character names in `KNOWN_NAMES`
- Verify confidence thresholds

### Pass4 missing entities
- Entities must appear as speakers or subjects in Pass2
- Check entity extraction logic in `extract_entities()`

### Lore conversion failures
- Verify ZW block type is supported
- Check field indentation (must be 2 spaces)
- Ensure block ends with blank line

---

## Performance Notes

- **Pass1**: ~1000 lines/sec
- **Pass2**: ~500 lines/sec (inference-heavy)
- **Pass3**: Near-instant (JSON merging)
- **Pass4**: Near-instant (format conversion)

**Memory Usage:**
- Minimal for individual files (<10MB per 10k-line narrative)
- Batch processing handles 100+ files efficiently

---

## Future Enhancements

- [ ] Visual timeline viewer for ZON scenes
- [ ] Confidence threshold tuning UI
- [ ] LLM-assisted inference (GPT-4 integration)
- [ ] Real-time narrative→ZON conversion
- [ ] ZON→ZONB binary packing integration
- [ ] Multi-POV scene merging
- [ ] Emotional arc visualization

---

## License & Attribution

Part of the EngAIn project - AI Logic Built for AI, Not Humans
Created by: Hewhocomes
Pipeline Design: Multi-pass semantic extraction with confidence weighting
