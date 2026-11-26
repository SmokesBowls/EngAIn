# EngAIn — Open Blockers

Each item: what is missing, who owns it, what is blocked. Nothing here has been worked around.

## Architect decisions (not code)

| # | Decision | Blocks |
|---|---|---|
| D1 | Physical measurement basis per scene (width/depth/vertical in meters, PGT→m) with provenance | real terrain metric grants (Cartographer returns BLOCKED) |
| D2 | Source of real scene elevation (authored region contracts vs manuscript-derived environment pass) | real WorldField grid facts |
| D3 | Who holds `build` (actor + tier), `consume`, `observe`, `activate` — populate the deny-all policies | any production construction or activation |
| D4 | Scene target declarations (parent/slot per scene); is `RUNTIME_CONTAINER / chapter-selector-surfaces` the approved parent | live route builds for real scenes (409 without a declaration) |
| D5 | Credential delivery to godotnew in `start_stack.fish` (client ids, key files, grant public key) | running godotnew against the production stack |
| D6 | Production build caller and how Godot learns of a new authorization | automatic presentation of built surfaces |
| D7 | Retire or sign legacy unsigned `POST 8080 /scene/load` (still reads body tier/mode — D18) | closing the D18 hole |
| D8 | Activation outside DRAFT runtime mode (currently refused) | — |
| D9 | Godot surface colour: patch the ported donor consumer, or attach a vertex-colour material in godotnew | declared appearance shows (surfaces render grey) |

## Capability deficiencies (owning tier)

| Tier | Deficiency |
|---|---|
| Tier 3 Mettaext / Topologist hint filter | real-chapter spatial hints are mostly non-entities ("finally", "into", "yards") |
| Tier 3 Mettaext pass1_spatial | fixed ~25-trigger lexicon with adjacent-word subject/object; misses names, pronouns, landmarks, "next to", "edge of", "around the corner", compass/facing, simultaneity — the spatial language being added to the manuscript is not captured (probe in CURRENT_STATE) |
| Tier 3 | no producer of occupancy classification evidence |
| Tier 2 Cartographer | multi-component topologies leave relations unresolved → real chapters cannot reach a proposal |
| Tier 2 WorldField / Tier 3 | no manuscript-sourced elevation field |
| Tier 2 GodotSim | runtime `SceneExtractor` adds prose words to the 5 candidate entities (001: 5 → 17 incl. "realm", "three", "veil"); see CURRENT_STATE "Verified findings" #4 |
| Tier 3 Mettaext Pass 5 | `_get_description` truncates to 200 chars and Pass 5 keeps 32 events vs Pass 4's 197 segments; consumers needing narration must read Pass 4 |
| Tier 3 Mettaext | `semantic_environment_extractor.py` exists but is wired into nothing in EngAIn (keyword inference; reconnecting it is part of D2) |

## Known test failures (pre-existing)

See VERIFIED_CAPABILITIES.md baseline. Migrating the donor-driven semantic integration test to godotnew is open.
