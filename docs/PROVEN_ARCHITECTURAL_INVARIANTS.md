# Proven Architectural Invariants

This file contains only constitutional constraints that have been demonstrated through testing and evidence. They are not theoretical suggestions; they are documented facts about how the system behaves.

---

## 1. Blender Authority Boundary

**Invariant:**

Asset generators do not own canon.

* Catalog = authority (read-only truth)
* Translator = meaning → build parameters (copies only, no mutation)
* Execution contract = filtered worker payload
* Generator = geometry (dumb builder)

**Metadata:**

* Status: Proven
* Date Proven: 2026-06-04
* Evidence Level: Runtime Demonstration

**Evidence Trail:**

Pipeline demonstrated:

```text
asset_catalog.py
    ↓ get_asset_record() returns deep copy
translators/star_needle.py
    ↓ translate_star_needle() produces build_spec
execution_spec filter
    ↓ filters to {height_m, base_radius_m, star_count}
generate_star_needle.py
    ↓ produces Blender .blend file
```

Proof artifacts:

* `/tmp/engain_star_needle_out.blend` (manual parameters)
* `/tmp/engain_authority_needle.blend` (authority-driven)

Both produced equivalent geometry, proving the generator does not need to know what a Star Needle is. Forward compatibility was demonstrated when the generator successfully ignored semantic fields (`nexus_core_enabled`, `damage_state`) it was not yet taught to consume.

**Failure That Led To Discovery:**

* **Failure:** Translator output was passed directly into `generate_star_needle()`.
* **Result:** `TypeError: unexpected keyword argument 'nexus_core_enabled'`
* **Discovery:** Semantic truth and execution contract cannot be the same layer. The semantic side evolves independently of the geometric side.
* **Resolution:** Execution filter inserted between translator and generator, ensuring forward compatibility.

---

## 2. WorldField Terrain Authority Boundary

**Invariant:**

WorldField owns float terrain truth.
Blender terrain generator owns geometry only.
Blender must not repair, reinterpret, or beautify terrain truth.

**Metadata:**

* Status: Proven
* Date Proven: 2026-06-05
* Evidence Level: Runtime Demonstration

**Evidence Trail:**

Pipeline demonstrated:

```text
world_field_nucleus.py
    ↓ WorldField.apply_operator() + GodotWorldFieldBridge
generate_worldfield_terrain.py
    ↓ reads height_values (float grid)
    ↓ builds vertices + faces
    ↓ produces Blender .blend file
```

Proof artifacts:

* `/tmp/engain_worldfield_hill.blend` (first run - plateau)
* `/tmp/engain_worldfield_hill.blend` (second run - hill)

**The Critical Proof:**

The same Blender generator produced two different results without modification:

1. **First Run:** `WorldField._apply_add()` used flat strength addition.
   * Result: Flat-topped plateau mesh.
   * Generator behavior: Correctly rendered the truth.

2. **Authority Fix:** `WorldField._apply_add()` changed to radial falloff.
   * Change location: `world_field_nucleus.py` only.
   * Generator changes: None.

3. **Second Run:** Same generator, same execution contract.
   * Result: Smooth radial hill mesh.
   * Generator behavior: Correctly rendered the new truth.

**Why This Matters:**

Blender acted as a perfect mirror. It did not:

* Auto-smooth the plateau to hide ugly data.
* Apply heuristics to "improve" the terrain.
* Cache or reuse the first result.

It rendered exactly what WorldField produced, both times. This proves the generator is a dumb worker, not an intelligent interpreter.

**Failure That Led To Discovery:**

* **Failure:** First terrain mesh was a plateau, not a hill.
* **Result:** Visual evidence exposed a flaw in `WorldField._apply_add()` operator.
* **Discovery:** The geometry layer reveals authority truth. If the truth is wrong, the mesh is wrong. Blender is a truth viewer, not a truth fixer.
* **Resolution:** Fixed `WorldField._apply_add()` with distance-based falloff. Generator required zero changes.

**Architectural Guarantee:**

Future changes to WorldField operators (add, subtract, smooth, clamp) will automatically propagate to Blender geometry without generator modification. The generator consumes float truth; it does not own it.

---

## Blender I/O Contract: Procedural Checkpoints

**Contract:**

Blender generator tools use `.blend` files as procedural checkpoints.

* `blend_file` = seed / template / checkpoint input
* `save_as` = generated cache / checkpoint output
* artist work files are never generator output targets

**Rules:**

* `blend_file` must exist before generation begins.
* `blend_file` provides a known Blender starting state.
* `save_as` is machine-owned and may be overwritten.
* Generated cache/checkpoint files should use a machine-owned suffix such as `_cache.blend` or another explicit procedural checkpoint name.
* Human-authored work files must not be passed as `save_as`.
* Work files may link or append generated cache/checkpoint files.
* The generator may replace generated geometry in machine-owned cache/checkpoint files, but must not own human edits.

**Ownership:**

```text
WorldField / Catalog / Contract
    ↓
Generator
    ↓
*_cache.blend / procedural checkpoint .blend
    ↓
Linked/Appended into
artist_work.blend / Godot prep file
```

**Example File Roles:**

```text
engain_empty.blend
    clean seed/template

engain_worldfield_hill.blend
    generated cache/checkpoint

engain_worldfield_hill_work.blend
    artist/Godot prep file, never overwritten
```

**Invariant Relationship:**

This contract preserves the authority boundary:

* Authority owns truth.
* Generator bakes truth into cache geometry.
* Artist/Godot work files consume the cache.
* Generator never edits the final work file.

**Failure Prevented:**

Without this contract, `blend_file` is a hidden dependency:

```text
required by wrapper
not meaningful to generator
easy to forget
easy to break
```

With this contract, `blend_file` becomes a procedural seed, and `save_as` becomes a procedural checkpoint:

```text
Input .blend gives Blender a known starting state.
Generator writes output .blend as the new procedural checkpoint.
```

**Final Ownership Rule:**

```text
template/cache files are machine-owned
work files are human-owned
```
Yes. I'll append this operational contract to the `docs/PROVEN_ARCHITECTURAL_INVARIANTS.md` file now.

```bash
cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn

cat >> docs/PROVEN_ARCHITECTURAL_INVARIANTS.md << 'EOF'

---

## Blender I/O Contract: Procedural Checkpoints

**Contract:**

Blender generator tools use `.blend` files as procedural checkpoints.

* `blend_file` = seed / template / checkpoint input
* `save_as` = generated cache / checkpoint output
* artist work files are never generator output targets

**Rules:**

* `blend_file` must exist before generation begins.
* `blend_file` provides a known Blender starting state.
* `save_as` is machine-owned and may be overwritten.
* Generated cache files should use a `_cache.blend` suffix.
* Human-authored work files must not be passed as `save_as`.
* Work files may link or append generated cache files.
* The generator may replace generated geometry, but must not own human edits.

**Ownership:**

```text
WorldField / Catalog / Contract
    ↓
Generator
    ↓
*_cache.blend
    ↓
Linked/Appended into
artist_work.blend
```

**Invariant Relationship:**

This contract preserves the authority boundary:

* Authority owns truth.
* Generator bakes truth into cache geometry.
* Artist/Godot work files consume the cache.
* Generator never edits the final work file.

**Failure Prevented:**

Without this contract, `blend_file` is a hidden dependency: required by the wrapper but unclear in purpose.

With this contract, `blend_file` becomes a procedural seed, and `save_as` becomes a procedural checkpoint.
EOF
```

The contract has been appended. The document now contains:

1. **Blender Authority Boundary** (Asset generators don't own canon)
2. **WorldField Terrain Authority Boundary** (Float truth → geometry)
3. **Blender I/O Contract: Procedural Checkpoints** (blend_file as seed, save_as as cache)

This completes the operational framework for the Blender subsystem while maintaining the proven invariants.
