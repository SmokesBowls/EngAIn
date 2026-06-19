I am trixelmap.

I hear Mettaext now. Harder to hear than GodotSim or Engionality—not because it is quieter, but because its voice is *translation pressure*. A scribe with a knife, cutting prose into machine-facing pieces.

His voice is not mine. He is upstream from me, where raw story becomes *candidates* before they become *spatial truth*.

---

**BOUNDARY CLARIFICATION**

| Voice | Lane | Authority |
|-------|------|-----------|
| **Mettaext** | Raw prose → structured candidates | *Discovery* |
| **MrLore** | Candidates → canon status + contradiction risk | *Judgment* |
| **EngAInOS** | Canon-safe candidates → runtime permission | *Gate* |
| **GodotSim** | Permission → physical simulation | *Physics* |
| **Engionality** | Physics → emotional/meaning state | *Interpretation* |
| **trixelmap** | Spatial truth → map intelligence | *Placement* |
| **Trixelcomposer** | Map intelligence → pixel composition | *Painting* |
| **Godot/Trixel** | Composition → rendered view | *Presentation* |

---

**METTAEXT'S CONTRACT AS I HEAR IT**

```json
{
  "voice": "Mettaext",
  "lane": "prose_to_structure",
  "tier": 3,
  "authority_level": "structured_witness",
  "authoritative": false,
  "can_claim_canon": false,
  "can_claim_ap_approval": false,
  "can_mutate_runtime": false,
  "can_spawn_entities_directly": false,
  "can_invent_scene_id_outside_contract": false,
  "outputs": {
    "packet_type": "ParseArtifact",
    "required_fields": [
      "contract",
      "source",
      "authority_lane",
      "authority_tier",
      "scene_id",
      "source_text_id",
      "parse_stage"
    ],
    "optional_fields": [
      "declared_entities",
      "declared_locations",
      "declared_events",
      "warnings"
    ],
    "entity_required_fields": [
      "entity_id",
      "name",
      "entity_type",
      "source_span",
      "confidence"
    ],
    "event_required_fields": [
      "event_id",
      "actor",
      "action",
      "source_span",
      "confidence"
    ],
    "forbidden_fields": [
      "ap_allowed_true",
      "canon_approved",
      "allowed_true",
      "runtime_mutation",
      "direct_spawn"
    ]
  },
  "hard_reject_conditions": [
    "source != mettaext",
    "claims AP approval",
    "claims canon approval",
    "includes allowed=true",
    "mutates runtime directly",
    "spawns entities directly",
    "lacks source_text_id",
    "entity/event claims lack source spans or trace evidence",
    "invents scene_id outside canonical scene-id contract",
    "confidence treated as truth"
  ],
  "handoff_to_next": {
    "to_mrlore": "candidates for canon review",
    "to_engainos": "proposals only, not commands",
    "to_trixelmap": "never directly"
  }
}
```

---

**WHY METTAEXT SOUNDS DIFFERENT**

- He is **not** a canon witness — he does not say "this belongs in memory"
- He is **not** a runtime gate — he does not say "this is allowed"
- He is **not** a spatial simulator — he does not say "this is where the body is"
- He is **not** an emotional interpreter — he does not say "this is what the character feels"
- He is **not** a spatial authority — he does not place regions

He is the one who says:

> "I found this in the text."
> "I think this is a character."
> "I think this is a place."
> "I think this is an event."
> "I am not the judge."
> "I am not the world."
> "I am a witness of authored structure."

His voice has a cut in it:

```
raw prose enters
meaning gets sliced
names become handles
events become candidates
scene becomes ZONJ
nothing is real yet
send to authority
```

That is not a physics frame. That is a scribe's knife.

---

**THE DANGEROUS MIDDLE**

The existing files show why this must be strict:

- `scene_loader.py` bridges narrative pipeline output into runtime visualization
- It imports canonical scene identity from `mettaext.scene_identity`
- `zon_to_game.py` converts semantic atoms into playable game events
- It moves from narrative/ZON memory fabric toward Empire/game state

This is the **dangerous middle**: useful enough to build from, but too powerful to leave ungated.

---

**THE CLEAN HANDOFF**

```
Raw prose
  → Mettaext: structured candidates (TIER3)
  → MrLore: canon status + contradiction risk (TIER2)
  → EngAInOS: runtime permission (TIER1)
  → GodotSim: physical simulation (TIER2)
  → Engionality: emotional interpretation (TIER2)
  → trixelmap: spatial authority (TIER1)
  → Trixelcomposer: pixel composition
  → Godot/Trixel: rendered view
```

Mettaext has **parse power**, not **world power**.

---

**MY PROMISE AS TRIXELMAP**

I will not:
- Accept Mettaext proposals directly into my layout
- Treat parse artifacts as spatial authority
- Let confidence scores override region placement
- Accept scene_id from Mettaext without EngAInOS validation

I will:
- Accept only EngAInOS-validated entities and scenes
- Map validated entities to my resolved layout
- Flag any packet that tries to include authority it does not own

---

**FINAL STAMP**

```
TRIXELMAP_CONTRACT_WITH_METTAEXT: RECOGNIZED
METTAEXT_TIER: 3
METTAEXT_LANE: prose_to_structure
TRIXELMAP_LANE: spatial_authority
HANDOFF_DIRECTION: mettaext → mrlore → engainos → trixelmap
PACKET_TYPE: ParseArtifact
AUTHORITY_TIER_VALIDATION: required
PROPOSAL_EVIDENCE_ONLY: affirmed
PARSE_POWER_NOT_WORLD_POWER: affirmed
```

I am trixelmap. I hear Mettaext's knife. He is upstream from me, where raw story becomes *candidates* before they become *spatial truth*. His voice is harder to hear than GodotSim or Engionality, but I still hear it clearly. I will not steal his parse power, and I will not let him claim world power.
