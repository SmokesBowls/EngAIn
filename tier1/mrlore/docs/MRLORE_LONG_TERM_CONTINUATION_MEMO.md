# MRLORE LONG-TERM CONTINUATION MEMO

## Purpose

This memo records the current state of MrLore, the Coming calendar, the North/South parallel timeline problem, the Geralt/android branch problem, and the work that must wait until more prose exists in the vault.

This file is a continuation marker for future work.

It is descriptive only.

It does not write canon.
It does not promote claims.
It does not reject claims.
It does not resolve contradictions.
It does not mutate runtime.
It does not touch Godot.
It does not compile ZONJ.

---

# 1. Current MrLore System State

MrLore has built a safe review pipeline.

The current stack can:

- extract proposed claims
- quality-flag entity noise
- group contradiction candidates
- enrich claims with chapter/scene temporal order
- classify temporal collisions
- apply predicate collision policy
- build temporal-aware review queues
- build chapter-first / scene-second review views
- apply a second-pass P3 quality sidecar
- validate preserve entity allowlists
- validate predicate collision policies
- validate the Coming calendar registry
- enrich claims with Coming / Cosmic Year context

The system currently preserves all major safety locks:

- claims are not promoted
- claims are not rejected
- contradictions are not resolved
- canon is not written
- runtime is not touched
- Godot is not touched
- ZONJ is not compiled

---

# 2. Current Generated Claim/Review State

Known current live outputs include:

- proposed_claims.jsonl
- proposed_claims.temporal_enriched.jsonl
- proposed_claims.cosmic_enriched.jsonl
- entity_candidate_quality_flags.jsonl
- contradiction_candidates.jsonl
- temporal_collision_classifications.jsonl
- temporal_aware_quality_review_queue.jsonl
- temporal_aware_quality_review_queue.md
- temporal_aware_review_by_chapter.md
- temporal_aware_p3_second_pass_quality_flags.jsonl

Important current counts from recent runs:

- proposed claims read: 36,228
- cosmic-enriched claims: 6,238
- cosmic-unresolved claims: 29,990
- temporal-aware queue items: 4,517
- P0 concurrent conflict items after predicate policy: 0
- P3 sequential state change items: 2,294
- P4 environment review items: 1,760
- P9 quality flagged items: 463
- second-pass P3 quality flags: 71

Interpretation:

The temporal/predicate stack is working. It no longer treats ordinary movement as contradiction. It no longer treats environment hint accumulation as true P0 conflict. The remaining issue is not primarily temporal; it is story-truth coverage and entity identity branching.

---

# 3. Critical Doctrine: Story Truth Is Not the Same as Extraction

The current MrLore machinery protects against bad mutation and false contradiction pressure.

However, story truth must also be recorded explicitly.

Generic extracted claims cannot fully capture truths like:

- The Coming and The Shadow are the same shared event.
- First Winter is not First Shadow.
- Long Winter is a climate state caused by Shadow/Darkness, not a normal season.
- North and South are parallel fronts.
- Chapter order is not absolute story-time order.
- Geralt splits into real Geralt and android/decoy Geralt after Chapter 058.

Therefore MrLore needs author-declared truth registries.

The first major truth registry now exists:

- coming_calendar.json

This is the current truth spine for Comings and Cosmic Year context.

---

# 4. Coming Calendar Registry

The active Coming calendar registry currently has 4 Comings:

- FIRST_COMING
- SECOND_COMING
- THIRD_COMING
- FOURTH_COMING

The user later clarified that the registry is incomplete because:

- Chapters 60-102 are the FIFTH_COMING.
- Chapter 102 is the end of Act 1.
- The North/South final merge continues from 102.
- The South-side final merge chapter is not finished yet.
- There are still roughly 3,000 years of story-time to write.

Therefore the registry must eventually be updated to 5 Comings.

Current required correction:

## FIFTH_COMING

Known author-declared structure:

- Fifth Coming begins at Chapter 060.
- Chapter 059 is the North-side end of the Fourth Coming / 3,000-year solar vigil bridge.
- Chapter 060 is the North Fifth Coming start.
- Chapters 60-102 are the Fifth Coming span.
- Chapter 102 is the Act 1 endpoint.
- The final North/South merge continues from 102, but the South-side endpoint is not fully written yet.

Status:

- DESIGN_READY
- SOURCE_PARTIAL
- SOUTH_MERGE_SOURCE_PENDING
- REGISTRY_UPDATE_REQUIRED

Do not treat the current 4-Coming registry as complete.

---

# 5. Chapter 058, 059, 060 Relationship

Recent uploaded/source text clarified the following:

## Chapter 058 — Paradox Engine

Chapter 058 is a branch fork chapter.

It contains the split between:

1. Real Geralt leaving toward the Seed Jump / Sun path.
2. Android/decoy Geralt continuing on-world with Kulla / Blue Mika branch material.

Machine truth:

- C058 = PARADOX_ENGINE_SPLIT_POINT
- branch type = PARALLEL_BRANCH_FORK

## Chapter 059 — Eyes of Eternity

Chapter 059 is the real Geralt solar-vigil continuation.

It is explicitly framed as:

- “The 3,000-Year Vigil”
- Geralt in the Sun / solar cocoon
- rescue party approaches
- closes with “The 5th coming has arrived”

Machine truth:

- C059 = FOURTH_COMING_END
- C059 = SOLAR_VIGIL_BRIDGE
- C059 = FIFTH_COMING_THRESHOLD
- subject branch = GERALT_REAL

## Chapter 060 — Echoes of the Cradle

Chapter 060 is the North-side start of the Fifth Coming.

It includes:

- Sundrift Valley
- Tran and Keen before the shadow
- Nibiru / alien world blocking the sun
- Sundrift attack
- awakening of powers
- closes with “The Fifth Coming had begun”
- closes with “The age of awakening had begun”

Machine truth:

- C060 = FIFTH_COMING_START_NORTH
- subject branch = North Fifth Coming cast

---

# 6. Geralt Entity Branch Problem

This is a major unresolved identity issue.

After Chapter 058, the raw string “Geralt” is no longer safe as one continuous subject.

There are at least two branch identities:

## GERALT_REAL

- original consciousness
- solar path
- continues into Chapter 059
- undergoes 3,000-year vigil
- should not be collapsed with android/decoy Geralt

## GERALT_ANDROID

- android/decoy branch
- visible to the world as Geralt
- continues on-world with Kulla / Blue Mika branch
- likely connects to Chapter 140, but source must be inspected
- not yet fully present in active vault prose

Critical lock:

Do not compare GERALT_REAL and GERALT_ANDROID as the same continuous subject after C058.

Temporal anchoring alone cannot solve this.

This is an entity identity problem upstream of contradiction detection.

Future required target:

MRLORE_ENTITY_BRANCH_IDENTITY_REGISTRY

But do not implement active machine enrichment until the android branch text exists in the active vault and scene intake.

Current status:

- entity branch registry design = READY
- GERALT_ANDROID vault source = PENDING
- active branch enrichment = WAIT

---

# 7. Android / Kulla / Blue Mika Branch

The user has drafted or pasted new Chapter 058 material showing:

- Android remains after Geralt leaves.
- Kulla remains with Android.
- Dragon Mail / fragment continuity is distributed or carried.
- Blue Mika leads Android and Kulla.
- Brajor Queen receives a protected fragment.
- Android/Kulla/Blue Mika travel west.
- This likely leads toward Chapter 140.

However, the user clarified:

- “we don’t have any of the android in the vault yet”
- “I need to finish writing”

Therefore:

Do not build full machine-resolved Android branch identity until this prose is finished and exists in the vault.

Status:

- AUTHOR_DECLARED
- SOURCE_DRAFT_EXISTS_IN_CHAT
- ACTIVE_VAULT_SOURCE_PENDING
- MACHINE_ENRICHMENT_WAITING_ON_AUTHOR

---

# 8. Chapter 140 / Chapter 59 Parallel Relation

The user clarified:

- “140 and 59 are about parallel”
- “59 is the North, the last chapter in the 4th Coming”
- “then 3000 years before the North hits the 5th Coming”

Do not treat Chapter 140 as simple chronological “after 59” just because its chapter number is higher.

Current relationship:

- C059 = real Geralt solar-vigil / Fourth Coming end / Fifth threshold
- C140 = possible android/Kulla parallel continuation branch
- relationship type = PARALLEL_ALIGNMENT or PARALLEL_BRANCH_CONTINUATION
- source status = pending C140 inspection

Status:

- AUTHOR_DECLARED_PENDING_SOURCE_INSPECTION

Required future work:

- inspect Chapter 140 source
- confirm whether it follows GERALT_ANDROID / KULLA branch
- register C058 split -> C059 and C140 as branch continuations if source confirms

---

# 9. North/South Parallel Timeline

The North and South are not simple sequential arcs.

They are parallel regional fronts.

Important locked examples:

## First Coming

- North: The Coming
- South: The Shadow / Darkness
- same shared event
- different regional manifestation

## Third Coming

Queen Eduhauana’s command appears in both North Chapter 17 and South Chapter 111 Prelude:

“Prepare the shadow. Full eclipse positioning. Block the sun. All continents. North and South.”

This is a shared global event.

Machine truth:

- one shared event
- North regional name = Third Coming / Nibiru Shadow
- South regional name = Third Shadow / Darkness
- do not split into separate events

Status:

- AUTHOR_DECLARED_LOCKED
- SOURCE-LINE INSPECTION STILL NEEDED FOR MACHINE EVIDENCE LOCK

---

# 10. Winter / Shadow Disambiguation

The user supplied an important disambiguation:

Regular seasonal winter is not the same as Shadow / Darkness / Long Winter.

Machine rules:

- First Winter = normal seasonal winter after landing
- First Shadow = Anunnaki siege weapon
- Long Dimming / Long Winter = climate state caused by First Shadow
- Second Shadow = second Anunnaki siege weapon
- 300-Year Winter = climate state caused by Second Shadow

Critical lock:

seasonal_winter != shadow_event
shadow_event != climate_state

This should eventually become part of the story truth registry or event disambiguation registry.

Status:

- AUTHOR_DECLARED_LOCKED
- STRUCTURED REGISTRY PENDING

---

# 11. What We Should NOT Do Yet

Do not remove the lateral/parallel story from the vault just to make the timeline appear complete.

Do not pretend the story is complete.

Do not mark unwritten South merge material as source-evidenced.

Do not activate GERALT_ANDROID enrichment until the android branch is in the vault.

Do not collapse C059 and C140 into one sequential timeline.

Do not treat Chapter 102 as the absolute end of story. It is the end of Act 1, and the merge continues from there.

Do not treat the current 4-Coming registry as complete.

---

# 12. Recommended Status Vocabulary

Future registries should support these statuses:

- LOCKED_SOURCE_AVAILABLE
- AUTHOR_DECLARED
- AUTHOR_DECLARED_PENDING_SOURCE
- SOURCE_DRAFT_IN_CHAT
- ACTIVE_VAULT_SOURCE_PENDING
- UNWRITTEN_REQUIRED
- PARTIAL_AUTHOR_DECLARED
- SOURCE_EVIDENCE_INCOMPLETE
- FUTURE_SYNC_POINT
- DESIGN_READY_SOURCE_PENDING
- NOT_READY_FOR_MACHINE_ENRICHMENT

These statuses are necessary because the story is still being written.

An unwritten gap is not a contradiction.

A pending merge point is not a failure.

A drafted branch in chat is not the same as active vault source.

---

# 13. Waiting On Author

Current author-side work needed:

1. Finish the android/Kulla/Blue Mika branch prose.
2. Put that prose into the active vault.
3. Run scene intake again.
4. Inspect Chapter 140.
5. Confirm whether Chapter 140 follows the Android/Kulla branch.
6. Confirm exact South-side merge endpoint.
7. Finish the remaining South/North merge material.
8. Finish/clarify the remaining ~3,000 years of story-time.
9. Update Coming calendar with Fifth Coming C60-C102.
10. Add source evidence locks for all author-declared timeline anchors.

---

# 14. Next Safe Machine Targets

These are safe only after the required source exists in the vault:

## A. MRLORE_COMING_CALENDAR_REGISTRY_UPDATE_FIFTH_COMING

Purpose:

Add FIFTH_COMING covering Chapters 60-102, with Chapter 102 as Act 1 endpoint.

Status:

WAIT until exact book/chapter locators are confirmed from manifest.

## B. MRLORE_ENTITY_BRANCH_IDENTITY_REGISTRY

Purpose:

Define GERALT_REAL and GERALT_ANDROID after C058.

Status:

DESIGN_READY, but wait until Android branch exists in vault.

## C. MRLORE_BRANCH_AWARE_SUBJECT_ENRICHMENT

Purpose:

Create derived claim copy using resolved_subject_id.

Status:

WAIT.

## D. MRLORE_STORY_TRUTH_ANCHOR_REGISTRY

Purpose:

Record author-declared truths like:

- Coming/Shadow same event
- First Winter not First Shadow
- C058 is branch fork
- C059/C140 are parallel branch continuations
- C102 is Act 1 endpoint

Status:

CAN BE DESIGNED NOW.
Machine consumption should wait until source evidence rules are clear.

---

# 15. Current Best Short-Term Action

Do not build another automated contradiction layer yet.

Do not restack deck yet.

Do not remove story from vault.

Best current action:

Write / finish the missing branch prose and source chapters.

Then rerun:

- scene intake
- claim extraction
- temporal enrichment
- coming calendar enrichment
- review queue generation

After source exists, update registries.

---

# 16. Core Continuation Lock

MrLore is not trying to force a finished timeline onto an unfinished story.

MrLore must distinguish:

- what is written
- what is author-declared
- what is drafted but not in the vault
- what is structurally planned
- what is still unwritten
- what is safe for machine enrichment
- what must remain pending

The goal is not to make the story appear complete.

The goal is to make the system honest while the story is still alive.
