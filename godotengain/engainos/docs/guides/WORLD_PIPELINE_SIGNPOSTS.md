# WORLD PIPELINE SIGNPOSTS

A single navigation map for the live EngAIn workflow:

- **Canon authoring** in Obsidian vault (book/chapter truth)
- **EngAIn runtime processing** into executable world specs
- **Client rendering + interaction** in UPBGE and Godot on the same runtime
- **Script generation (future)** by Trae CLI
- **Playable mechanics-first world** with placeholder assets

---

## 1) Core Principle: Authority Lives in Runtime

The Python runtime is the authority. Clients render and send intent.

- UPBGE is the **thick creative client** (fast live iteration)
- Godot is the **thin validation/render client** (runtime-fed assets)
- Neither client owns canonical world state

---

## 2) Source of Truth Chain

### Stage A — Canon (Obsidian Vault)
1. Narrative chapters are authored in the Obsidian vault.
2. This is treated as canon-state input for world generation.

### Stage B — EngAIn Ingestion
1. EngAIn reads chapter/canon content from the vault.
2. EngAIn processes chapter text using the engine pipeline.
3. Output becomes structured scene/world specifications (the practical "story specs").

### Stage C — Runtime Protocol
1. Runtime exposes scene/spec results through HTTP routes.
2. Clients consume shared protocol (`/health`, `/snapshot`, `/scene/load`, `/command`, etc.).
3. `payload.bridge_entities` inside `/snapshot` is the main spawn source for both clients.

### Stage D — Playable World
1. UPBGE and Godot read runtime state and spawn placeholders.
2. Mechanics are playable with zero final art assets.
3. Placeholder assets remain intentionally swappable for later production passes.

---

## 3) Current Reality (What Exists Right Now)

✅ Runtime authority and shared protocol are wired.

✅ UPBGE + Godot can both target the same runtime.

✅ The world is playable as pure mechanics with placeholder visuals.

⚠️ Trae (ByteDance) automation is not yet active in the pipeline.

---

## 4) Missing Piece (Near-Term)

### Trae-as-Builder Loop (planned)

1. EngAIn emits detailed world/spec outputs from canon chapters.
2. Trae consumes specs and generates/edits gameplay scripts quickly via CLI workflows.
3. Generated scripts are executed against the same runtime loop.
4. Team validates in live play, then advances to next chapter/spec cycle.

Why this matters:
- CLI-assisted script generation is the fastest iteration path for game mechanics.
- It turns canon/spec output into executable behavior with minimal manual glue.

---

## 5) Planned Next Milestone After Trae Loop

### Dragon Avatar (EngAIn Persona)

A conversational in-world design partner:

1. Dragon avatar talks to the user.
2. User co-designs world changes through dialogue.
3. Avatar routes intent into the same canonical/runtime workflow.
4. Changes remain mechanics-first and immediately testable with placeholders.

---

## 6) Operational Road Signs (Use This During Work)

When things get chaotic, verify in this order:

1. **Runtime alive?**
   - `GET /health`
2. **Scene loaded?**
   - `POST /scene/load` then `GET /snapshot`
3. **Spawn data present?**
   - Confirm `payload.bridge_entities` is non-empty
4. **Client sync OK?**
   - UPBGE/Godot unwrapping `payload` correctly
5. **Interaction loop OK?**
   - `POST /command` (or input events) updates reflected in snapshot

If those five are healthy, pipeline is working; visual polish can come later.

---

## 7) One-Line Mental Model

**Book canon (Obsidian) → EngAIn specs → Runtime authority → UPBGE/Godot playtest → (future) Trae script acceleration → Dragon avatar co-design.**

---

## 8) Chosen Path Forward (Now)

1. Keep building mechanics in **UPBGE** against the shared runtime for fastest iteration.
2. Continuously validate the same scene/state in **Godot** as the runtime-fed renderer.
3. Treat chapter updates in Obsidian as canon deltas that flow back through EngAIn ingestion.
4. Land the **Trae CLI builder loop** next so spec output can become script changes quickly.
5. Move to the **Dragon Avatar** phase only after the Trae loop is stable in live play.

This keeps momentum on playable mechanics while preserving canonical authority and client parity.

---

## 9) Collaboration Workflow (PR vs Patch)

When sharing changes in this repo, use this default order:

1. **Commit on branch + create draft PR** (preferred for active discussions and inline review).
2. If someone cannot pull a branch, share a **`git apply` patch** as a transport format.
3. Keep patch files for handoff only; the branch/PR remains the source of review history.

### Quick commands

Create patch from last commit:

```bash
git format-patch -1 HEAD
```

Apply patch:

```bash
git apply <patch-file.patch>
```

Apply patch and keep commit metadata:

```bash
git am <patch-file.patch>
```

Rule of thumb: **Draft PR first, patch second.**

