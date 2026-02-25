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

    def extract_entities(self, obj: Dict[str, Any]) -> List[str]:
        """Extract all named entities from either scene format or canonical zonj."""
        ents = obj.get("@entities")
        if isinstance(ents, list) and ents:
            return sorted({str(x).lower() for x in ents if str(x).strip()})

        segments = obj.get("segments", [])
        if not isinstance(segments, list):
            segments = []

        entities = set()

        for seg in segments:
            if not isinstance(seg, dict):
                continue

            sp = seg.get("speaker")
            if isinstance(sp, str) and sp:
                entities.add(sp.lower())

            inferred = seg.get("inferred", {})
            if not isinstance(inferred, dict):
                inferred = {}

            for item in inferred.get("speaker_inferred", []):
                v = item.get("value") if isinstance(item, dict) else None
                if v:
                    entities.add(str(v).lower())

            for item in inferred.get("actor", []):
                v = item.get("value") if isinstance(item, dict) else None
                if v:
                    entities.add(str(v).lower())

            for item in inferred.get("emotion", []):
                s = item.get("subject") if isinstance(item, dict) else None
                if s:
                    entities.add(str(s).lower())

            for item in inferred.get("thought", []):
                s = item.get("subject") if isinstance(item, dict) else None
                if s and str(s).lower() != "unknown":
                    entities.add(str(s).lower())

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
            if seg.get("type") == "blank":
                continue

            line_no = seg.get("line")
            seg_type = seg.get("type", "narration")
            text = seg.get("text", "")

            lines.append(f"  - line: {line_no}")
            lines.append(f"    type: {seg_type}")

            if "speaker" in seg:
                lines.append(f"    speaker: {seg['speaker']}")

            if text:
                text_escaped = str(text).replace('"', '\\"')
                lines.append(f'    text: "{text_escaped}"')

        return "\n".join(lines)

    def build_inferred_section(self, scene: Dict[str, Any]) -> str:
        """Build =inferred section"""
        lines = ["=inferred:"]

        emotions = []
        actions = []
        thoughts = []
        actors = []

        for seg in scene.get("segments", []):
            if seg.get("type") == "blank":
                continue

            line_no = seg.get("line")
            inferred = seg.get("inferred", {})

            for emo in inferred.get("emotion", []):
                emotions.append({
                    "line": line_no,
                    "subject": emo.get("subject"),
                    "emotion": emo.get("label"),
                    "confidence": float(emo.get("confidence", 0.0)),
                })

            for act in inferred.get("action", []):
                actions.append({
                    "line": line_no,
                    "action": act.get("label"),
                    "confidence": float(act.get("confidence", 0.0)),
                })

            for th in inferred.get("thought", []):
                thoughts.append({
                    "line": line_no,
                    "subject": th.get("subject"),
                    "confidence": float(th.get("confidence", 0.0)),
                })

            for ac in inferred.get("actor", []):
                actors.append({
                    "line": line_no,
                    "actor": ac.get("value"),
                    "confidence": float(ac.get("confidence", 0.0)),
                })

        if emotions:
            lines.append("  emotions:")
            for emo in emotions:
                lines.append(
                    f"    - {{line: {emo['line']}, subject: {emo['subject']}, "
                    f"emotion: {emo['emotion']}, confidence: {emo['confidence']:.2f}}}"
                )

        if actions:
            lines.append("  actions:")
            for act in actions:
                lines.append(
                    f"    - {{line: {act['line']}, action: {act['action']}, "
                    f"confidence: {act['confidence']:.2f}}}"
                )

        if thoughts:
            lines.append("  thoughts:")
            for th in thoughts:
                lines.append(
                    f"    - {{line: {th['line']}, subject: {th['subject']}, "
                    f"confidence: {th['confidence']:.2f}}}"
                )

        if actors:
            lines.append("  actors:")
            for ac in actors:
                lines.append(
                    f"    - {{line: {ac['line']}, actor: {ac['actor']}, "
                    f"confidence: {ac['confidence']:.2f}}}"
                )

        return "\n".join(lines)

    def build_narrative_section(self, scene: Dict[str, Any]) -> str:
        """Build =narrative summary section"""
        lines = ["=narrative:"]
        segment_types: Dict[str, int] = {}

        for seg in scene.get("segments", []):
            t = seg.get("type", "narration")
            segment_types[t] = segment_types.get(t, 0) + 1

        total_segments = sum(segment_types.values())
        lines.append(f'  "{scene.get("id", "unknown")} - {total_segments} segments"')

        for seg_type, count in sorted(segment_types.items()):
            lines.append(f"  {seg_type}: {count}")

        return "\n".join(lines)

    def convert_to_zon(self, zonj_path: Path, metadata: ZONMetadata) -> str:
        with zonj_path.open("r", encoding="utf-8") as f:
            scene = json.load(f)

        sections = [
            self.build_zon_header(scene, metadata),
            "",
            self.build_segments_section(scene),
            "",
            self.build_inferred_section(scene),
            "",
            self.build_narrative_section(scene),
        ]
        return "\n".join(sections)

    def convert_to_zonj(self, zonj_path: Path, metadata: ZONMetadata) -> Dict[str, Any]:
        with zonj_path.open("r", encoding="utf-8") as f:
            scene = json.load(f)

        scene_id = scene.get("id", "unknown_scene")
        entities = self.extract_entities(scene)

        when_val = (
            f"{metadata.start_time}~{metadata.end_time}"
            if (metadata.start_time and metadata.end_time)
            else f"{metadata.era}.scene_{scene_id}"
        )

        zon_canonical: Dict[str, Any] = {
            "@id": f"scene.{scene_id}",
            "@when": when_val,
            "@where": f"Realm/Physical/{metadata.location}",
            "@scope": metadata.scope,
            "@entities": entities,
            "=segments": [],
            "=inferred": {
                "emotions": [],
                "actions": [],
                "thoughts": [],
                "actors": [],
            },
            "=metadata": {
                "source_format": "zonj_narrative",
                "source_files": scene.get("source_files", {}),
            },
        }

        # Segments
        for seg in scene.get("segments", []):
            if seg.get("type") == "blank":
                continue

            entry = {"line": seg.get("line"), "type": seg.get("type")}
            if "speaker" in seg:
                entry["speaker"] = seg.get("speaker")
            if "text" in seg:
                entry["text"] = seg.get("text")
            zon_canonical["=segments"].append(entry)

        # Inferred
        for seg in scene.get("segments", []):
            inferred = seg.get("inferred", {})
            line_no = seg.get("line")

            for emo in inferred.get("emotion", []):
                zon_canonical["=inferred"]["emotions"].append({
                    "line": line_no,
                    "subject": emo.get("subject"),
                    "emotion": emo.get("label"),
                    "confidence": emo.get("confidence"),
                })

            for act in inferred.get("action", []):
                zon_canonical["=inferred"]["actions"].append({
                    "line": line_no,
                    "action": act.get("label"),
                    "confidence": act.get("confidence"),
                })

            for th in inferred.get("thought", []):
                zon_canonical["=inferred"]["thoughts"].append({
                    "line": line_no,
                    "subject": th.get("subject"),
                    "confidence": th.get("confidence"),
                })

            for ac in inferred.get("actor", []):
                zon_canonical["=inferred"]["actors"].append({
                    "line": line_no,
                    "actor": ac.get("value"),
                    "confidence": ac.get("confidence"),
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

    metadata = ZONMetadata(
        era=args.era,
        location=args.location,
        scope=args.scope,
        start_time=args.start,
        end_time=args.end
    )

    bridge = ZONBridge()

    zon_text = bridge.convert_to_zon(input_path, metadata)
    zon_json = bridge.convert_to_zonj(input_path, metadata)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    base_name = input_path.stem.replace("zonj_", "")
    zon_path = output_dir / f"{base_name}.zon"
    zonj_path = output_dir / f"{base_name}.zonj.json"

    with zon_path.open("w", encoding="utf-8") as f:
        f.write(zon_text)

    with zonj_path.open("w", encoding="utf-8") as f:
        json.dump(zon_json, f, ensure_ascii=False, indent=2)

    print(f"[PASS4] Converted to ZON format:")
    print(f"  Human-readable: {zon_path}")
    print(f"  Canonical JSON: {zonj_path}")
    print(f"  Era: {metadata.era}")
    print(f"  Location: {metadata.location}")

    entities = zon_json.get("@entities") or bridge.extract_entities(zon_json)
    if entities:
        print(f"  Entities: {', '.join(entities)}")


if __name__ == "__main__":
    main()
