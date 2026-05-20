#!/usr/bin/env python3
"""
pass2_zw_integrated.py - Enhanced inference with ZW scenario support
Adds capability to process ZW scenario files and integrate with narrative analysis.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional
from pass2_enhanced import *  # Import existing functionality


class ZWScenarioProcessor:
    """Process ZW scenario files and extract structured data"""
    
    ZW_PATTERNS = {
        "zw_chapter": re.compile(r'ZW-CHAPTER id="([^"]+)" title="([^"]+)" phase="([^"]+)"'),
        "zw_location": re.compile(r'ZW-LOCATION id="([^"]+)" name="([^"]+)" type="([^"]+)"'),
        "zw_faction": re.compile(r'ZW-FACTION id="([^"]+)" name="([^"]+)" role="([^"]+)"'),
        "zw_dialogue": re.compile(r'ZW-DIALOGUE id="([^"]+)" speaker="([^"]+)"'),
        "zw_tech": re.compile(r'ZW-TECH id="([^"]+)" owner="([^"]+)" name="([^"]+)"'),
    }
    
    def __init__(self):
        self.scenario_data = {
            "chapters": [],
            "locations": [],
            "factions": [],
            "characters": [],
            "technologies": [],
            "dialogues": [],
            "relations": []
        }
    
    def parse_zw_file(self, path: Path) -> Dict:
        """Parse ZW scenario file"""
        content = path.read_text(encoding="utf-8")
        lines = content.split('\n')
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse ZW-CHAPTER
            if line.startswith("ZW-CHAPTER"):
                m = self.ZW_PATTERNS["zw_chapter"].search(line)
                if m:
                    self.scenario_data["chapters"].append({
                        "id": m.group(1),
                        "title": m.group(2),
                        "phase": m.group(3)
                    })
            
            # Parse ZW-LOCATION
            elif line.startswith("ZW-LOCATION"):
                m = self.ZW_PATTERNS["zw_location"].search(line)
                if m:
                    self.scenario_data["locations"].append({
                        "id": m.group(1),
                        "name": m.group(2),
                        "type": m.group(3)
                    })
            
            # Parse ZW-FACTION
            elif line.startswith("ZW-FACTION"):
                m = self.ZW_PATTERNS["zw_faction"].search(line)
                if m:
                    self.scenario_data["factions"].append({
                        "id": m.group(1),
                        "name": m.group(2),
                        "role": m.group(3)
                    })
            
            # Parse ZW-DIALOGUE
            elif line.startswith("ZW-DIALOGUE"):
                m = self.ZW_PATTERNS["zw_dialogue"].search(line)
                if m:
                    # Extract emotion if present
                    emotion = None
                    if 'emotion="' in line:
                        emotion_match = re.search(r'emotion="([^"]+)"', line)
                        emotion = emotion_match.group(1) if emotion_match else None
                    
                    self.scenario_data["dialogues"].append({
                        "id": m.group(1),
                        "speaker": m.group(2),
                        "emotion": emotion
                    })
            
            # Parse ZW-TECH
            elif line.startswith("ZW-TECH"):
                m = self.ZW_PATTERNS["zw_tech"].search(line)
                if m:
                    self.scenario_data["technologies"].append({
                        "id": m.group(1),
                        "owner": m.group(2),
                        "name": m.group(3)
                    })
            
            # Parse other ZW types
            elif line.startswith("ZW-LEADER"):
                # Extract leader info
                pass
            elif line.startswith("ZW-FACTION-REL"):
                # Extract faction relations
                pass
        
        return self.scenario_data
    
    def enrich_characters(self, segments: List[Segment]) -> Dict[str, Character]:
        """Enrich character analysis with ZW scenario data"""
        characters = extract_characters(segments)
        
        # Add ZW faction data to characters
        for faction in self.scenario_data["factions"]:
            faction_name = faction["name"]
            if faction_name not in characters:
                characters[faction_name] = Character(
                    name=faction_name,
                    traits={"faction_leader", "strategic"}
                )
            else:
                characters[faction_name].traits.add("faction_leader")
                characters[faction_name].traits.add("strategic")
        
        return characters
    
    def get_scenario_context(self) -> Dict:
        """Get scenario context for enhanced inference"""
        return {
            "era": self.scenario_data["chapters"][0]["phase"] if self.scenario_data["chapters"] else "Unknown",
            "faction_relations": [],
            "technologies": self.scenario_data["technologies"],
            "locations": self.scenario_data["locations"]
        }


def infer_speakers_with_scenario(segments: List[Segment], 
                                characters: Dict[str, Character],
                                scenario_processor: ZWScenarioProcessor) -> List[Tuple[int, str, float]]:
    """Enhanced speaker inference using ZW scenario data"""
    atoms = []
    
    for seg in segments:
        if seg.type == "dialogue" and seg.speaker and seg.speaker != "unknown":
            atoms.append((seg.text_line_no, seg.speaker, 0.95))
        
        elif seg.type == "dialogue" and seg.speaker == "unknown":
            # Use ZW dialogue data to infer speakers
            for zw_dialogue in scenario_processor.scenario_data["dialogues"]:
                if zw_dialogue["speaker"].lower() in seg.text.lower():
                    atoms.append((seg.text_line_no, zw_dialogue["speaker"], 0.85))
                    break
    
    return atoms


def main_enhanced():
    """Enhanced main function with ZW scenario support"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Pass 2 with ZW scenario support")
    parser.add_argument("pass1_output", help="Pass 1 output file")
    parser.add_argument("--zw-scenario", help="ZW scenario file for context enrichment")
    parser.add_argument("--output", help="Custom output file name")
    
    args = parser.parse_args()
    
    # Load segments
    segments = load_segments(args.pass1_output)
    
    # Initialize scenario processor
    scenario_processor = ZWScenarioProcessor()
    scenario_context = {}
    
    # Process ZW scenario if provided
    if args.zw_scenario:
        zw_path = Path(args.zw_scenario)
        if zw_path.exists():
            scenario_data = scenario_processor.parse_zw_file(zw_path)
            scenario_context = scenario_processor.get_scenario_context()
            print(f"[ZW] Loaded scenario: {len(scenario_data['factions'])} factions, "
                  f"{len(scenario_data['dialogues'])} dialogues")
    
    # Extract characters with ZW enrichment
    characters = scenario_processor.enrich_characters(segments) if args.zw_scenario else extract_characters(segments)
    
    # Run enhanced inference
    speakers = infer_speakers_with_scenario(segments, characters, scenario_processor) if args.zw_scenario else infer_speakers_enhanced(segments, characters)
    emotions = infer_emotions_enhanced(segments, characters)
    actions = infer_actions_enhanced(segments)
    thoughts = infer_thoughts_enhanced(segments, characters)
    relationships = infer_relationships(segments, characters)
    
    # Determine output file
    base = Path(args.pass1_output).stem
    if base.startswith("out_pass1_"):
        base = base[len("out_pass1_"):]
    
    outfile = args.output or f"out_pass2_{base}.metta"
    
    # Write output with scenario metadata
    with open(outfile, "w", encoding="utf-8") as f:
        f.write("; PASS2 ENHANCED WITH ZW SCENARIO SUPPORT\n")
        
        if args.zw_scenario:
            f.write(f"; ZW Scenario: {Path(args.zw_scenario).name}\n")
            for chapter in scenario_processor.scenario_data["chapters"]:
                f.write(f"; Chapter: {chapter['title']} ({chapter['phase']})\n")
        
        f.write("\n")
        
        # Write all inference atoms (same format as original)
        # [Existing write_metta code here]
    
    print(f"[PASS2 ENHANCED] Output → {outfile}")
    print(f"[ZW] Context: {len(scenario_processor.scenario_data.get('factions', []))} factions")


if __name__ == "__main__":
    main_enhanced()
