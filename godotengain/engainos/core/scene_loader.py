"""
scene_loader.py - Load game scene JSON and send to Godot

Bridges narrative pipeline output to runtime visualization.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from spatial_reasoner import apply_spatial_reasoning
from spatial_skin_system import Entity3D, Transform3D, ColorRGB, build_scene_render_plans
from mettaext.scene_identity import to_canonical_scene_id

class SceneLoader:
    """Load narrative-generated scenes into Godot runtime"""
    
    def __init__(self, scenes_dir: Path = None):
        if scenes_dir is None:
            candidates = [
                Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/mettaext/game_scenes"),
                Path.home() / "Downloads/EngAIn/mettaext/game_scenes",
            ]
            for candidate in candidates:
                if candidate.exists():
                    self.scenes_dir = candidate
                    break
            else:
                self.scenes_dir = candidates[0]
        else:
            self.scenes_dir = Path(scenes_dir)
    
    def load_scene(self, scene_id: str) -> Dict[str, Any]:
        """
        Load a scene by ID.

        Accepts both canonical IDs (scene.002_molten_descent) and legacy
        file stems (002_molten_descent). Tries three candidate stems in order
        so no file renames are needed.
        """
        canonical = to_canonical_scene_id(scene_id)
        stem_without_prefix = canonical.removeprefix("scene.")

        candidates = [scene_id, canonical, stem_without_prefix]
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_candidates = [c for c in candidates if not (c in seen or seen.add(c))]

        for stem in unique_candidates:
            path = self.scenes_dir / f"{stem}.json"
            if path.exists():
                with path.open('r') as f:
                    return json.load(f)

        attempted = [str(self.scenes_dir / f"{s}.json") for s in unique_candidates]
        raise FileNotFoundError(
            f"Scene '{scene_id}' not found. Attempted:\n" + "\n".join(f"  {p}" for p in attempted)
        )
    
    def list_available_scenes(self) -> List[str]:
        """List all available scene IDs"""
        return [
            p.stem for p in self.scenes_dir.glob("*.json")
        ]
    
    def extract_spawn_data(self, scene: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract entity spawn data for Godot
        
        Args:
            scene: Loaded scene data
        
        Returns: List of spawn commands for Godot
        """
        spawn_commands = []
        
        for entity in scene.get('entities', []):
            spawn_commands.append({
                'type': 'spawn_entity',
                'id': entity['id'],
                'name': entity['name'],
                'position': [
                    entity['position']['x'],
                    entity['position']['y'],
                    entity['position']['z']
                ],
                'health': entity['health'],
                'max_health': entity['max_health'],
                'entity_type': entity['type']
            })
        
        return spawn_commands
    
    def extract_dialogue_events(self, scene: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract dialogue events in order
        
        Args:
            scene: Loaded scene data
        
        Returns: List of dialogue events
        """
        return [
            event for event in scene.get('events', [])
            if event['type'] in ['dialogue', 'thought']
        ]
    
    def get_scene_metadata(self, scene: Dict[str, Any]) -> Dict[str, str]:
        """Extract scene metadata"""
        return {
            'scene_id': scene.get('scene_id', 'unknown'),
            'description': scene.get('description', ''),
            'location': scene.get('metadata', {}).get('where', 'Unknown')
        }


def spawn_to_entities(formatted: dict) -> list[Entity3D]:
    entities = []

    for cmd in formatted.get("spawn_commands", []):
        pos = cmd.get("position", [0, 0, 0])

        entity = Entity3D(
            zw_concept=cmd.get("entity_type", "character"),
            ap_profile="default_npc",
            kernel_bindings={},
            placeholder_mesh="capsule",
            transform=Transform3D.from_data(position=pos),

            entity_id=cmd.get("id"),
            entity_type=cmd.get("entity_type", "character"),

            # TEMP visual mapping
            skin_3d_id="engain_dragon",
            color=ColorRGB(0.6, 0.8, 1.0)
        )

        entities.append(entity)

    return entities


def render_plan_to_spawn(plan) -> dict:
    return {
        "type": "spawn_entity",
        "id": plan.logic_tags.get("entity_id"),
        "entity_type": plan.entity_type,

        # position
        "position": [
            plan.transform.x,
            plan.transform.y,
            plan.transform.z,
        ],

        # RENDER CONTRACT
        "render_mode": "scene_instance" if plan.skin_3d_id else "planar_sprite",
        "scene_ref": "res://assets/EngAInDragon.tscn" if plan.skin_3d_id else "",

        "size_world": [1.0, 1.8],
        "collision_profile": "character_medium",
        "interaction_radius": 1.5,
        "shadow_mode": "projected",
    }


# ================================================================
# GODOT BRIDGE INTEGRATION
# ================================================================

def format_for_godot(scene: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format scene data for Godot consumption
    
    Returns dict ready to send via HTTP to Godot
    """
    loader = SceneLoader()
    
    formatted = {
        'metadata': loader.get_scene_metadata(scene),
        'spawn_commands': loader.extract_spawn_data(scene),
        'events': loader.extract_dialogue_events(scene),
        'initial_state': scene.get('initial_state', {})
    }
    
    # 1. Apply AI spatial reasoning
    formatted = apply_spatial_reasoning(formatted)

    # 2. 🔥 NEW PIPELINE: build spatial skin entities and render plans
    entities = spawn_to_entities(formatted)
    plans = build_scene_render_plans(entities)

    formatted["spawn_commands"] = [
        render_plan_to_spawn(p) for p in plans
    ]
    
    return formatted


# ================================================================
# CLI INTERFACE
# ================================================================

if __name__ == '__main__':
    import sys
    
    loader = SceneLoader()
    
    if len(sys.argv) < 2:
        print("Available scenes:")
        for scene_id in loader.list_available_scenes():
            print(f"  - {scene_id}")
        sys.exit(0)
    
    scene_id = sys.argv[1]
    
    print(f"Loading scene: {scene_id}")
    scene = loader.load_scene(scene_id)
    
    print(f"\nMetadata:")
    metadata = loader.get_scene_metadata(scene)
    for key, value in metadata.items():
        print(f"  {key}: {value}")
    
    print(f"\nEntities: {len(scene.get('entities', []))}")
    for entity in scene.get('entities', [])[:5]:  # First 5
        print(f"  - {entity['name']} at ({entity['position']['x']}, {entity['position']['y']}, {entity['position']['z']})")
    
    print(f"\nEvents: {len(scene.get('events', []))}")
    for event in scene.get('events', [])[:3]:  # First 3
        print(f"  - {event['type']}: {event['actor']} - {event['data'].get('text', '')[:50]}...")
