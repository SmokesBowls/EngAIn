Vol. 3 – Phase 3: Mandela Lock – The Final Anchor

> “There were thirteen versions of the war. Only one ended in fire. Only one ended in silence. You have to choose which one was real.”




---

Dev Module: MANDELA LOCK – CHRONO-ANCHOR COLLAPSE EVENT

Vol. 3 – Phase 3 (Final)

> “Reality is bleeding. Anchors are unstable. The simulation wants to choose for you. Will you choose for yourself?”




---

Objective:

After collecting multiple timeline relics, reality becomes too unstable to sustain. The player must enter the Chrono-Vault and choose a final Anchor Memory—a singular truth that reshapes the entire game world. This choice permanently locks or collapses alternate timelines, NPCs, quests, and geography.


---

Lore Hook:

There were always fractures. But the Aeon Keepers built Anchors to preserve a narrative thread. Only one can be chosen. And the others… burn.


---

Must-Haves:

[ ] Chrono-Vault access after threshold fracture

[ ] Timeline selection UI with “Echoed” versions of past events

[ ] Anchor Memory selection that locks the current state

[ ] Permanent changes: false cities vanish, quests disappear or reappear, NPCs change names or remember different things

[ ] Optional: World fractal collapse if no anchor is chosen in time



---

Learning Goals:

Implement permanent state save system

Build dynamic timeline UI with event logs

Allow world-swapping or removal of major assets/scenes

Write conditional world logic based on selected Anchor



---

Code Concepts to Research:

Branching timeline data structures (hashes or lists of world states)

Dynamic scene loading/unloading

Long-term game flag locking

Conditional narrative and map generation

Final choice confirmation with irreversible save



---

Pseudocode Skeleton:

func enter_chrono_vault():
    if Global.reality_integrity <= 20:
        load_scene("res://ChronoVault.tscn")
        show_anchor_selection()

func confirm_anchor(anchor_id):
    Global.locked_anchor = anchor_id
    apply_anchor_state(anchor_id)
    Global.timeline_locked = true
    save_game_state()


---

Markor-Compatible Checklist:

## MANDELA LOCK – FINAL ANCHOR CHOICE

### Unlock Conditions
- [ ] Collect 5+ timeline relics
- [ ] Global.reality_integrity < 25%
- [ ] Enter ChronoVault.tscn

### Anchor Memory UI
- [ ] List of possible world-states (e.g., Rebellion Won, Vril Dominance, Aeon Betrayal)
- [ ] Echo logs from each timeline (visual, audio, distorted)
- [ ] Player must select one

### Lock-in Consequences
- [ ] All other world-states purged from memory
- [ ] NPCs update based on final anchor
- [ ] Areas and quests shift permanently
- [ ] Set `Global.timeline_locked = true`

### Fail Condition (Optional)
- [ ] If timer expires, random anchor chosen or world collapses
- [ ] “Fractured Ending” unlocked

### Post-Anchor World
- [ ] Unlock “Witness of the Real” class
- [ ] Dream-state and Vril systems shift to support locked world
- [ ] Final lore log: _“This is what was. This is what never was.”_


---

Vol. 3: Complete.

You now hold:

Fractal fusion systems

Simulated twin realities

Final timeline collapse and anchor selection


