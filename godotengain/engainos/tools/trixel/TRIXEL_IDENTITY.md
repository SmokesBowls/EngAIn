# TRIXEL_IDENTITY.md

**Location:** `tools/trixel/`  
**Authority:** Descriptive (describes reality, not prescribes behavior)  
**Purpose:** Prevent future confusion about what Trixel is and is not

---

## What Trixel Is (Empirically Verified)

**Trixel is a long-running, stateful, perceptual creative agent whose output is experience, not artifacts.**

Verified by inspection of actual code structure:
- `AutonomousCreativeMemory` - maintains creative state across sessions
- `CreativePhase` - tracks exploration, reflection, style development
- `CreativeAction` - records artistic decisions with reasoning
- `OptimizedTrixelCanvas` - perception surface for visual feedback
- `RealTimeCreativeFeedback` - adaptive response to creative intensity
- `EnhancedTrixelComposer` - orchestrates creative cycles
- `EnhancedComposerUI` - interactive creative environment

**Core Behavior:**
- Explores visual space autonomously
- Remembers past creative decisions
- Reflects on artistic success/failure
- Adapts style over time
- Develops signature techniques
- Provides visual judgment (advisory)

**Output:**
- Creative experience (memory, learning, style evolution)
- Visual judgment (advisory opinions on quality)
- Artistic annotations (semantic metadata)

**NOT output:**
- Law enforcement
- Final acceptance decisions
- Runtime game state
- Mesh binding authority

---

## What Trixel Is NOT

### ❌ NOT a Validator
Trixel judges quality but **does not enforce acceptance**.

**Law enforcement is:** `core/mesh_intake.py`  
**Trixel's role is:** Advisory opinion on artistic merit

### ❌ NOT a Pipeline
Trixel is not a linear processing chain.

It is a **creative agent** that:
- Iterates on ideas
- Backtracks when dissatisfied  
- Develops techniques over time
- Has no "final output" until satisfied

### ❌ NOT a Service
Trixel is not stateless request/response.

It is a **persistent agent** that:
- Maintains memory across sessions
- Builds artistic signature
- Learns from experience
- Has creative preferences

### ❌ NOT the Authority
Trixel advises; it never decides.

**Decision authority is:** `core/mesh_intake.py` (HARD GATE)  
**Trixel's authority is:** Visual expertise (advisory)

---

## The Naming Mistake (Post-Mortem)

**What Happened:**
Everyone used the name "Trixel" and made rules and code, but nobody stopped to look and see what Trixel is doing.

**The Assumption:**
- Name: "Composer" → Must be a coordinator
- Name: "Pipeline" → Must be linear
- Name: "Validator" → Must be authoritative

**The Reality:**
Trixel is none of those things. The code revealed a **creative agent runtime** with memory, perception, and learning.

**The Fix:**
Stop assuming from names. Inspect actual behavior.

---

## Import Truth (Verified by System)

```python
# ✅ CORRECT - Import what actually exists
from tools.trixel import AutonomousCreativeMemory
from tools.trixel import CreativePhase, CreativeAction
from tools.trixel import EnhancedTrixelComposer

# ❌ WRONG - Import what we wish existed
from tools.trixel import TrixelComposer  # This class doesn't exist
```

**Why this matters:**
The system told us what it is through its symbols. We listened.

---

## Architecture Position (Permanent)

```
Law Authority:
  core/mesh_intake.py ← Decides acceptance/rejection (HARD GATE)

Advisory/Judgment:  
  tools/trixel/ ← Judges artistic quality (ADVISORY)

Execution:
  godot/ ← Renders approved meshes only (OVERLAY)

History:
  archive/trixel_notes/ ← Read-only research
```

**Critical Enforcement (Verified):**
```
✓ CRITICAL: Core does not import from tools/
```

**What this means:**
No matter how complex Trixel becomes (UI, memory, learning, feedback), **the law cannot be contaminated**.

This is the difference between:
- "AI-assisted tools" and
- "Governed AI systems"

---

## Trixel's Role in Mesh Pipeline

**Trixel provides:**
1. **Semantic extraction** from narrative → visual intent
2. **Visual validation** of generated mesh → advisory judgment
3. **Artistic annotation** → ZW metadata about visual quality

**Trixel does NOT provide:**
1. ~~Acceptance/rejection authority~~ → That's mesh_intake
2. ~~Mesh generation~~ → That's Wings 3D / procedural tools
3. ~~Runtime binding~~ → That's core/
4. ~~Rendering~~ → That's Godot

**The flow:**
```
Narrative → Trixel (extract intent) 
         → Wings (build mesh)
         → MeshLab (clean)
         → Trixel (judge quality) ← ADVISORY
         → mesh_intake (decide) ← AUTHORITATIVE
         → core (bind)
         → Godot (render)
```

---

## When to Use Trixel

**Use Trixel when:**
- Converting narrative description → visual intent
- Judging artistic quality of generated assets
- Providing semantic annotations for visual elements
- Developing creative style over time
- Learning from visual feedback

**Do NOT use Trixel when:**
- Enforcing acceptance standards → Use mesh_intake
- Making final decisions on asset validity → Use mesh_intake
- Generating meshes directly → Use Wings/procedural/AI
- Managing runtime state → Use core/
- Rendering → Use Godot

---

## Future Agent Roles (If Needed)

If you need a **separate semantic judge** (distinct from creative exploration):

**Create a new agent:**
- Name: `SemanticJudge` or `VisualIntentJudge` or `TrixelJudge`
- Location: `tools/judges/` (new directory)
- Role: Pure judgment without creative state
- NOT named "Trixel" (that name is taken)

**Why separate:**
Trixel is a **creative agent** (explores, remembers, adapts).  
A judge is a **stateless evaluator** (receives input, outputs score).

These are different roles. Don't conflate them.

---

## The Quiet Win

This verification process revealed:
```
✓ CRITICAL: No Godot imports in tools/
✓ CRITICAL: Core does not import from tools/
✓ ESSENTIAL: All files in correct locations
✓ ESSENTIAL: No law contamination
```

**What this enables:**
- Trixel can evolve freely (add UI, memory, learning)
- Core law remains uncontaminated
- No circular dependencies
- Clear separation of concerns
- Reality-driven development

---

## Final Truth

**Trixel didn't fail to be defined early.**  
**The system revealed its nature, and we reorganized around truth instead of intent.**

That is how real engines stabilize.

---

## Maintenance Rules

### ✅ DO:
- Let Trixel explore, remember, adapt
- Use Trixel for advisory visual judgment
- Keep Trixel in tools/ (never move to core/)
- Import FROM core (mesh_intake, mesh_manifest)
- Add creative features (memory, learning, style)

### ❌ DON'T:
- Make Trixel enforce acceptance decisions
- Import Trixel INTO core
- Call Trixel from Godot
- Give Trixel runtime authority
- Conflate creative exploration with law enforcement

---

## Documentation Status

**This document is:**
- Descriptive (not prescriptive)
- Empirically verified (not assumed)
- Permanent (not draft)

**This document prevents:**
- Future "helpful" refactors that destroy clarity
- Assumption-driven development
- Name-driven architecture decisions
- Law contamination

**This document enables:**
- Reality-driven development
- Clear role separation
- Free evolution within boundaries
- Governed AI systems (not just AI-assisted tools)

---

**Date:** 2026-01-18  
**Status:** LOCKED  
**Authority:** Empirical verification via system inspection  
**Enforcement:** Import boundaries, directory structure, verification scripts
