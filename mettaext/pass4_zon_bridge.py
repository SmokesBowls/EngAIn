#!/usr/bin/env python3
"""
pass4_zon_bridge.py - Convert ZONJ narrative scenes to ZON memory fabric

Takes Pass3 ZONJ output and converts to ZON4D format with:
- Temporal anchoring (@when)
- Spatial anchoring (@where)
- Scope and entity tracking
- Proper semantic sections

Usage:
    python3 pass4_zon_bridge.py zonj_scene.json
    python3 pass4_zon_bridge.py zonj_scene.json --era FirstAge --location Beach
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ZONMetadata:
    """Metadata for ZON temporal/spatial anchoring"""
    era: str = "Unknown"
    location: str = "Unknown"
    scope: str = "narrative"
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class ZONBridge:
    """Convert ZONJ scenes to ZON memory fabric format"""
    
    def __init__(self):
        self.known_entities = set()
    
    def extract_entities(self, scene: Dict[str, Any]) -> List[str]:
        """Extract all named entities from scene"""
        entities = set()
        
        for seg in scene.get("segments", []):
            # Explicit speakers
            if "speaker" in seg:
                entities.add(seg["speaker"].lower())
            
            # Inferred data
            inferred = seg.get("inferred", {})
            
            # Speaker inferences
            for item in inferred.get("speaker_inferred", []):
                entities.add(item["value"].lower())
            
            # Actor inferences
            for item in inferred.get("actor", []):
                entities.add(item["value"].lower())
            
            # Emotion subjects
            for item in inferred.get("emotion", []):
                entities.add(item["subject"].lower())
            
            # Thought subjects
            for item in inferred.get("thought", []):
                subj = item["subject"].lower()
                if subj != "unknown":
                    entities.add(subj)
        
        return sorted(entities)
    
    def build_zon_header(self, scene: Dict[str, Any], metadata: ZONMetadata) -> str:
        """Build ZON header section"""
        scene_id = scene.get("id", "unknown_scene")
        entities = self.extract_entities(scene)
        
        lines = []
        lines.append(f"@id: scene.{scene_id}")
        
        # Temporal anchor
        if metadata.start_time and metadata.end_time:
            lines.append(f"@when: {metadata.start_time}~{metadata.end_time}")
        else:
            lines.append(f"@when: {metadata.era}.scene_{scene_id}")
        
        # Spatial anchor
        lines.append(f"@where: Realm/Physical/{metadata.location}")
        
        # Scope
        lines.append(f"@scope: {metadata.scope}")
        
        # Entities
        if entities:
            entities_str = ", ".join(entities)
            lines.append(f"@entities: [{entities_str}]")
        
        return "\n".join(lines)
    
    def build_segments_section(self, scene: Dict[str, Any]) -> str:
        """Build =segments section"""
        lines = ["=segments:"]
        
        for seg in scene.get("segments", []):
            if seg["type"] == "blank":
                continue
            
            line_no = seg["line"]
            seg_type = seg["type"]
            text = seg.get("text", "")
            
            # Build segment entry
            seg_line = f"  - line: {line_no}"
            lines.append(seg_line)
            lines.append(f"    type: {seg_type}")
            
            if "speaker" in seg:
                lines.append(f"    speaker: {seg['speaker']}")
            
            if text:
                # Escape quotes and format text
                text_escaped = text.replace('"', '\\"')
                lines.append(f'    text: "{text_escaped}"')
        
        return "\n".join(lines)
    
    def build_inferred_section(self, scene: Dict[str, Any]) -> str:
        """Build =inferred section with all semantic atoms"""
        lines = ["=inferred:"]
        
        # Collect all inferences by type
        emotions = []
        actions = []
        thoughts = []
        actors = []
        
        for seg in scene.get("segments", []):
            line_no = seg["line"]
            inferred = seg.get("inferred", {})
            
            # Emotions
            for emo in inferred.get("emotion", []):
                emotions.append({
                    "line": line_no,
                    "subject": emo["subject"],
                    "emotion": emo["label"],
                    "confidence": emo["confidence"]
                })
            
            # Actions
            for act in inferred.get("action", []):
                actions.append({
                    "line": line_no,
                    "action": act["label"],
                    "confidence": act["confidence"]
                })
            
            # Thoughts
            for thought in inferred.get("thought", []):
                thoughts.append({
                    "line": line_no,
                    "subject": thought["subject"],
                    "confidence": thought["confidence"]
                })
            
            # Actors
            for actor in inferred.get("actor", []):
                actors.append({
                    "line": line_no,
                    "actor": actor["value"],
                    "confidence": actor["confidence"]
                })
        
        # Write emotions
        if emotions:
            lines.append("  emotions:")
            for emo in emotions:
                lines.append(f"    - {{line: {emo['line']}, subject: {emo['subject']}, "
                           f"emotion: {emo['emotion']}, confidence: {emo['confidence']:.2f}}}")
        
        # Write actions
        if actions:
            lines.append("  actions:")
            for act in actions:
                lines.append(f"    - {{line: {act['line']}, action: {act['action']}, "
                           f"confidence: {act['confidence']:.2f}}}")
        
        # Write thoughts
        if thoughts:
            lines.append("  thoughts:")
            for thought in thoughts:
                lines.append(f"    - {{line: {thought['line']}, subject: {thought['subject']}, "
                           f"confidence: {thought['confidence']:.2f}}}")
        
        # Write actors
        if actors:
            lines.append("  actors:")
            for actor in actors:
                lines.append(f"    - {{line: {actor['line']}, actor: {actor['actor']}, "
                           f"confidence: {actor['confidence']:.2f}}}")
        
        return "\n".join(lines)
    
    def build_narrative_section(self, scene: Dict[str, Any]) -> str:
        """Build =narrative section for human-readable summary"""
        lines = ["=narrative:"]
        
        # Count segment types
        segment_types = {}
        for seg in scene.get("segments", []):
            seg_type = seg["type"]
            segment_types[seg_type] = segment_types.get(seg_type, 0) + 1
        
        # Build summary
        total_segments = sum(segment_types.values())
        lines.append(f'  "{scene.get("id", "unknown")} - {total_segments} segments"')
        
        # Add type breakdown
        for seg_type, count in sorted(segment_types.items()):
            lines.append(f"  {seg_type}: {count}")
        
        return "\n".join(lines)
    
    def convert_to_zon(self, zonj_path: Path, metadata: ZONMetadata) -> str:
        """Convert ZONJ scene file to ZON format"""
        with zonj_path.open("r", encoding="utf-8") as f:
            scene = json.load(f)
        
        sections = []
        
        # Header
        sections.append(self.build_zon_header(scene, metadata))
        sections.append("")
        
        # Segments
        sections.append(self.build_segments_section(scene))
        sections.append("")
        
        # Inferred data
        sections.append(self.build_inferred_section(scene))
        sections.append("")
        
        # Narrative summary
        sections.append(self.build_narrative_section(scene))
        
        return "\n".join(sections)
    
    def convert_to_zonj(self, zonj_path: Path, metadata: ZONMetadata) -> Dict[str, Any]:
        """Convert ZONJ scene to canonical ZON JSON format"""
        with zonj_path.open("r", encoding="utf-8") as f:
            scene = json.load(f)
        
        scene_id = scene.get("id", "unknown_scene")
        entities = self.extract_entities(scene)
        
        # Build canonical ZON JSON structure
        zon_canonical = {
            "@id": f"scene.{scene_id}",
            "@when": metadata.start_time and metadata.end_time 
                     and f"{metadata.start_time}~{metadata.end_time}" 
                     or f"{metadata.era}.scene_{scene_id}",
            "@where": f"Realm/Physical/{metadata.location}",
            "@scope": metadata.scope,
            "@entities": entities,
            "=segments": [],
            "=inferred": {
                "emotions": [],
                "actions": [],
                "thoughts": [],
                "actors": []
            },
            "=metadata": {
                "source_format": "zonj_narrative",
                "source_files": scene.get("source_files", {})
            }
        }
        
        # Add segments
        for seg in scene.get("segments", []):
            if seg["type"] == "blank":
                continue
            
            seg_entry = {
                "line": seg["line"],
                "type": seg["type"]
            }
            
            if "speaker" in seg:
                seg_entry["speaker"] = seg["speaker"]
            
            if "text" in seg:
                seg_entry["text"] = seg["text"]
            
            zon_canonical["=segments"].append(seg_entry)
        
        # Add inferred data
        for seg in scene.get("segments", []):
            inferred = seg.get("inferred", {})
            line_no = seg["line"]
            
            for emo in inferred.get("emotion", []):
                zon_canonical["=inferred"]["emotions"].append({
                    "line": line_no,
                    "subject": emo["subject"],
                    "emotion": emo["label"],
                    "confidence": emo["confidence"]
                })
            
            for act in inferred.get("action", []):
                zon_canonical["=inferred"]["actions"].append({
                    "line": line_no,
                    "action": act["label"],
                    "confidence": act["confidence"]
                })
            
            for thought in inferred.get("thought", []):
                zon_canonical["=inferred"]["thoughts"].append({
                    "line": line_no,
                    "subject": thought["subject"],
                    "confidence": thought["confidence"]
                })
            
            for actor in inferred.get("actor", []):
                zon_canonical["=inferred"]["actors"].append({
                    "line": line_no,
                    "actor": actor["value"],
                    "confidence": actor["confidence"]
                })
        
        return zon_canonical


def main():
    parser = argparse.ArgumentParser(
        description="Convert ZONJ narrative scenes to ZON memory fabric format"
    )
    parser.add_argument("input", help="Input ZONJ scene file")
    parser.add_argument("--era", default="Unknown", help="Temporal era (e.g. FirstAge)")
    parser.add_argument("--location", default="Unknown", help="Spatial location (e.g. Beach)")
    parser.add_argument("--scope", default="narrative", help="Scope (narrative/canon/log)")
    parser.add_argument("--start", help="Start time (ISO or relative)")
    parser.add_argument("--end", help="End time (ISO or relative)")
    parser.add_argument("--output-dir", default=".", help="Output directory")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)
    
    # Build metadata
    metadata = ZONMetadata(
        era=args.era,
        location=args.location,
        scope=args.scope,
        start_time=args.start,
        end_time=args.end
    )
    
    # Convert
    bridge = ZONBridge()
    
    # Generate .zon (human-readable)
    zon_text = bridge.convert_to_zon(input_path, metadata)
    
    # Generate .zonj (canonical JSON)
    zon_json = bridge.convert_to_zonj(input_path, metadata)
    
    # Determine output paths
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    base_name = input_path.stem.replace("zonj_", "")
    zon_path = output_dir / f"{base_name}.zon"
    zonj_path = output_dir / f"{base_name}.zonj.json"
    
    # Write outputs
    with zon_path.open("w", encoding="utf-8") as f:
        f.write(zon_text)
    
    with zonj_path.open("w", encoding="utf-8") as f:
        json.dump(zon_json, f, ensure_ascii=False, indent=2)
    
    print(f"[PASS4] Converted to ZON format:")
    print(f"  Human-readable: {zon_path}")
    print(f"  Canonical JSON: {zonj_path}")
    print(f"  Era: {metadata.era}")
    print(f"  Location: {metadata.location}")
    
    # Show entity summary
    entities = bridge.extract_entities(zon_json)
    if entities:
        print(f"  Entities: {', '.join(entities)}")


if __name__ == "__main__":
    main()
