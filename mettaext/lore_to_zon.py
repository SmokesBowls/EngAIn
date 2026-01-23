#!/usr/bin/env python3
"""
lore_to_zon.py - Convert ZW lore files to ZON memory fabric

Handles various ZW lore block types:
- ZW_EVENT_SEED
- ZW_CHARACTER_LAW
- ZW_SPECIES_ORIGIN
- ZW_WORLD_RULE
- ZW_CANON

Converts to ZON with proper temporal/spatial anchoring.

Usage:
    python3 lore_to_zon.py zw_event_seeds.zw
    python3 lore_to_zon.py zw_*.zw --batch
"""

import sys
import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ZWBlock:
    """Parsed ZW block"""
    block_type: str
    fields: Dict[str, Any]
    raw_lines: List[str]


class LoreToZON:
    """Convert ZW lore blocks to ZON format"""
    
    # Map ZW block types to ZON scopes
    SCOPE_MAP = {
        "ZW_EVENT_SEED": "event",
        "ZW_CHARACTER_LAW": "canon",
        "ZW_SPECIES_ORIGIN": "lore",
        "ZW_WORLD_RULE": "canon",
        "ZW_CANON": "canon",
    }
    
    # Map era tags to temporal anchors
    ERA_MAP = {
        "first_age": "FirstAge",
        "pre_matter": "PreMatter",
        "post_shattering": "PostShattering",
    }
    
    def __init__(self):
        self.blocks: List[ZWBlock] = []
    
    def parse_zw_file(self, path: Path) -> List[ZWBlock]:
        """Parse ZW lore file into blocks"""
        blocks = []
        current_block = None
        current_fields = {}
        current_lines = []
        
        with path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            
            # Block start: ZW_BLOCK_TYPE:
            if line and not line.startswith(" ") and ":" in line:
                # Save previous block if exists
                if current_block:
                    blocks.append(ZWBlock(
                        block_type=current_block,
                        fields=current_fields,
                        raw_lines=current_lines
                    ))
                
                # Start new block
                current_block = line.rstrip(":")
                current_fields = {}
                current_lines = [line]
                i += 1
                continue
            
            # Field line (indented)
            if line.startswith("  ") and current_block:
                current_lines.append(line)
                
                # Parse field
                field_line = line.strip()
                if ":" in field_line:
                    key, value = field_line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Handle list values [...]
                    if value.startswith("[") and value.endswith("]"):
                        # Simple list parsing
                        items = value[1:-1].split(",")
                        value = [item.strip().strip('"') for item in items if item.strip()]
                    # Remove quotes from strings
                    elif value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    
                    current_fields[key] = value
            
            # Blank line - might end block
            elif not line.strip():
                if current_block:
                    blocks.append(ZWBlock(
                        block_type=current_block,
                        fields=current_fields,
                        raw_lines=current_lines
                    ))
                    current_block = None
                    current_fields = {}
                    current_lines = []
            
            i += 1
        
        # Save final block
        if current_block:
            blocks.append(ZWBlock(
                block_type=current_block,
                fields=current_fields,
                raw_lines=current_lines
            ))
        
        return blocks
    
    def extract_temporal_anchor(self, block: ZWBlock) -> str:
        """Extract @when temporal anchor from block"""
        # Check for explicit era field
        if "era" in block.fields:
            era = block.fields["era"]
            # Convert to standard format
            era_key = era.lower().replace(" ", "_")
            era_canonical = self.ERA_MAP.get(era_key, era)
            
            # Add event id if available
            if "id" in block.fields:
                event_id = block.fields["id"]
                return f"{era_canonical}.{event_id}"
            
            return era_canonical
        
        # Check tags for era hints
        if "tags" in block.fields:
            tags = block.fields["tags"]
            if isinstance(tags, list):
                for tag in tags:
                    tag_lower = tag.lower()
                    if tag_lower in self.ERA_MAP:
                        return self.ERA_MAP[tag_lower]
        
        return "Unknown.era"
    
    def extract_spatial_anchor(self, block: ZWBlock) -> str:
        """Extract @where spatial anchor from block"""
        # Check for domain field (world rules)
        if "domain" in block.fields:
            domain = block.fields["domain"]
            return f"Realm/{domain.capitalize()}"
        
        # Check for scope field (canon)
        if "scope" in block.fields:
            scope = block.fields["scope"]
            return f"Realm/{scope.capitalize()}"
        
        # Default to cosmic/universal
        return "Realm/Cosmic"
    
    def extract_entities(self, block: ZWBlock) -> List[str]:
        """Extract entity references from block"""
        entities = []
        
        # Character laws
        if "character" in block.fields:
            entities.append(block.fields["character"].lower())
        
        # Species origins
        if "species" in block.fields:
            entities.append(block.fields["species"].lower().replace("-", "_"))
        
        if "derived_from" in block.fields:
            entities.append(block.fields["derived_from"].lower())
        
        return entities
    
    def convert_block_to_zon(self, block: ZWBlock) -> str:
        """Convert a single ZW block to ZON format"""
        lines = []
        
        # @id
        block_id = block.fields.get("id", "unknown")
        lines.append(f"@id: {block.block_type.lower()}.{block_id}")
        
        # @when
        when = self.extract_temporal_anchor(block)
        lines.append(f"@when: {when}")
        
        # @where
        where = self.extract_spatial_anchor(block)
        lines.append(f"@where: {where}")
        
        # @scope
        scope = self.SCOPE_MAP.get(block.block_type, "lore")
        lines.append(f"@scope: {scope}")
        
        # @entities
        entities = self.extract_entities(block)
        if entities:
            entities_str = ", ".join(entities)
            lines.append(f"@entities: [{entities_str}]")
        
        lines.append("")
        
        # =attributes section (all non-id fields)
        lines.append("=attributes:")
        for key, value in block.fields.items():
            if key == "id":
                continue
            
            if isinstance(value, list):
                lines.append(f"  {key}:")
                for item in value:
                    lines.append(f"    - {item}")
            elif isinstance(value, str) and ("\n" in value or len(value) > 80):
                # Multi-line string
                lines.append(f'  {key}: |')
                for subline in value.split("\n"):
                    lines.append(f"    {subline}")
            else:
                lines.append(f"  {key}: {value}")
        
        lines.append("")
        
        # =tags section
        if "tags" in block.fields:
            tags = block.fields["tags"]
            if isinstance(tags, list):
                lines.append("=tags:")
                for tag in tags:
                    lines.append(f"  - {tag}")
                lines.append("")
        
        return "\n".join(lines)
    
    def convert_block_to_zonj(self, block: ZWBlock) -> Dict[str, Any]:
        """Convert a single ZW block to canonical ZON JSON"""
        block_id = block.fields.get("id", "unknown")
        
        zon_json = {
            "@id": f"{block.block_type.lower()}.{block_id}",
            "@when": self.extract_temporal_anchor(block),
            "@where": self.extract_spatial_anchor(block),
            "@scope": self.SCOPE_MAP.get(block.block_type, "lore"),
            "=attributes": {},
            "=metadata": {
                "source_format": "zw_lore",
                "block_type": block.block_type
            }
        }
        
        # Add entities if present
        entities = self.extract_entities(block)
        if entities:
            zon_json["@entities"] = entities
        
        # Add all fields as attributes
        for key, value in block.fields.items():
            if key != "id":
                zon_json["=attributes"][key] = value
        
        return zon_json
    
    def convert_file(self, input_path: Path, output_dir: Path):
        """Convert entire ZW lore file to ZON"""
        blocks = self.parse_zw_file(input_path)
        
        if not blocks:
            print(f"WARNING: No blocks found in {input_path}")
            return
        
        # Determine output filenames
        base_name = input_path.stem
        zon_path = output_dir / f"{base_name}.zon"
        zonj_path = output_dir / f"{base_name}.zonj.json"
        
        # Convert to .zon (human-readable)
        zon_lines = []
        zon_lines.append(f"# Converted from: {input_path.name}")
        zon_lines.append(f"# Blocks: {len(blocks)}")
        zon_lines.append("")
        
        for block in blocks:
            zon_lines.append(self.convert_block_to_zon(block))
            zon_lines.append("")
        
        with zon_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(zon_lines))
        
        # Convert to .zonj (canonical JSON)
        zonj_data = {
            "source_file": input_path.name,
            "block_count": len(blocks),
            "blocks": [self.convert_block_to_zonj(block) for block in blocks]
        }
        
        with zonj_path.open("w", encoding="utf-8") as f:
            json.dump(zonj_data, f, ensure_ascii=False, indent=2)
        
        print(f"[LORE→ZON] Converted {input_path.name}:")
        print(f"  {len(blocks)} blocks → {zon_path}")
        print(f"  Canonical JSON → {zonj_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert ZW lore files to ZON memory fabric format"
    )
    parser.add_argument("input", nargs="+", help="Input ZW lore file(s)")
    parser.add_argument("--batch", action="store_true", 
                       help="Process multiple files")
    parser.add_argument("--output-dir", default="./zon_output",
                       help="Output directory (default: ./zon_output)")
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Process files
    converter = LoreToZON()
    
    for input_file in args.input:
        input_path = Path(input_file)
        
        if not input_path.exists():
            print(f"ERROR: File not found: {input_path}")
            continue
        
        try:
            converter.convert_file(input_path, output_dir)
        except Exception as e:
            print(f"ERROR converting {input_path}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
