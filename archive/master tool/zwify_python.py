#!/usr/bin/env python3
"""
zwify_python.py - Python implementation of ZWify Ultra paste-anything parser
Converts scenario descriptions to ZW format.
"""

import re
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ZWifyParser:
    """Parse mixed-format scenario descriptions into ZW format"""
    
    def __init__(self):
        self.patterns = {
            "chapter": re.compile(r'SCENARIO_CHAPTER\s*:\s*"?([^"\n]+)"?', re.IGNORECASE),
            "phase": re.compile(r'SCENARIO_PHASE\s*:\s*"?([^"\n]+)"?', re.IGNORECASE),
            "overview": re.compile(r'OVERVIEW\s*:\s*"?([\s\S]+?)(?:\n[A-Z_]{3,}|\Z)', re.IGNORECASE),
            "teaser": re.compile(r'CONTINUATION_TEASER\s*:\s*"?([^"\n]+)"?', re.IGNORECASE),
        }
    
    def extract_section(self, content: str, section_name: str) -> str:
        """Extract a section using regex"""
        pattern = re.compile(
            rf'{section_name}\s*:\s*"?([\s\S]+?)(?:\n[A-Z_]{3,}|\Z)', 
            re.IGNORECASE
        )
        match = pattern.search(content)
        return match.group(1).strip() if match else ""
    
    def extract_list_items(self, section_content: str) -> List[str]:
        """Extract bullet list items from a section"""
        items = []
        lines = section_content.split('\n')
        
        for line in lines:
            line = line.strip()
            # Match bullet points starting with -, *, or •
            if re.match(r'^[-*•]\s+', line):
                # Remove bullet and clean
                item = re.sub(r'^[-*•]\s+', '', line)
                # Remove quotes if present
                item = re.sub(r'^"|"$', '', item)
                if item:
                    items.append(item)
        
        return items
    
    def parse_timeline(self, content: str) -> List[Dict]:
        """Parse timeline events"""
        timeline = []
        timeline_section = self.extract_section(content, "TIMELINE_OF_EVENTS")
        
        if not timeline_section:
            return timeline
        
        # Split by bullet points
        events_raw = re.split(r'\n[-*•]\s+', timeline_section.strip())
        
        for event_raw in events_raw:
            if not event_raw.strip():
                continue
            
            event = {
                "date": self._extract_field(event_raw, "DATE"),
                "location": self._extract_field(event_raw, "LOCATION"),
                "event": self._extract_field(event_raw, "EVENT")
            }
            
            if any(event.values()):  # Only add if any field has content
                timeline.append(event)
        
        return timeline
    
    def _extract_field(self, text: str, field_name: str) -> str:
        """Extract field from text using pattern"""
        pattern = re.compile(
            rf'{field_name}\s*:\s*"?([^"\n]+)"?', 
            re.IGNORECASE
        )
        match = pattern.search(text)
        return match.group(1).strip() if match else ""
    
    def parse_factions(self, content: str) -> List[Dict]:
        """Parse factions section"""
        factions = []
        factions_section = self.extract_section(content, "FACTIONS")
        
        if not factions_section:
            return factions
        
        # Split factions by bullet points
        factions_raw = re.split(r'\n[-*•]\s+', factions_section.strip())
        
        for faction_raw in factions_raw:
            if not faction_raw.strip():
                continue
            
            faction = {
                "name": self._extract_field(faction_raw, "NAME"),
                "role": self._extract_field(faction_raw, "ROLE"),
                "technologies": self._extract_list_from_field(faction_raw, "TECHNOLOGIES"),
                "key_individuals": self._extract_list_from_field(faction_raw, "KEY_INDIVIDUALS"),
                "characteristics": self._extract_list_from_field(faction_raw, "CHARACTERISTICS")
            }
            
            if faction["name"]:
                factions.append(faction)
        
        return factions
    
    def _extract_list_from_field(self, text: str, field_name: str) -> List[str]:
        """Extract list items from a specific field"""
        # Find the field content
        field_pattern = re.compile(
            rf'{field_name}\s*:\s*([\s\S]+?)(?:\n[A-Z][A-Z_]*\s*:|$)', 
            re.IGNORECASE
        )
        match = field_pattern.search(text)
        
        if not match:
            return []
        
        field_content = match.group(1)
        return self.extract_list_items(field_content)
    
    def parse_locations(self, content: str) -> List[Dict]:
        """Parse locations section"""
        locations = []
        locations_section = self.extract_section(content, "LOCATIONS")
        
        if not locations_section:
            return locations
        
        # Split locations by bullet points
        locations_raw = re.split(r'\n[-*•]\s+', locations_section.strip())
        
        for location_raw in locations_raw:
            if not location_raw.strip():
                continue
            
            location = {
                "name": self._extract_field(location_raw, "NAME"),
                "type": self._extract_field(location_raw, "TYPE"),
                "description": self._extract_field(location_raw, "DESCRIPTION")
            }
            
            if location["name"]:
                locations.append(location)
        
        return locations
    
    def parse_dialogue(self, content: str) -> List[Dict]:
        """Parse dialogue section"""
        dialogue = []
        dialogue_section = self.extract_section(content, "DIALOGUE")
        
        if not dialogue_section:
            return dialogue
        
        # Split dialogue entries by bullet points
        entries_raw = re.split(r'\n[-*•]\s+', dialogue_section.strip())
        
        for entry_raw in entries_raw:
            if not entry_raw.strip():
                continue
            
            # Try structured format first
            speaker = self._extract_field(entry_raw, "SPEAKER")
            line = self._extract_field(entry_raw, "LINE")
            
            # If not found, try compact "Speaker: text" format
            if not speaker and ':' in entry_raw:
                parts = entry_raw.split(':', 1)
                speaker = parts[0].strip()
                line = parts[1].strip()
                # Remove quotes
                line = re.sub(r'^"|"$', '', line)
            
            if speaker or line:
                dialogue.append({
                    "speaker": speaker or "Unknown",
                    "line": line or "",
                    "emotion": self._extract_field(entry_raw, "EMOTION"),
                    "scene": self._extract_field(entry_raw, "SCENE"),
                    "stage": self._extract_field(entry_raw, "STAGE")
                })
        
        return dialogue
    
    def parse(self, content: str) -> Dict:
        """Parse complete scenario"""
        # Extract basic info
        chapter_match = self.patterns["chapter"].search(content)
        phase_match = self.patterns["phase"].search(content)
        overview_match = self.patterns["overview"].search(content)
        teaser_match = self.patterns["teaser"].search(content)
        
        # Clean overview text
        overview_text = overview_match.group(1) if overview_match else ""
        overview_text = re.sub(r'\n+', ' ', overview_text).strip()
        
        return {
            "chapter": chapter_match.group(1) if chapter_match else "",
            "phase": phase_match.group(1) if phase_match else "",
            "overview": overview_text,
            "teaser": teaser_match.group(1) if teaser_match else "",
            "themes": self.extract_list_items(self.extract_section(content, "KEY_THEMES_EMERGING")),
            "objectives": self.extract_list_items(
                self.extract_section(content, "ANUNNAKI_OBJECTIVES_FOR_PHASE_1") or 
                self.extract_section(content, "OBJECTIVES")
            ),
            "timeline": self.parse_timeline(content),
            "locations": self.parse_locations(content),
            "factions": self.parse_factions(content),
            "relations": self._parse_relations(content),
            "dialogue": self.parse_dialogue(content),
            "metadata": {
                "parsed_at": datetime.now().isoformat(),
                "source_length": len(content)
            }
        }
    
    def _parse_relations(self, content: str) -> List[Dict]:
        """Parse faction relations"""
        relations = []
        relations_section = self.extract_section(content, "FACTION_RELATIONS")
        
        if not relations_section:
            return relations
        
        # Split relations by bullet points
        relations_raw = re.split(r'\n[-*•]\s+', relations_section.strip())
        
        for rel_raw in relations_raw:
            if not rel_raw.strip():
                continue
            
            relation = {
                "a": self._extract_field(rel_raw, "A"),
                "b": self._extract_field(rel_raw, "B"),
                "relation": self._extract_field(rel_raw, "RELATION"),
                "notes": self._extract_field(rel_raw, "NOTES")
            }
            
            if relation["a"] or relation["b"] or relation["relation"]:
                relations.append(relation)
        
        return relations
    
    def generate_zw(self, parsed_data: Dict) -> str:
        """Generate ZW format from parsed data"""
        zw_lines = []
        
        # Helper function for slug generation
        def slug(text):
            if not text:
                return ""
            return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
        
        # ZW-CHAPTER header
        chapter_id = f"ch-{slug(parsed_data['chapter'])}"
        zw_lines.append(
            f'ZW-CHAPTER id="{chapter_id}" '
            f'title="{parsed_data["chapter"]}" '
            f'phase="{parsed_data["phase"]}"'
        )
        
        if parsed_data["overview"]:
            zw_lines.append(f'overview: "{parsed_data["overview"]}"')
        
        if parsed_data["themes"]:
            themes_str = ', '.join(f'"{theme}"' for theme in parsed_data["themes"])
            zw_lines.append(f'themes: [{themes_str}]')
        
        if parsed_data["teaser"]:
            zw_lines.append(f'next_teaser: "{parsed_data["teaser"]}"')
        
        zw_lines.append(f'created: {datetime.now().isoformat()}')
        zw_lines.append("")
        
        # Locations
        loc_ids = {}
        for i, loc in enumerate(parsed_data["locations"]):
            loc_id = f"loc-{slug(loc['name']) or f'loc{i}'}"
            loc_ids[loc["name"]] = loc_id
            
            zw_lines.append(f'ZW-LOCATION id="{loc_id}" name="{loc["name"]}" type="{loc["type"]}"')
            if loc["description"]:
                zw_lines.append(f'description: "{loc["description"]}"')
            zw_lines.append("")
        
        # Timeline events
        for i, event in enumerate(parsed_data["timeline"]):
            loc_ref = ""
            if event["location"] and event["location"] in loc_ids:
                loc_ref = f' location_ref="{loc_ids[event["location"]]}"'
            
            zw_lines.append(f'ZW-TIMELINE-EVENT id="{chapter_id}-t{i}" date="{event["date"]}"{loc_ref}')
            if event["event"]:
                zw_lines.append(f'summary: "{event["event"]}"')
            zw_lines.append("")
        
        # Factions and related entities
        fac_ids = {}
        for i, faction in enumerate(parsed_data["factions"]):
            fac_id = f"fac-{slug(faction['name']) or f'fac{i}'}"
            fac_ids[faction["name"]] = fac_id
            
            zw_lines.append(f'ZW-FACTION id="{fac_id}" name="{faction["name"]}" role="{faction["role"]}"')
            
            if faction["characteristics"]:
                char_str = ',\n  '.join(f'"{c}"' for c in faction["characteristics"])
                zw_lines.append(f'characteristics: [\n  {char_str}\n]')
            
            zw_lines.append("")
            
            # Key individuals
            for individual in faction["key_individuals"]:
                # Parse individual string (could be "Name: Role" or just "Name")
                name = individual
                role = ""
                if ":" in individual:
                    name, role = individual.split(":", 1)
                    name = name.strip()
                    role = role.strip()
                
                person_id = f"char-{slug(name)}"
                
                # Determine ZW type based on role
                if any(title in role.lower() for title in ["queen", "king", "supreme", "commander"]):
                    zw_lines.append(f'ZW-LEADER ref="{fac_id}" id="{person_id}" name="{name}" notes="{role}"')
                elif any(title in role.lower() for title in ["overseer", "captain", "chief", "lead"]):
                    zw_lines.append(f'ZW-COMMAND ref="{fac_id}" id="{person_id}" name="{name}" notes="{role}"')
                else:
                    zw_lines.append(f'ZW-PROFILE type="character" ref="{fac_id}" id="{person_id}" name="{name}" role="{role}"')
            
            # Technologies
            for tech in faction["technologies"]:
                tech_id = f"tech-{slug(tech)}"
                zw_lines.append(f'ZW-TECH id="{tech_id}" owner="{fac_id}" name="{tech}"')
        
        zw_lines.append("")
        
        # Relations
        for i, rel in enumerate(parsed_data["relations"]):
            a_id = fac_ids.get(rel["a"], f"fac-{slug(rel['a'])}")
            b_id = fac_ids.get(rel["b"], f"fac-{slug(rel['b'])}")
            
            zw_lines.append(
                f'ZW-FACTION-REL id="rel-{i}" '
                f'a="{a_id}" b="{b_id}" '
                f'relation="{rel["relation"]}" '
                f'notes="{rel["notes"]}"'
            )
        
        if parsed_data["relations"]:
            zw_lines.append("")
        
        # Dialogue
        for i, dlg in enumerate(parsed_data["dialogue"]):
            # Build attributes
            attrs = []
            if dlg["emotion"]:
                attrs.append(f'emotion="{dlg["emotion"]}"')
            if dlg["scene"]:
                attrs.append(f'scene="{dlg["scene"]}"')
            if dlg["stage"]:
                attrs.append(f'stage="{dlg["stage"]}"')
            
            attrs_str = " " + " ".join(attrs) if attrs else ""
            
            zw_lines.append(f'ZW-DIALOGUE id="{chapter_id}-dlg-{i}" speaker="{dlg["speaker"]}"{attrs_str}')
            zw_lines.append(f'line: "{dlg["line"]}"')
        
        return "\n".join(zw_lines)


def main():
    parser = argparse.ArgumentParser(
        description="ZWify Ultra - Convert scenario descriptions to ZW format"
    )
    parser.add_argument("input", help="Input file with scenario description")
    parser.add_argument("--output", "-o", help="Output ZW file (default: based on input name)")
    parser.add_argument("--format", choices=["zw", "json"], default="zw", 
                       help="Output format (default: zw)")
    
    args = parser.parse_args()
    
    # Read input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        return 1
    
    content = input_path.read_text(encoding="utf-8")
    
    # Parse
    parser = ZWifyParser()
    parsed = parser.parse(content)
    
    # Generate output
    if args.format == "json":
        output = json.dumps(parsed, indent=2, ensure_ascii=False)
        ext = "json"
    else:
        output = parser.generate_zw(parsed)
        ext = "zw"
    
    # Write output
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_suffix(f".{ext}")
    
    output_path.write_text(output, encoding="utf-8")
    
    # Print summary
    print(f"✅ Parsed: {input_path.name}")
    print(f"  • Chapter: {parsed['chapter']}")
    print(f"  • Factions: {len(parsed['factions'])}")
    print(f"  • Locations: {len(parsed['locations'])}")
    print(f"  • Timeline events: {len(parsed['timeline'])}")
    print(f"  • Dialogue lines: {len(parsed['dialogue'])}")
    print(f"📝 Output: {output_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
