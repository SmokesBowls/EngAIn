#!/usr/bin/env python3
"""
pass5_game_bridge.py - ZON Memory Fabric → Game Scene

Takes Pass4 ZON output and generates game-ready scene JSON.

Usage:
    python3 pass5_game_bridge.py out_pass1_03_Fist_contact.zonj.json
    python3 pass5_game_bridge.py narrative_work/zon/*.zonj.json --output game_scenes/
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List


class GameBridge:
    """Convert ZON memory fabric to game scenes"""
    
    def convert_zon_to_game(self, zon_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert ZON to game scene format"""
        
        # Extract scene ID (remove 'scene.' prefix)
        scene_id = zon_data.get('@id', 'unknown_scene')
        if scene_id.startswith('scene.'):
            scene_id = scene_id[6:]
        
        # Get description from first narration segment
        segments = zon_data.get('=segments', [])
        description = self._get_description(segments)
        
        # Extract characters from @entities
        entity_list = zon_data.get('@entities', [])
        characters = self._create_characters(entity_list)
        
        # Extract location from @where
        where = zon_data.get('@where', '')
        locations = self._create_locations(where)
        
        # Extract events from segments
        events = self._extract_events(segments)
        
        # Build initial state
        initial_state = self._build_state(characters, locations)
        
        return {
            'scene_id': scene_id,
            'description': description,
            'entities': characters,
            'locations': locations,
            'events': events,
            'initial_state': initial_state,
            'metadata': {
                'when': zon_data.get('@when', ''),
                'where': zon_data.get('@where', ''),
                'scope': zon_data.get('@scope', 'narrative')
            }
        }
    
    def _get_description(self, segments: List[Dict]) -> str:
        """Get scene description from first narration"""
        for seg in segments[:10]:
            if seg.get('type') == 'narration':
                return seg.get('text', '')[:200]
        return ''
    
    def _create_characters(self, entity_list: List[str]) -> List[Dict]:
        """Create character entries"""
        characters = []
        for i, entity_id in enumerate(entity_list):
            characters.append({
                'id': entity_id,
                'name': entity_id.capitalize(),
                'health': 100.0,
                'max_health': 100.0,
                'position': {'x': i * 5, 'y': 0, 'z': 0},
                'type': 'character'
            })
        return characters
    
    def _create_locations(self, where: str) -> List[Dict]:
        """Create location from @where path"""
        if not where:
            return []
        
        parts = where.split('/')
        location_name = parts[-1] if parts else 'Unknown'
        
        return [{
            'id': location_name.lower(),
            'name': location_name,
            'description': f"Location: {where}",
            'path': where,
            'type': 'area'
        }]
    
    def _extract_events(self, segments: List[Dict]) -> List[Dict]:
        """Extract events from segments"""
        events = []
        
        for i, seg in enumerate(segments):
            seg_type = seg.get('type', '')
            
            if seg_type == 'dialogue':
                events.append({
                    'type': 'dialogue',
                    'timestamp': i,
                    'actor': seg.get('speaker', 'unknown'),
                    'action': 'speak',
                    'data': {
                        'text': seg.get('text', ''),
                        'line': seg.get('line', 0)
                    }
                })
            
            elif seg_type == 'thought':
                events.append({
                    'type': 'thought',
                    'timestamp': i,
                    'actor': seg.get('thinker', 'unknown'),
                    'action': 'think',
                    'data': {
                        'text': seg.get('text', ''),
                        'line': seg.get('line', 0)
                    }
                })
        
        return events
    
    def _build_state(self, characters: List[Dict], locations: List[Dict]) -> Dict:
        """Build initial game state"""
        combat_entities = {}
        spatial_entities = {}
        
        for char in characters:
            combat_entities[char['id']] = {
                'health': char['health'],
                'max_health': char['max_health']
            }
            spatial_entities[char['id']] = char['position']
        
        return {
            'combat': {'entities': combat_entities},
            'spatial': {'entities': spatial_entities},
            'locations': locations
        }


def main():
    parser = argparse.ArgumentParser(description='Convert ZON to game scenes')
    parser.add_argument('zon_files', nargs='+', help='ZON files to convert')
    parser.add_argument('--output', default='./game_scenes', help='Output directory')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    bridge = GameBridge()
    
    for zon_file in args.zon_files:
        zon_path = Path(zon_file)
        
        if not zon_path.exists():
            print(f"⚠ File not found: {zon_path}")
            continue
        
        print(f"Converting: {zon_path.name}")
        
        # Load ZON
        with zon_path.open('r') as f:
            zon_data = json.load(f)
        
        # Convert
        game_scene = bridge.convert_zon_to_game(zon_data)
        
        # Save
        output_path = output_dir / f"{game_scene['scene_id']}.json"
        with output_path.open('w') as f:
            json.dump(game_scene, f, indent=2)
        
        print(f"  ✓ {game_scene['scene_id']}.json")
        print(f"    Characters: {len(game_scene['entities'])}")
        print(f"    Events: {len(game_scene['events'])}")
        print(f"    Location: {game_scene['metadata']['where']}")
        print()
    
    print(f"✓ Done! Game scenes in: {output_dir}")


if __name__ == '__main__':
    main()
