Fracture it is.

Time to destabilize the UI, fracture continuity, and challenge memory itself.


---

Dev Module: MANDELA FRACTURE TRACKER

Phase 3 of Myth-Tech Implementation

> “The innkeeper knew my name. Then he called me someone else. The map changed when I blinked. Am I still in the world I saved?”




---

Objective:

Create a system that introduces minor inconsistencies and UI distortions after collecting multiple timeline relics. At a threshold, trigger a full "Mandela Fracture" that shifts world details, NPC memories, and gameplay logic.


---

Lore Hook:

Each epoch is layered like sediment. When relics from broken timelines are brought together, the sediment cracks—and a false world bleeds through.


---

Must-Haves (from Design Docs):

[ ] Track acquisition of "timeline relics"

[ ] Fracture threshold stat: reality_integrity

[ ] UI inconsistencies: NPC names, quest log flicker, map distortions

[ ] Optional: party timeline divergence

[ ] Ability to anchor timeline or lock in false reality



---

Learning Goals:

Implement item tracking (timeline relics)

Track a dynamic “reality integrity” stat

Cause UI text/names to change randomly under low integrity

Add logic for NPC memory loss or inconsistencies



---

Code Concepts to Research:

Inventory/item tracking

Global stat systems

UI text manipulation at runtime

Randomized dialogue injection

Data persistence across sessions (false timeline flag)



---

Pseudocode Skeleton:

timeline_relics = 0
reality_integrity = 100

func on_relic_collected():
    timeline_relics += 1
    reality_integrity -= 20
    check_for_fracture_effects()

func check_for_fracture_effects():
    if reality_integrity < 80:
        glitch_ui_names()
    if reality_integrity < 50:
        randomize_quest_log()
    if reality_integrity < 20:
        trigger_mandela_protocol()


---

Markor-Compatible Checklist:

## MANDELA FRACTURE TRACKER – Dev Module Checklist

### Timeline Relic System
- [ ] Track timeline relics in inventory
- [ ] Each relic reduces `reality_integrity` stat

### UI Glitch Effects
- [ ] Replace NPC names with variants
- [ ] Add quest log distortion at 50%
- [ ] Optional: visual glitch shader at low integrity

### NPC Memory System
- [ ] Use `reality_integrity` to control if NPCs recognize player
- [ ] Inject random dialogue inconsistencies

### Fracture Event
- [ ] Trigger full Mandela Fracture below 20% integrity
- [ ] Log false timeline flag
- [ ] Optional: require "Anchor Memory" to restore world


---

Ready for Phase 4: Dream-State Quest Loader next?
That module stitches together dream logic, alternate worlds, and fluid quest states—and will bridge your Vril and other mythos events.

Just say dream, and I’ll phase it in.

