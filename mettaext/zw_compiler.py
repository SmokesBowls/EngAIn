#!/usr/bin/env python3
import json
import sys
import re
from pathlib import Path


# -----------------------------
# Canon phrase matchers (STRICT)
# -----------------------------

# -----------------------------
# Module: World State
# -----------------------------
def match_world_state(line):
    l = line.lower()
    res = []
    if "planetary core stabilizes" in l:
        res.append({
            "@type": "STATE_DELTA",
            "@where": "Earth/Core",
            "state": {"core_stability": "stabilized"}
        })
    if "magnetic field strength approaching sustainable thresholds" in l:
        res.append({
            "@type": "STATE_DELTA",
            "@where": "Earth/Atmosphere",
            "state": {"magnetic_field": "approaching_sustainable"}
        })
    if "atmospheric composition shifting toward oxygen-nitrogen balance" in l:
        res.append({
            "@type": "STATE_DELTA",
            "@where": "Earth/Atmosphere",
            "state": {"atmosphere": "oxygen_nitrogen_balance"}
        })
    if "water coverage approximately seventy-two percent" in l:
        res.append({
            "@type": "CONTEXT",
            "@where": "Earth/Surface",
            "metrics": {"water_coverage": 0.72}
        })
    if "two major continental masses" in l:
        res.append({
            "@type": "CONTEXT",
            "@where": "Earth/Surface",
            "metrics": {"continental_masses": 2}
        })
    if "three thousand, four hundred and seventeen years" in l:
        res.append({
            "@type": "CONTEXT",
            "@when": "t-3417y",
            "metrics": {"years_since_shattering": 3417}
        })
    return res

# -----------------------------
# Module: Embodiment
# -----------------------------
def match_embodiment(line):
    l = line.lower()
    res = []
    if "physical form is limitation" in l:
        res.append({
            "@type": "RULE",
            "@agent": "Korath",
            "constraint": {
                "physical_form": "limitation",
                "preferred_state": "non_physical"
            }
        })
    if "nephoretti were manifesting" in l:
        res.append({
            "@type": "EVENT",
            "@when": "t0",
            "event": "nephoretti_manifestation_started"
        })
    if "nephoretti leaped" in l:
        res.append({
            "@type": "EVENT",
            "@when": "t1",
            "event": "nephoretti_deployed_to_physical_plane"
        })
    if "the body began forming" in l:
        res.append({
            "@type": "EVENT",
            "event": "embodiment_started"
        })
    if "falling through actual atmosphere" in l:
        res.append({
            "@type": "EVENT",
            "event": "entered_physical_atmosphere"
        })
    if "landing was violent" in l:
        res.append({
            "@type": "EVENT",
            "event": "surface_impact"
        })
    return res

# -----------------------------
# Module: Entity Evolution
# -----------------------------
def match_entity_evolution(line):
    l = line.lower()
    res = []
    if "the giants." in l:
        res.append({
            "@type": "ENTITY_INTRODUCTION",
            "entity": "Giants",
            "origin": "Pelagor_transformed"
        })
    return res

# -----------------------------
# Module: Role Assignment
# -----------------------------
def match_role_assignment(line):
    l = line.lower()
    res = []
    if "you are prime" in l:
        res.append({
            "@type": "ROLE_ASSIGNMENT",
            "entity": "Senareth",
            "role": "Prime"
        })
    return res

# -----------------------------
# Module: Interactions
# -----------------------------
def match_interactions(line):
    l = line.lower()
    res = []
    if "afraid" in l and "giant" in l:
        res.append({
            "@type": "RULE",
            "agent": "Giants",
            "constraint": "fear_response_to_nephoretti"
        })
    if '"listen,"' in l:
        res.append({
            "@type": "INTERACTION",
            "source": "Senareth",
            "target": "Nephoretti",
            "interaction": "command",
            "effect": "attention"
        })
    if '"gather the others,"' in l:
        res.append({
            "@type": "INTERACTION",
            "source": "Senareth",
            "target": "Nephoretti",
            "interaction": "command",
            "effect": "assembly_coordination"
        })
    if 'they formed a loose semicircle at the tree line' in l:
        res.append({
            "@type": "INTERACTION",
            "source": "Giants",
            "target": "Nephoretti",
            "interaction": "fear_response",
            "effect": "maintain_distance"
        })
    if '"we wait,"' in l:
        res.append({
            "@type": "INTERACTION",
            "source": "Senareth",
            "target": "Nephoretti",
            "interaction": "command",
            "effect": "hold_position"
        })
    return res

# -----------------------------
# Module: Paradox Engine Systems (Ch 58)
# -----------------------------
def match_paradox_engine_systems(line):
    l = line.lower()
    res = []
    if "it is a paradox engine" in l:
        res.append({
            "@type": "STATE_DELTA",
            "state": {"composition": "paradox_engine"}
        })
    if "forty-seven minutes" in l and "pulse" in l:
        res.append({
            "@type": "EVENT",
            "event": "white_sky_pulse",
            "interval": "47_minutes"
        })
    if "cocoon of crystallized stellar" in l:
        res.append({
            "@type": "STATE_DELTA",
            "state": {"geralt_status": "solar_fusion_cocoon"}
        })
    if "the decoy will require staging" in l:
        res.append({
            "@type": "ENTITY_EVOLUTION",
            "entity": "Clone",
            "role": "decoy"
        })
    if "gpt—will serve here" in l:
        res.append({
            "@type": "ROLE_ASSIGNMENT",
            "entity": "Mr. GPT",
            "role": "decoy_operator"
        })
    if "conduit for the energy she steals" in l:
        res.append({
            "@type": "ROLE_ASSIGNMENT",
            "entity": "Geralt",
            "role": "sun_bound_conduit"
        })
    return res

# -----------------------------
# Module: War Systems (Ch 102/103)
# -----------------------------
def match_war_systems(line):
    l = line.lower()
    res = []
    if "entire war parties from each tribe" in l:
        res.append({
            "@type": "EVENT",
            "event": "faction_deployment_started"
        })
    if "awakening for war was terrible to behold" in l:
        res.append({
            "@type": "STATE_DELTA",
            "state": {"war_state": "active"}
        })
    if "dragon mail complete and singing with power" in l:
        res.append({
            "@type": "STATE_DELTA",
            "state": {"dragon_mail_status": "synthesized"}
        })
    if "dark sun" in l and "pulsed with malevolent intent" in l:
        res.append({
            "@type": "EVENT",
            "event": "dark_sun_pulse",
            "effect": "temporal_distortion"
        })
    if "fragmented child, who chose division over unity" in l:
        res.append({
            "@type": "RULE",
            "agent": "Viên",
            "constraint": "forced_fragmentation"
        })
    if "battlefield began to fragment" in l:
        res.append({
            "@type": "STATE_DELTA",
            "state": {"battlefield_state": "fragmented"}
        })
    if "proven yourselves worthy of the real war" in l:
        res.append({
            "@type": "EVENT",
            "event": "queen_escalation",
            "effect": "war_state_transition"
        })
    return res

# -----------------------------
# Registry
# -----------------------------
ZON_MATCHERS = [
    match_world_state,
    match_embodiment,
    match_entity_evolution,
    match_role_assignment,
    match_interactions,
    match_paradox_engine_systems,
    match_war_systems
]

# -----------------------------
# Extract from segments
# -----------------------------

def extract_zon_blocks(segments):
    out = []
    for seg in segments:
        text = seg.get("text", "")
        for fn in ZON_MATCHERS:
            results = fn(text)
            if results:
                if isinstance(results, list):
                    out.extend(results)
                else:
                    out.append(results)
    return out


# -----------------------------
# ZW-C5: Validation Layer
# -----------------------------

def run_validation(original_entities, segments, zon_blocks, valid_entities, spatial_hints):
    warnings = []
    validation = {
        "unknown_entity_candidates": [],
        "missing_spatial_candidates": [],
        "orphan_references": [],
        "empty_categories": []
    }

    canon_lower = set(x.lower() for x in CANON_ENTITIES)
    all_canon_places = set(x.lower() for x in SPATIAL_MAPPING.values())

    # 1. Unknown entity candidates
    unknowns = set()
    for e in original_entities:
        if isinstance(e, str):
            if e.lower() not in canon_lower:
                unknowns.add(e)
        elif isinstance(e, dict) and "entity_id" in e:
            if e["entity_id"].lower() not in canon_lower:
                unknowns.add(e["entity_id"])
    validation["unknown_entity_candidates"] = sorted(list(unknowns))

    # 2. Missing spatial candidates
    if len(spatial_hints) == 0:
        place_keywords = ["mountain", "chamber", "sun", "sky", "cavern", "plain", "room"]
        candidates = set()
        for seg in segments:
            text = seg.get("text", "")
            for word in place_keywords:
                if re.search(r'\b' + word + r'\b', text, re.IGNORECASE):
                    candidates.add(word)
        if candidates:
            validation["missing_spatial_candidates"] = sorted(list(candidates))
            warnings.append(f"No spatial hints found, but chapter contains place candidates: {', '.join(sorted(list(candidates)))}")
        else:
            warnings.append("No spatial hints found.")

    # 3. Orphan zon block references
    for idx, block in enumerate(zon_blocks):
        for field in ["@agent", "source", "target", "entity"]:
            if field in block:
                val = block[field]
                if val.lower() not in canon_lower:
                    validation["orphan_references"].append(f"Block {idx} references unknown entity '{val}' in '{field}'")
        
        if "@where" in block:
            val = block["@where"]
            if val.lower() not in all_canon_places:
                validation["orphan_references"].append(f"Block {idx} references unknown place '{val}' in '@where'")

    # 4. Empty extraction categories
    if len(zon_blocks) == 0:
        validation["empty_categories"].append("zon_blocks")
        warnings.append("No zon_blocks extracted.")
    if len(valid_entities) == 0:
        validation["empty_categories"].append("entities")
        warnings.append("No entities found.")

    return validation, warnings


# -----------------------------
# Normalize scene base
# -----------------------------

def build_base_scene(doc_id):
    return {
        "doc_id": doc_id,
        "scene_id": doc_id,
        "title": None,
        "where": None,
        "when": None,
        "entities": [],
        "segments": [],
        "beats": [],
        "zon_blocks": []
    }


# -----------------------------
# Canon Entities & Normalization
# -----------------------------

CANON_ENTITIES = [
    "Lyaris",
    "Theron",
    "Vaelith",
    "Mordain",
    "Syreth",
    "Korath",
    "Nephoretti",
    "Pelagor",
    "Aeon Keepers",
    "Senareth",
    "Giants",
    "Geralt",
    "Zypher",
    "Kulla",
    "Clone",
    "Mr. GPT"
]

NAME_FIXES = {
    "Neferati": "Nephoretti",
    "neferati": "Nephoretti"
}

def normalize_canon_names(segments):
    for seg in segments:
        if "text" in seg:
            for bad, good in NAME_FIXES.items():
                seg["text"] = seg["text"].replace(bad, good)

def extract_canon_entities(segments):
    found = set()
    for seg in segments:
        text = seg.get("text", "")
        for canon in CANON_ENTITIES:
            # Use word boundaries for clean matching
            if re.search(r'\b' + re.escape(canon) + r'\b', text, re.IGNORECASE):
                found.add(canon)
    return sorted(list(found))


# -----------------------------
# Spatial Mapping
# -----------------------------

SPATIAL_MAPPING = {
    r"\bethereal realm\b": "Ethereal Realm",
    r"\bakashic records\b": "Akashic Records",
    r"\bplanetary core\b": "Earth/Core",
    r"\b(atmospheric composition|atmosphere)\b": "Earth/Atmosphere",
    r"\bwater coverage\b": "Earth/Surface",
    r"\bcontinental masses\b": "Earth/Surface/ContinentalMasses",
    r"\bcoastal regions\b": "Earth/Surface/CoastalRegions",
    r"\btidal pools\b": "Earth/Surface/TidalPools",
    r"\bthe veil\b": "Ethereal Realm/Veil",
    r"\bvrill convergence\b": "Ethereal Realm/VrillConvergencePoints",
    r"\bmountain\b": "Tidecaller's Mountain",
    r"\bchamber\b": "Tidecaller's Mountain/ParadoxChamber",
    r"\bcavern\b": "Tidecaller's Mountain/Cavern",
    r"\bsky\b": "Earth/Sky/WhiteSky",
    r"\bsun\b": "SolarSystem/Sun/Core",
    r"\bcocoon\b": "SolarSystem/Sun/FusionCocoon",
    r"\bmars\b": "Mars",
    r"\bvoid spire\b": "Mars/VoidSpire",
    r"\bcanyon\b": "Mars/CanyonKillingField",
    r"\bcitadel\b": "Mars/CrimsonCitadel",
    r"\bunderground\b": "Mars/Underground",
    r"\bdark sun\b": "Mars/DarkSunOrbit"
}

def extract_spatial_hints(segments):
    found = set()
    for seg in segments:
        text = seg.get("text", "")
        for pattern, canon_path in SPATIAL_MAPPING.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.add(canon_path)
    return sorted(list(found))


# -----------------------------
# Main compile
# -----------------------------

def generate_report(zon_blocks, valid_entities, spatial_hints, original_entities, segments):
    validation, warnings = run_validation(original_entities, segments, zon_blocks, valid_entities, spatial_hints)
    report = {
        "compiler_version": "0.5",
        "zon_blocks_count": len(zon_blocks),
        "entities_count": len(valid_entities),
        "spatial_hints_count": len(spatial_hints),
        "warnings": warnings,
        "validation": validation
    }
    return report

def compile_file(in_path, out_path):
    p = Path(in_path)

    if p.suffix == ".json" or p.name.endswith(".zonj"):
        data = json.loads(p.read_text())

        segments = data.get("=segments", []) or data.get("segments", [])
        
        raw_ents = data.get("entities", [])
        if isinstance(raw_ents, dict):
            original_entities = list(raw_ents.keys())
        else:
            original_entities = raw_ents
        
        # 1. Normalize canon names in source/segments
        normalize_canon_names(segments)
        
        # 2. Rebuild @entities from known canon names
        valid_entities = extract_canon_entities(segments)
        data["@entities"] = valid_entities
        data["entities"] = valid_entities
        
        # 3. Generate zon_blocks
        zon_blocks = extract_zon_blocks(segments)

        # 4. Generate spatial_hints
        spatial_hints = extract_spatial_hints(segments)
        data["spatial_hints"] = spatial_hints

        # Preserve original structure
        data["zon_blocks"] = zon_blocks
        data["compiler_report"] = generate_report(zon_blocks, valid_entities, spatial_hints, original_entities, segments)
        
        # Ensure output directory exists
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)

        Path(out_path).write_text(json.dumps(data, indent=2))
        print(f"[OK] augmented scene -> {out_path}")
        return

    # Raw text mode (fallback)
    lines = p.read_text().splitlines()
    segments = [{"text": l} for l in lines]
    
    normalize_canon_names(segments)
    valid_entities = extract_canon_entities(segments)

    scene = build_base_scene(p.stem)
    scene["segments"] = segments
    scene["@entities"] = valid_entities
    scene["entities"] = valid_entities
    scene["zon_blocks"] = extract_zon_blocks(segments)
    scene["spatial_hints"] = extract_spatial_hints(segments)
    scene["compiler_report"] = generate_report(scene["zon_blocks"], valid_entities, scene["spatial_hints"], [], segments)
    
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(scene, indent=2))
    print(f"[OK] built scene -> {out_path}")


# -----------------------------
# Entry
# -----------------------------

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: zw_compiler.py input output")
        sys.exit(1)

    compile_file(sys.argv[1], sys.argv[2])
