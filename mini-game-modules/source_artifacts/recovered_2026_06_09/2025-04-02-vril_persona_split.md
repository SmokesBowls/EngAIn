Phase 2 incoming: Vril Persona Split.
This is where it gets spicy—identity fragmentation, dual states, dream hijacks. We're not just tracking a stat anymore—we're rewriting the self.


---

Dev Module: VRIL PERSONA SPLIT

Phase 2 of Myth-Tech Implementation

> “When the glyphs spoke, I woke up in a room I didn’t recognize. My hands were bloody. My mouth was smiling.”




---

Objective:

Create a system where the player develops a second persona upon triggering the Vril Rebellion event. The alter-character may appear in dreams, overwrite player decisions, or influence dialogue/events.


---

Lore Hook:

The Vril didn’t die. They encoded themselves into subconscious memory. When you read the glyphs… they remember you.


---

Must-Haves (from Design Docs):

[ ] Event trigger: read 3 glyphs

[ ] Alter-character state (boolean: has_split_persona = true)

[ ] Dream event system (random chance or forced during sleep)

[ ] Shift control or narrative to alternate self during dreams

[ ] Optional: Moral conflict dialogue choices or overwritten actions



---

Learning Goals:

Set up event-driven variable flags

Create a simple sleep/dream system

Create dialogue/event overrides based on character state

Switch control to alternate logic path or character during dreams



---

Code Concepts to Research:

Boolean flags + event systems (has_split_persona)

Scene switching / dream transitions

Branching dialogue trees

Conditional choice systems

Save/load altered state (if persistent between sessions)



---

Pseudocode Skeleton:

# When player reads a Nephoretti glyph
func on_glyph_read():
    glyphs_read += 1
    if glyphs_read >= 3:
        has_split_persona = true
        show_message("Something has awakened...")

# When player sleeps
func on_sleep():
    if has_split_persona and randf() > 0.5:
        enter_dream_state()

func enter_dream_state():
    current_scene = "VrilDream"
    control_switch_to_alter_persona()
    play_reversed_audio_logs()


---

Markor-Compatible Checklist:

## VRIL PERSONA SPLIT – Dev Module Checklist

### Trigger System
- [ ] Track Nephoretti glyphs read
- [ ] Trigger persona split at 3 glyphs
- [ ] Set `has_split_persona` = true

### Dream System
- [ ] Create sleep interaction or rest mechanic
- [ ] Random chance to enter Vril dream realm
- [ ] Load alternate scene or overlay (e.g. Simulacrum War)

### Alter-Character
- [ ] Introduce altered narrative perspective
- [ ] Switch choices/dialogue based on split
- [ ] Optional: log overwritten actions or wake up in new location


---

Want me to drop Phase 3: Mandela Fracture Tracker next? That one gets wild with UI flickers, reality stats, and timeline divergence flags.

Or we can go with Dream-State Quest Loader and lock down how Vril and other realities pull the player into alt quests.

Just say fracture or dream, and I’ll summon the next module.

