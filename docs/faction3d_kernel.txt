# faction3d_kernel.gd
# Pure functional mr kernel for Faction3D subsystem
# Handles 20 canonical factions across 6 layers with phase-gated progression
# Pattern: Immutable snapshot-in/snapshot-out, no side effects, deterministic logic only

class_name Faction3DKernel
extends RefCounted

# ============================================================================
# CANONICAL FACTION CONSTANTS
# ============================================================================

enum FactionID {
	# DRAGONWAYNE / COSMIC CONSTANTS (2)
	DRAGONS,
	GRAVITONS,
	
	# ETHEREAL (2)
	ETHEREAL_KEEPERS,
	ELOHIM,
	
	# VOID (1)
	DRACO,
	
	# INTERSTELLAR (1)
	GALACTIC_FEDERATION,
	
	# MATERIAL - RESISTANCE (6)
	PLEADIANS,
	NORDICS,
	MARTIANS,
	ORIONS,
	SIRIANS,
	ANDROMEDANS,
	
	# MATERIAL - ANTAGONISTS (2)
	REPTILIANS,
	ANUNNAKI,
	
	# MATERIAL - EARTH FACTIONS (3)
	EARTH_CONCORDAT,
	BLACK_VEIL_DIRECTORATE,
	AWAKENING_NETWORK,
	
	# DEEP / LEY (2)
	VEILED_CONCLAVE,
	CONTINUITY_INITIATIVE,
}

enum Layer {
	DRAGONWAYNE,    # Cosmic constants
	ETHEREAL,     # Soul/consciousness layer
	VOID,         # Dimensional rifts
	INTERSTELLAR, # Galactic authority
	MATERIAL,     # Physical space
	DEEP_LEY,     # Subsurface arcane
}

enum Phase {
	DORMANT,   # Phase 1 - early game, background presence
	ACTIVE,    # Phase 2 - mid game, direct interaction
	ENFORCING, # Phase 3 - late game, hard consequences
}

enum Alignment {
	COSMIC_CONSTANT,  # Dragons, Gravitons
	BALANCE_LAW,      # Elohim, Ethereal Keepers, Federation
	RESISTANCE,       # Nordics, Pleadians, Martians, etc.
	ANTAGONIST,       # Anunnaki, Reptilians
	NEUTRAL,          # Draco
	CIVILIAN,         # Earth factions
	ARCANE,           # Veiled Conclave, Continuity Initiative
}

# ============================================================================
# FACTION DEFINITIONS (Canonical Set)
# ============================================================================

const FACTION_DEFS := {
	FactionID.DRAGONS: {
		"name": "Dragons",
		"layer": Layer.DRAGONWAYNE,
		"alignment": Alignment.COSMIC_CONSTANT,
		"domain": ["Stellar Leys", "Dragon Nebula", "Dragonwayne Nodes"],
		"visibility": "mythic",
		"role": "Cosmic pressure system / Late-game escalators",
		"interaction_modes": {
			Phase.DORMANT: ["observe_mythic"],
			Phase.ACTIVE: ["dialogue", "trial", "quest_assign", "judge"],
			Phase.ENFORCING: ["cosmic_enforce", "physics_override"],
		},
		"constraints": ["non_recruitable", "non_commandable", "non_ownable"],
	},
	
	FactionID.GRAVITONS: {
		"name": "Gravitons",
		"layer": Layer.DRAGONWAYNE,
		"alignment": Alignment.COSMIC_CONSTANT,
		"domain": ["Gravity Wells", "Mass Nodes", "Void Boundaries"],
		"visibility": "abstract",
		"role": "Physics enforcement / Hard limits on reality abuse",
		"interaction_modes": {
			Phase.DORMANT: ["pressure_warning", "instability_signal"],
			Phase.ACTIVE: ["physics_constraint", "soft_override"],
			Phase.ENFORCING: ["hard_override", "void_rift_shutdown", "god_tech_nullify"],
		},
		"constraints": ["non_negotiable", "deterministic", "overrides_all_when_active"],
	},
	
	FactionID.ETHEREAL_KEEPERS: {
		"name": "Ethereal Keepers",
		"layer": Layer.ETHEREAL,
		"alignment": Alignment.BALANCE_LAW,
		"domain": ["Soul Flow", "Memory Continuity", "Ethereal Realm"],
		"visibility": "invisible",
		"role": "Soul integrity / Timeline failsafe",
		"interaction_modes": {
			Phase.DORMANT: ["observe_only"],
			Phase.ACTIVE: ["ethereal_guide", "akashic_access"], # Only in Ethereal Realm
			Phase.ENFORCING: ["extinction_prevent", "consciousness_preserve"],
		},
		"constraints": ["material_layer_observe_only", "ethereal_layer_questgiver"],
	},
	
	FactionID.ELOHIM: {
		"name": "Elohim",
		"layer": Layer.ETHEREAL,
		"alignment": Alignment.BALANCE_LAW,
		"domain": ["The Cradle", "Universal Seals", "Ethereal Interface"],
		"visibility": "rare_manifestation",
		"role": "Cosmic wardens / Arbiter class",
		"interaction_modes": {
			Phase.DORMANT: ["observe_seal"],
			Phase.ACTIVE: ["arbiter", "cosmic_law_enforcement"],
			Phase.ENFORCING: ["primordial_guard", "void_destabilization_counter"],
		},
		"constraints": ["overrides_federation", "rare_manifestation_only"],
	},
	
	FactionID.DRACO: {
		"name": "Draco",
		"layer": Layer.VOID,
		"alignment": Alignment.NEUTRAL,
		"domain": ["Void Rifts", "The Cradle (contested)", "Dimensional Gates"],
		"visibility": "hidden",
		"role": "Dimensional exploiters / High-reward antagonists",
		"interaction_modes": {
			Phase.DORMANT: ["rift_monitor"],
			Phase.ACTIVE: ["void_exploit", "tech_rival", "rift_control"],
			Phase.ENFORCING: ["rift_destabilize", "graviton_trigger"],
		},
		"constraints": ["triggers_graviton_response", "rivals_arcturians_elohim"],
	},
	
	FactionID.GALACTIC_FEDERATION: {
		"name": "Galactic Federation",
		"layer": Layer.INTERSTELLAR,
		"alignment": Alignment.BALANCE_LAW,
		"domain": ["Treaty Space", "Neutral Zones", "Galactic Council"],
		"visibility": "restricted",
		"role": "Constraint engine / Prevents early total war",
		"interaction_modes": {
			Phase.DORMANT: ["treaty_monitor"],
			Phase.ACTIVE: ["volatile_alignment_bar", "sanction_threat", "exemption_grant"],
			Phase.ENFORCING: ["isolate_faction", "erase_violator"],
		},
		"constraints": ["high_authority_low_intervention", "volatile_rapid_alignment"],
		"alignment_volatility": 0.8, # Easily swayed
	},
	
	FactionID.PLEADIANS: {
		"name": "Pleadians",
		"layer": Layer.MATERIAL,
		"alignment": Alignment.RESISTANCE,
		"domain": ["Europa", "Underwater Sanctuaries"],
		"visibility": "visible",
		"role": "Spiritual support / Morale system",
		"interaction_modes": {
			Phase.DORMANT: ["spiritual_influence"],
			Phase.ACTIVE: ["morale_boost", "healing_field", "awakening_catalyst"],
			Phase.ENFORCING: ["resistance_anchor"],
		},
		"alliances": ["Nordics", "Martians", "Sirians", "Andromedans"],
	},
	
	FactionID.NORDICS: {
		"name": "Nordics",
		"layer": Layer.MATERIAL,
		"alignment": Alignment.RESISTANCE,
		"domain": ["Enceladus", "Icy Ocean Hub"],
		"visibility": "visible",
		"role": "Command & Coordination / Strategic AI",
		"interaction_modes": {
			Phase.DORMANT: ["strategic_planning"],
			Phase.ACTIVE: ["command_coordination", "alliance_unification", "tactical_research"],
			Phase.ENFORCING: ["resistance_leadership"],
		},
		"alliances": ["Pleadians", "Martians", "Orions", "Sirians"],
	},
	
	FactionID.MARTIANS: {
		"name": "Martians",
		"layer": Layer.MATERIAL,
		"alignment": Alignment.RESISTANCE,
		"domain": ["Mars", "Phobos", "Deimos"],
		"visibility": "visible",
		"role": "Ground warfare / Combat strength",
		"interaction_modes": {
			Phase.DORMANT: ["defensive_patrol"],
			Phase.ACTIVE: ["ground_combat", "resistance_nodes", "tactical_strike"],
			Phase.ENFORCING: ["last_stand_defense"],
		},
		"alliances": ["Nordics", "Orions", "Pleadians"],
		"rivalries": ["Reptilians"],
	},
	
	FactionID.ORIONS: {
		"name": "Orions",
		"layer": Layer.MATERIAL,
		"alignment": Alignment.RESISTANCE,
		"domain": ["The Moon", "Lunar Archives"],
		"visibility": "visible",
		"role": "Knowledge guardians / Archive access",
		"interaction_modes": {
			Phase.DORMANT: ["archive_protection"],
			Phase.ACTIVE: ["celestial_knowledge", "lunar_defense", "ancient_tech_access"],
			Phase.ENFORCING: ["knowledge_preservation"],
		},
		"alliances": ["Martians", "Nordics"],
	},
	
	FactionID.SIRIANS: {
		"name": "Sirians",
		"layer": Layer.MATERIAL,
		"alignment": Alignment.RESISTANCE,
		"domain": ["Umbra Planes", "Asteroid Field (trade routes)", "Earth (embedded)"],
		"visibility": "visible",
		"role": "Logistics & Diplomacy / Trade routes",
		"interaction_modes": {
			Phase.DORMANT: ["trade_coordination"],
			Phase.ACTIVE: ["diplomatic_mediation", "logistics_optimization", "alliance_stabilization"],
			Phase.ENFORCING: ["supply_lines_critical"],
		},
		"alliances": ["Pleadians", "Andromedans", "Nordics"],
	},
	
	FactionID.ANDROMEDANS: {
		"name": "Andromedans",
		"layer": Layer.MATERIAL,
		"alignment": Alignment.RESISTANCE,
		"domain": ["Ceres", "Europa", "Bio-Zones"],
		"visibility": "visible",
		"role": "Genetic preservation / Human resilience modifiers",
		"interaction_modes": {
			Phase.DORMANT: ["genetic_monitoring"],
			Phase.ACTIVE: ["genetic_engineering", "anunnaki_tampering_counter", "human_enhancement"],
			Phase.ENFORCING: ["genetic_continuity"],
		},
		"alliances": ["Pleadians", "Sirians"],
	},
	
	FactionID.REPTILIANS: {
		"name": "Reptilians",
		"layer": Layer.MATERIAL,
		"alignment": Alignment.ANTAGONIST,
		"domain": ["Earth", "Mars (contested)"],
		"visibility": "visible",
		"role": "Enforcers / Occupation mechanics",
		"interaction_modes": {
			Phase.DORMANT: ["infiltration"],
			Phase.ACTIVE: ["occupation", "suppression", "anunnaki_enforcement"],
			Phase.ENFORCING: ["total_control_attempt"],
		},
		"alliances": ["Anunnaki"],
		"rivalries": ["Martians", "Orions", "All Resistance"],
	},
	
	FactionID.ANUNNAKI: {
		"name": "Anunnaki",
		"layer": Layer.MATERIAL,
		"alignment": Alignment.ANTAGONIST,
		"domain": ["Nibiru (origin)", "Earth (remote control)"],
		"visibility": "hidden_command",
		"role": "Strategic dominion / High-level antagonists",
		"interaction_modes": {
			Phase.DORMANT: ["observation"],
			Phase.ACTIVE: ["remote_control", "genetic_manipulation", "resource_exploitation"],
			Phase.ENFORCING: ["direct_invasion_threat"],
		},
		"alliances": ["Reptilians"],
		"constraints": ["indirect_control_only", "no_early_physical_occupation"],
	},
	
	FactionID.EARTH_CONCORDAT: {
		"name": "Earth Concordat",
		"layer": Layer.MATERIAL,
		"alignment": Alignment.CIVILIAN,
		"domain": ["Earth Surface", "Public Authority"],
		"visibility": "visible",
		"role": "Population control / Inertia system",
		"interaction_modes": {
			Phase.DORMANT: ["status_quo"],
			Phase.ACTIVE: ["compliance_enforcement", "public_authority"],
			Phase.ENFORCING: ["breakdown"],
		},
	},
	
	FactionID.BLACK_VEIL_DIRECTORATE: {
		"name": "Black Veil Directorate",
		"layer": Layer.MATERIAL,
		"alignment": Alignment.CIVILIAN,
		"domain": ["Earth Subsurface", "Hidden Facilities"],
		"visibility": "hidden",
		"role": "Containment / Fog-of-war mechanics",
		"interaction_modes": {
			Phase.DORMANT: ["information_suppression"],
			Phase.ACTIVE: ["containment_protocol", "truth_suppression", "asset_control"],
			Phase.ENFORCING: ["disclosure_prevention"],
		},
	},
	
	FactionID.AWAKENING_NETWORK: {
		"name": "Awakening Network",
		"layer": Layer.MATERIAL,
		"alignment": Alignment.CIVILIAN,
		"domain": ["Earth Surface", "Digital Networks"],
		"visibility": "visible",
		"role": "Civilian resistance / Viral spread",
		"interaction_modes": {
			Phase.DORMANT: ["awareness_seeding"],
			Phase.ACTIVE: ["information_spread", "morale_boost", "grassroots_resistance"],
			Phase.ENFORCING: ["mass_awakening"],
		},
	},
	
	FactionID.VEILED_CONCLAVE: {
		"name": "Veiled Conclave",
		"layer": Layer.DEEP_LEY,
		"alignment": Alignment.ARCANE,
		"domain": ["Deep Earth", "Ley Networks"],
		"visibility": "hidden",
		"role": "Arcane stability / Reality anchors",
		"interaction_modes": {
			Phase.DORMANT: ["ley_maintenance"],
			Phase.ACTIVE: ["reality_anchor", "breach_sealing", "ley_manipulation"],
			Phase.ENFORCING: ["reality_collapse_prevention"],
		},
	},
	
	FactionID.CONTINUITY_INITIATIVE: {
		"name": "Continuity Initiative",
		"layer": Layer.DEEP_LEY,
		"alignment": Alignment.ARCANE,
		"domain": ["Earth Subsurface", "Bunker Networks"],
		"visibility": "hidden",
		"role": "Survival planning / Timeline insurance",
		"interaction_modes": {
			Phase.DORMANT: ["contingency_planning"],
			Phase.ACTIVE: ["timeline_branching", "survival_protocol", "continuity_backup"],
			Phase.ENFORCING: ["extinction_insurance"],
		},
	},
}

# ============================================================================
# SNAPSHOT STRUCTURE
# ============================================================================

# Snapshot format:
# {
#   "factions": {
#     FactionID: {
#       "influence": float,          # -1.0 to 1.0
#       "phase": Phase,              # Current phase state
#       "active_domains": [str],     # Currently controlled domains
#       "alignment_mods": {faction_id: float}, # Relationship modifiers
#       "mode_flags": [str],         # Active interaction modes
#     }
#   },
#   "global_phase": Phase,           # Overall game phase
#   "federation_alignment": float,   # -1.0 to 1.0 (volatile)
#   "graviton_pressure": float,      # 0.0 to 1.0 (enforcement threshold)
#   "layer_visibility": {Layer: bool}, # Which layers are accessible
# }

# ============================================================================
# KERNEL FUNCTIONS (Pure, Deterministic, Immutable)
# ============================================================================

static func mr_create_snapshot() -> Dictionary:
	"""Pure: Generate initial faction snapshot"""
	var snapshot := {
		"factions": {},
		"global_phase": Phase.DORMANT,
		"federation_alignment": 0.0,
		"graviton_pressure": 0.0,
		"layer_visibility": {
			Layer.MATERIAL: true,
			Layer.DEEP_LEY: false,
			Layer.INTERSTELLAR: false,
			Layer.VOID: false,
			Layer.ETHEREAL: false,
			Layer.DRAGONWAYNE: false,
		},
	}
	
	# Initialize all factions
	for faction_id in FactionID.values():
		var def = FACTION_DEFS.get(faction_id, {})
		snapshot["factions"][faction_id] = {
			"influence": 0.0,
			"phase": Phase.DORMANT,
			"active_domains": def.get("domain", []).duplicate(),
			"alignment_mods": {},
			"mode_flags": def.get("interaction_modes", {}).get(Phase.DORMANT, []).duplicate(),
		}
	
	return snapshot

static func mr_get_faction_state(snapshot_in: Dictionary, faction_id: int) -> Dictionary:
	"""Pure: Retrieve faction state"""
	return snapshot_in.get("factions", {}).get(faction_id, {})

static func mr_set_faction_influence(snapshot_in: Dictionary, faction_id: int, influence_delta: float) -> Dictionary:
	"""Pure: Modify faction influence, return new snapshot"""
	var snapshot_out := _deep_copy(snapshot_in)
	
	var faction = snapshot_out["factions"].get(faction_id, {})
	if faction.is_empty():
		return snapshot_out # Invalid faction, no change
	
	faction["influence"] = clampf(faction.get("influence", 0.0) + influence_delta, -1.0, 1.0)
	
	return snapshot_out

static func mr_check_phase_visibility(snapshot_in: Dictionary, faction_id: int, check_phase: int) -> bool:
	"""Pure: Check if faction is visible/interactable at given phase"""
	var faction = snapshot_in.get("factions", {}).get(faction_id, {})
	var faction_phase = faction.get("phase", Phase.DORMANT)
	
	# Faction must be at or beyond check_phase to be visible
	return faction_phase >= check_phase

static func mr_get_interaction_modes(snapshot_in: Dictionary, faction_id: int) -> Array:
	"""Pure: Get current valid interaction modes for faction"""
	var faction = snapshot_in.get("factions", {}).get(faction_id, {})
	return faction.get("mode_flags", [])

static func mr_escalate_phase(snapshot_in: Dictionary, target_phase: int) -> Dictionary:
	"""Pure: Escalate global phase and update faction phases accordingly"""
	var snapshot_out := _deep_copy(snapshot_in)
	
	snapshot_out["global_phase"] = target_phase
	
	# Update each faction's phase and mode flags
	for faction_id in snapshot_out["factions"].keys():
		var faction = snapshot_out["factions"][faction_id]
		var def = FACTION_DEFS.get(faction_id, {})
		
		# Update phase
		faction["phase"] = target_phase
		
		# Update mode flags based on new phase
		var modes = def.get("interaction_modes", {}).get(target_phase, [])
		faction["mode_flags"] = modes.duplicate()
	
	return snapshot_out

static func mr_modify_federation_alignment(snapshot_in: Dictionary, delta: float) -> Dictionary:
	"""Pure: Modify Federation alignment (volatile, rapid movement)"""
	var snapshot_out := _deep_copy(snapshot_in)
	
	# Federation has high volatility - small actions cause big swings
	var volatility = FACTION_DEFS[FactionID.GALACTIC_FEDERATION].get("alignment_volatility", 0.5)
	var amplified_delta = delta * volatility
	
	snapshot_out["federation_alignment"] = clampf(
		snapshot_out.get("federation_alignment", 0.0) + amplified_delta,
		-1.0, 1.0
	)
	
	return snapshot_out

static func mr_increase_graviton_pressure(snapshot_in: Dictionary, delta: float) -> Dictionary:
	"""Pure: Increase graviton pressure (physics abuse accumulator)"""
	var snapshot_out := _deep_copy(snapshot_in)
	
	snapshot_out["graviton_pressure"] = clampf(
		snapshot_out.get("graviton_pressure", 0.0) + delta,
		0.0, 1.0
	)
	
	# If pressure exceeds threshold and in ENFORCING phase, Gravitons activate
	if snapshot_out["graviton_pressure"] >= 0.8 and snapshot_out["global_phase"] == Phase.ENFORCING:
		# Update Graviton faction to enforcing mode
		var graviton_faction = snapshot_out["factions"][FactionID.GRAVITONS]
		graviton_faction["mode_flags"] = FACTION_DEFS[FactionID.GRAVITONS]["interaction_modes"][Phase.ENFORCING].duplicate()
	
	return snapshot_out

static func mr_check_layer_accessible(snapshot_in: Dictionary, layer: int) -> bool:
	"""Pure: Check if a layer is currently accessible"""
	return snapshot_out.get("layer_visibility", {}).get(layer, false)

static func mr_unlock_layer(snapshot_in: Dictionary, layer: int) -> Dictionary:
	"""Pure: Make a layer accessible (requires traversal trigger)"""
	var snapshot_out := _deep_copy(snapshot_in)
	snapshot_out["layer_visibility"][layer] = true
	return snapshot_out

static func mr_get_faction_relationships(snapshot_in: Dictionary, faction_id: int) -> Dictionary:
	"""Pure: Get alliances and rivalries for a faction"""
	var def = FACTION_DEFS.get(faction_id, {})
	return {
		"alliances": def.get("alliances", []),
		"rivalries": def.get("rivalries", []),
	}

static func mr_check_constraint_violated(snapshot_in: Dictionary, faction_id: int, action: String) -> bool:
	"""Pure: Check if an action violates faction constraints"""
	var def = FACTION_DEFS.get(faction_id, {})
	var constraints = def.get("constraints", [])
	
	# Check common constraint violations
	if "non_recruitable" in constraints and action == "recruit":
		return true
	if "non_commandable" in constraints and action == "command":
		return true
	if "material_layer_observe_only" in constraints and action == "quest_assign":
		var current_layer = _infer_current_layer(snapshot_in)
		if current_layer == Layer.MATERIAL:
			return true
	
	return false

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

static func _deep_copy(data: Dictionary) -> Dictionary:
	"""Deep copy dictionary for immutability"""
	return data.duplicate(true)

static func _infer_current_layer(snapshot_in: Dictionary) -> int:
	"""Infer current layer from layer_visibility (highest unlocked layer)"""
	var visibility = snapshot_in.get("layer_visibility", {})
	
	# Check in descending order of layer hierarchy
	for layer in [Layer.DRAGONWAYNE, Layer.ETHEREAL, Layer.VOID, Layer.INTERSTELLAR, Layer.MATERIAL, Layer.DEEP_LEY]:
		if visibility.get(layer, false):
			return layer
	
	return Layer.MATERIAL # Default

# ============================================================================
# INVARIANTS (For Validation)
# ============================================================================

static func validate_snapshot(snapshot_in: Dictionary) -> bool:
	"""Validate snapshot structure and invariants"""
	
	# Required keys
	if not snapshot_in.has("factions"):
		return false
	if not snapshot_in.has("global_phase"):
		return false
	
	# All factions present
	for faction_id in FactionID.values():
		if not snapshot_in["factions"].has(faction_id):
			return false
	
	# Influence bounds
	for faction_state in snapshot_in["factions"].values():
		var influence = faction_state.get("influence", 0.0)
		if influence < -1.0 or influence > 1.0:
			return false
	
	# Federation alignment bounds
	var fed_alignment = snapshot_in.get("federation_alignment", 0.0)
	if fed_alignment < -1.0 or fed_alignment > 1.0:
		return false
	
	# Graviton pressure bounds
	var grav_pressure = snapshot_in.get("graviton_pressure", 0.0)
	if grav_pressure < 0.0 or grav_pressure > 1.0:
		return false
	
	return true
