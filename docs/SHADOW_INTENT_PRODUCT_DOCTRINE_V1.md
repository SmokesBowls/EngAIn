# SHADOW INTENT PRODUCT DOCTRINE V1

**Document ID:** `SHADOW_INTENT_PRODUCT_DOCTRINE_V1`  
**Project:** EngAIn  
**Classification:** Product Doctrine / Design Lock / Future Implementation Target  
**Status:** Accepted conceptual specification; this document does **not** claim the complete feature is implemented  
**Date:** 2026-09-03

---

## 1. Purpose

Shadow Intent is a long-standing EngAIn game-authoring concept intended to solve several problems at once:

1. creators can remain trapped in edit mode indefinitely and never deliberately finish a game;
2. AI-assisted creation produces large amounts of rejected, replaced, abandoned, experimental, and alternate material that may still contain creative value;
3. long-running projects accumulate enough local data that storage pressure eventually becomes a practical constraint;
4. ordinary deletion treats unused creative intent as garbage even when that intent could support a coherent new work;
5. a creator who has already played most of a game while building it needs a meaningful reason to commit the first game as finished.

Shadow Intent converts the negative space of authorship into a future creative resource.

The governing idea is:

> **What the creator deliberately did not choose is still creative intent. Preserve it as shadow material, and when an authorized trigger occurs, resolve that material into a new playable work instead of silently wasting it.**

Shadow Intent is not merely a recycle bin, undo history, backup folder, alternate-ending generator, or storage compressor. It is a creative subsystem whose raw material is accumulated rejected intent.

---

## 2. The Core Authoring Model

During ordinary co-authoring, EngAIn continually encounters decisions with at least two broad outcomes:

```text
accepted intent
    -> becomes part of the active game

rejected / abandoned / replaced intent
    -> becomes eligible for Shadow Intent
```

Examples of shadow-eligible material may include:

- rejected characters;
- removed characters;
- unused character relationships;
- discarded town or location names;
- abandoned settlements, regions, maps, or world layouts;
- alternate quest structures;
- dialogue branches deliberately removed from the accepted work;
- unused mechanics;
- replaced mechanics;
- alternate visual directions;
- rejected assets or asset variants;
- abandoned factions;
- unused lore;
- alternate timelines;
- unused endings;
- story branches the creator explicitly chose not to pursue;
- prototypes and experiments that expressed real creative intent but were not accepted into the active game.

The important distinction is deliberate creative rejection, not simple technical trash.

A corrupted cache file, duplicate build artifact, temporary compiler output, or meaningless generated noise is not automatically Shadow Intent merely because it is unused.

Shadow Intent should preserve **meaningful abandoned possibility**, not indiscriminately archive every byte the toolchain ever produced.

---

## 3. Why It Is Called Shadow Intent

The accepted game represents realized intent: the choices that became true in that authored world.

Shadow Intent represents unrealized intent: ideas that were considered, shaped, discussed, prototyped, or partially built but deliberately did not become part of the accepted work.

The term therefore means more than "deleted ideas."

```text
REALIZED INTENT
    accepted decisions
    -> Game 1

SHADOW INTENT
    rejected / abandoned / replaced decisions
    -> unresolved creative possibility
```

The shadow does not automatically become canon in Game 1.

It remains subordinate to the completed work until a separate synthesis event is authorized.

---

## 4. Primary Product Goal: Give the Creator a Reason to Finish

AI-assisted game creation creates a peculiar completion problem.

A creator can spend months or years doing this:

```text
edit level
play level
change level
play again
change character
rewrite scene
replace town
rebuild mechanic
play again
add another level
edit again
```

By the time the project is nearly complete, the creator may already have experienced most of the content through testing and editing.

The final act of declaring the game "finished" can therefore feel less rewarding than continuing to modify it.

Shadow Intent changes the incentive.

While Game 1 is still being authored, the Shadow Intent pool may accumulate, but its full synthesis payoff remains unavailable.

The deliberate completion event authorizes something new:

```text
finish Game 1
    -> freeze / identify the completed accepted work
    -> close the associated Shadow Intent collection window
    -> synthesize the accumulated shadow material
    -> produce a new playable work the creator has not already experienced
```

The creator's reward for finally leaving edit mode is therefore not merely a badge, export dialog, or "project complete" message.

The reward can be:

> **A second game created from the roads not taken while the first game was being authored.**

This is a core behavioral purpose of Shadow Intent.

---

## 5. The Shadow Game Is Not Merely an Alternate Ending

Shadow Intent should not be reduced to "generate the other ending."

Its source material may have accumulated across the entire authorship history.

A resulting Shadow Game may therefore contain coherent transformations built from combinations such as:

- a rejected character becoming central;
- a discarded town becoming the main setting;
- an abandoned faction becoming dominant;
- a mechanic that did not fit Game 1 becoming foundational in the new game;
- a removed relationship becoming the basis of a new conflict;
- an alternate history explaining why unused material exists elsewhere in the world;
- rejected quests combining into an entirely different progression;
- unused visual or environmental directions becoming the identity of another region or era.

The synthesis process must be allowed to organize, reinterpret, reconcile, and transform shadow material into a coherent work.

It must not simply concatenate a folder of rejected assets and call the result a sequel.

---

## 6. Surprise Is Part of the Reward

The creator may know Shadow Intent is accumulating, but the system should avoid turning the Shadow Game into another project they continuously spoil through editing.

The product value comes partly from the fact that the creator supplied the ingredients over time without manually assembling the final result.

Conceptually:

```text
creator makes Game 1
    -> creator sees accepted work repeatedly
    -> rejected intent accumulates separately
    -> creator finally commits Game 1
    -> EngAIn resolves shadow material
    -> creator receives something substantially new
```

The creator authored the source possibilities, but did not necessarily author the final combination.

That distinction is intentional.

---

## 7. Secondary Product Goal: Make Storage Pressure Productive

Long-running AI-assisted projects accumulate data.

Eventually the creator may reach the practical limit of local storage.

Without Shadow Intent, the likely choices are ordinary ones:

- stop building;
- buy more storage;
- move arbitrary folders somewhere else;
- upload material to cloud storage;
- start deleting old experiments and abandoned work;
- manually decide which unused material still matters.

Shadow Intent introduces another option:

> **Before the creator is forced to throw unused creative history away, offer to turn the accumulated shadow material into a playable artifact.**

This does **not** mean generating a Shadow Game automatically frees disk space.

The synthesis itself may temporarily require additional space.

The storage value comes afterward, when the creator has a meaningful artifact that can be moved to another storage device or location.

Example:

```text
local project becomes storage-constrained
    -> Shadow Intent synthesis is offered / required as appropriate
    -> Shadow Game is generated and verified
    -> creator copies or moves the completed Shadow Game to:
         external drive
         flash drive
         another machine
         user-chosen archive
         optional cloud location
    -> creator may then remove raw shadow source material from the working machine
    -> local space becomes available again
```

The important product insight is that the creator was going to have to remove something anyway.

Shadow Intent attempts to extract creative value **before** that removal occurs.

---

## 8. Storage Is a Trigger, Not the Meaning of the Feature

Shadow Intent must not be mischaracterized as a disk-management utility.

Storage pressure is one possible activation condition because it creates a natural moment when the user must make a decision about accumulated project history.

The feature remains fundamentally creative.

Two major activation paths are therefore valid:

### 8.1 Completion Trigger

The creator deliberately finishes Game 1.

```text
AUTHORING
    -> FINAL COMMITMENT
    -> GAME 1 COMPLETE
    -> SHADOW SYNTHESIS AUTHORIZED
```

### 8.2 Storage-Pressure Trigger

The local working environment is approaching or has reached a configured safe storage boundary.

```text
AUTHORING
    -> STORAGE WARNING
    -> CRITICAL STORAGE CONDITION
    -> CREATION BLOCKED IF CONTINUING IS UNSAFE
    -> SHADOW INTENT / STORAGE RESOLUTION FLOW
```

The exact implementation may permit other deliberate triggers in the future, but these two capture the original product logic.

---

## 9. The Old-Television Static Intervention

A key part of the original Shadow Intent user experience is that severe storage pressure should not be presented as a forgettable little operating-system-style warning.

As storage approaches the hard limit, EngAIn should provide escalating warnings.

When the system reaches a condition where continued creation would be unsafe or impossible, the authoring/game presentation may deliberately transition into an **old television static** interruption.

The intended emotional sequence is approximately:

```text
normal game / editor
    -> warning signs
    -> stronger warning
    -> hard storage boundary reached
    -> screen breaks into old-TV static
    -> brief "what just happened?" moment
    -> EngAIn clearly reveals that the project is safe
    -> creation is suspended until storage is addressed
```

The joke is intentional.

For a moment, the user may think the game or computer just broke.

That surprise should be theatrical, not deceptive or destructive.

Within seconds the system must clearly communicate:

- the project has not been lost;
- this is an EngAIn intervention;
- local storage has reached a critical condition;
- additional building is suspended because continuing could endanger the working project;
- the user has clear next actions.

The static screen is therefore both fiction and functional UX.

It turns a mundane technical limit into a memorable part of the game-authoring experience.

---

## 10. Escalating Storage States

A future implementation should distinguish at least these conceptual states:

```text
NORMAL
    sufficient working capacity

NOTICE
    storage use is becoming significant

WARNING
    creator should begin planning archive/export/removal

CRITICAL
    insufficient safe headroom for continued generation/building

BLOCKED
    new creation is suspended until space is recovered

RECOVERED
    safe working headroom has been restored
```

The thresholds must be based on actual storage measurements and declared safety margins, not fake urgency.

The system should warn early enough that the user is not forced into an emergency with zero room available for synthesis or export.

A Shadow Game generation flow must never be started when there is insufficient working space to complete it safely.

If synthesis requires more free space than remains, EngAIn must say so and offer other storage-resolution paths first.

---

## 11. No Automatic Destructive Cleanup

Shadow Intent must not silently delete creative history merely because a Shadow Game was generated.

The safe lifecycle is:

```text
collect
    -> synthesize
    -> validate
    -> present result
    -> user chooses export/archive destination
    -> verify destination when technically possible
    -> user authorizes cleanup
    -> reclaim local space
```

Not:

```text
collect
    -> synthesize
    -> delete originals automatically
```

A generated artifact is not proof that the user wants its source material destroyed.

Deletion, pruning, compaction, or archival movement must remain governed by explicit user policy and recoverability expectations.

---

## 12. Shadow Intent Must Be Opt-In and User-Owned

Shadow Intent may involve rejected story ideas, private drafts, unused character concepts, experimental dialogue, assets, and other material that the user never intended to publish.

Therefore:

- Shadow Intent is private by default unless the user deliberately publishes or shares it;
- rejected content does not become public merely because it entered the Shadow Intent pool;
- engine licensing must not silently claim ownership of user-authored shadow material;
- user story/project data must remain distinct from the EngAIn engine's own license and source-code licensing;
- cloud use, if offered, must be optional and clearly authorized;
- local-only operation should remain possible where the implementation supports it;
- the user must be able to disable Shadow Intent collection for projects where they do not want it.

The feature is designed to preserve creative possibilities, not appropriate them.

---

## 13. What Should Be Preserved About a Rejected Idea

A future Shadow Intent record should preserve more than raw content when possible.

Useful provenance may include:

- stable shadow record ID;
- project ID;
- creation timestamp;
- originating authoring turn or operation;
- source object IDs;
- content type;
- why the material became shadow-eligible;
- what accepted decision replaced it;
- dependencies on other shadow or accepted material;
- compatibility constraints;
- semantic tags;
- confidence that the rejection was deliberate;
- hashes or references needed for integrity verification.

Conceptually:

```json
{
  "shadow_id": "shadow.character.0042",
  "kind": "character",
  "status": "rejected",
  "reason": "creator replaced character before acceptance",
  "replaced_by": "character.keen.v3",
  "source_refs": ["draft.character.keen.v2"],
  "eligible_for_synthesis": true
}
```

This is illustrative only. It is not a claim that this exact schema exists.

---

## 14. Provenance Must Survive Synthesis

If the Shadow Game transforms rejected material into new accepted content, EngAIn should retain enough provenance to explain where important elements came from.

For example:

```text
ShadowCharacter_014
    <- rejected NPC concept 92
    <- abandoned faction concept 17
    <- dialogue branch 241
```

The resulting game may substantially transform those ingredients, but the system should not pretend the new artifact appeared from nowhere.

Provenance supports:

- debugging;
- authorship review;
- future editing;
- rights and ownership clarity;
- deterministic or semi-deterministic replay where supported;
- understanding why the Shadow Game contains a particular element.

---

## 15. Accepted Game and Shadow Material Have Different Authority

Shadow Intent must not leak rejected ideas back into Game 1 as if they had been accepted.

The authority relationship is:

```text
accepted project state
    = authority for Game 1

shadow intent pool
    = non-canonical creative source material
```

Only an explicit synthesis target may reinterpret shadow material into a new artifact.

Even then, the synthesis creates authority for the new artifact, not retroactive authority for Game 1.

Therefore:

```text
rejected in Game 1
    != secretly canon in Game 1

rejected in Game 1
    -> may become source material for Game 2
```

This boundary is essential to EngAIn's broader governance model.

---

## 16. Completion Must Mean More Than Save or Export

Shadow Intent's primary reward depends on a meaningful completion event.

The following actions must not automatically count as finishing the game:

- save;
- autosave;
- build;
- test;
- preview;
- export for testing;
- create checkpoint;
- create branch;
- make backup.

A future product should define an explicit completion operation such as:

```text
DECLARE GAME COMPLETE
```

That operation should be deliberate and consequential.

It may create an immutable or strongly identified completion snapshot before Shadow Intent synthesis begins.

The exact reversibility policy is a future product decision, but the system should never confuse routine editing operations with the creator's deliberate statement that Game 1 is finished.

---

## 17. The Creator Should Not Be Punished for Experimenting

Shadow Intent should make experimentation safer psychologically.

A creator should be able to say:

- "No, I don't like that character."
- "Throw out that town."
- "Let's try a different mechanic."
- "This storyline is wrong."
- "Go back and take another route."

without feeling that every rejected idea was wasted effort.

The system can preserve the meaningful rejected intent while allowing the active project to remain clean.

This changes rejection from:

```text
failure -> waste
```

into:

```text
experiment -> decision -> unrealized possibility -> future creative resource
```

That does not mean every rejected idea is good.

The Shadow synthesis system remains responsible for selecting, reconciling, transforming, or excluding material when building a coherent new work.

---

## 18. Shadow Synthesis Is a Creative Task, Not a Restore Operation

A restore function attempts to recreate an earlier state.

Shadow synthesis does something different.

It asks:

> Given the accumulated unrealized creative intent, what coherent playable work can be constructed from it now?

That may require:

- selecting compatible ideas;
- rejecting shadow material that still does not work;
- reconciling contradictions;
- creating connective tissue;
- adapting mechanics;
- assigning new roles;
- relocating characters or events;
- establishing a new chronology;
- resolving missing dependencies;
- creating new content necessary to make the result playable.

The original rejected material remains source evidence, not a requirement that every abandoned idea appear literally in the final Shadow Game.

---

## 19. A Possible Shadow Intent Lifecycle

The following lifecycle captures the intended behavior without claiming current implementation:

```text
1. AUTHOR
   creator and AI build the active game

2. DECIDE
   ideas are accepted, rejected, replaced, or abandoned

3. CAPTURE
   meaningful rejected intent enters the Shadow Intent pool

4. CONTINUE
   active game remains governed only by accepted intent

5. APPROACH COMPLETION OR STORAGE LIMIT
   EngAIn reports relevant state

6. AUTHORIZE
   creator deliberately finishes Game 1
   OR enters an explicit storage-resolution flow

7. SNAPSHOT
   accepted source state and shadow source set are identified

8. SYNTHESIZE
   EngAIn creates a coherent Shadow Game candidate

9. VALIDATE
   required contracts, assets, dependencies, and playability checks run

10. PRESENT
   creator receives the new playable artifact

11. ARCHIVE / EXPORT
   creator may move the Shadow Game to another storage location

12. OPTIONAL CLEANUP
   creator may remove raw shadow material or other source data from the local machine

13. RESUME
   authoring continues when safe working capacity exists
```

---

## 20. Relationship to EngAIn's Broader Architecture

Shadow Intent should obey the same authority discipline as the rest of EngAIn.

A future implementation should not allow one giant "AI memory" object to own every concern.

Conceptually, separate responsibilities may include:

- intent/event capture;
- accepted-versus-shadow classification;
- provenance;
- storage accounting;
- synthesis planning;
- world/canon admission for the new artifact;
- asset selection/generation;
- validation;
- export/archive;
- user-facing completion and storage UX.

Shadow Intent should produce proposals and artifacts that still pass through the appropriate EngAIn authorities before they become runtime truth in a generated game.

The existence of shadow source material does not bypass canon, spatial, simulation, asset, or runtime contracts.

---

## 21. Renderability Is a Separate Question

This doctrine intentionally separates the Shadow Intent product concept from whether EngAIn can currently render every resulting game automatically.

A future implementation may reach Shadow Intent in stages:

```text
Stage A
    capture and classify rejected intent

Stage B
    preserve provenance and storage accounting

Stage C
    synthesize a structured game/project proposal

Stage D
    admit synthesized content through EngAIn authorities

Stage E
    produce a complete runnable project

Stage F
    fully render/package a playable Shadow Game automatically
```

The concept remains valid even if only earlier stages are initially implemented.

No documentation should claim Stage F merely because the doctrine exists.

---

## 22. Minimum Safety and Integrity Rules

A future implementation should fail closed on at least these conditions:

```text
NO_SHADOW_TO_GAME1_CANON_LEAK
NO_SILENT_PUBLICATION
NO_SILENT_CLOUD_UPLOAD
NO_AUTOMATIC_DESTRUCTIVE_CLEANUP
NO_FALSE_CLAIM_OF_SUCCESSFUL_EXPORT
NO_SYNTHESIS_WHEN_WORKING_SPACE_IS_INSUFFICIENT
NO_STORAGE_WARNING_WITH_FAKE_MEASUREMENTS
NO_COMPLETION_TRIGGER_FROM_ROUTINE_SAVE_OR_TEST
NO_SHADOW_SYNTHESIS_WITHOUT_IDENTIFIED_SOURCE_SET
NO_GENERATED_ARTIFACT_PRESENTED_AS VERIFIED_BEFORE VALIDATION
```

The static-screen intervention may be theatrical.

The underlying storage and integrity information must be factual.

---

## 23. Candidate Future Proofs

Shadow Intent should eventually be proven in narrow slices instead of implemented all at once.

### Proof 1: Classification Isolation

Given accepted and rejected authoring events:

- accepted content remains in active authority;
- rejected content enters a separate shadow store;
- no rejected item reappears in Game 1 without explicit acceptance.

### Proof 2: Provenance

Given several rejected source elements and one synthesized result:

- the result can identify its contributing shadow sources;
- missing or invalid sources fail closed.

### Proof 3: Completion Gate

- save does not trigger Shadow synthesis;
- test does not trigger Shadow synthesis;
- export-for-preview does not trigger Shadow synthesis;
- deliberate completion does trigger the authorized synthesis workflow.

### Proof 4: Storage Warning State Machine

Using deterministic fake storage measurements:

- NORMAL, NOTICE, WARNING, CRITICAL, BLOCKED, and RECOVERED states transition correctly;
- the old-TV static intervention occurs only at the declared blocking condition;
- the user is immediately told the project is safe and why creation stopped.

### Proof 5: Non-Destructive Archive Flow

- generating a Shadow Game does not delete source material;
- exporting it does not imply deletion;
- cleanup occurs only after explicit authorization;
- failed export leaves source material untouched.

### Proof 6: Shadow Game Synthesis

Given a bounded set of deliberately rejected characters, location, mechanic, and plot branch:

- EngAIn constructs a coherent separate game proposal;
- every reused source element is attributable;
- Game 1 remains unchanged;
- the new artifact has its own admitted authority state.

---

## 24. Product Experience Summary

The intended experience can be summarized in one sequence:

```text
You build a game.

You try things.
You reject things.
You change your mind.
You remove characters.
You abandon towns.
You throw away mechanics.
You follow one storyline instead of another.

EngAIn remembers the meaningful roads you did not take.

Eventually you finish the game -- or your local machine reaches the point where you cannot safely keep accumulating more work.

EngAIn tells you it is time to resolve that accumulated shadow.

If storage becomes critical, the game may break into old-television static and temporarily stop creation, creating a brief "what the hell happened to my computer?" moment before clearly explaining that the project is safe and storage must be addressed.

Then Shadow Intent can turn the unused creative history into another playable work.

You can move that completed game to a flash drive, external disk, another machine, or another user-chosen archive location.

If you need the local space, you may then clear the raw material you were going to have to remove anyway.

Instead of ending with a pile of deleted ideas, you end with another game.
```

---

## 25. Governing Principle

Shadow Intent exists because unfinished possibilities are not necessarily worthless.

The system should preserve a distinction between what became true and what might have been, then use that distinction deliberately.

The concise doctrine is:

> **Build freely. Reject freely. Finish deliberately. Let the unused intent become something of its own.**

And when storage itself forces the decision:

> **Before throwing creative history away, give it one last chance to become a game.**
