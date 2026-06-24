"""
Metta Extractor – Phase 1
Raw markdown / text  →  structured segments

This ONLY does segmentation and light typing.
Downstream builders (ZW/ZON/AP) will consume Segment objects.

Intentionally zero external deps – stdlib only.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Iterable
import re
import uuid


# --------- Data Model --------- #

@dataclass
class Segment:
    """
    Atomic narrative unit.

    type:
      - scene_header
      - narration
      - dialogue
      - action
      - meta
      - blank
    """
    id: str
    scene_id: str
    index: int        # order within scene
    type: str
    text: str
    speaker: Optional[str] = None
    meta: Dict[str, str] = field(default_factory=dict)

    def short(self, max_len: int = 60) -> str:
        t = self.text.replace("\n", " ").strip()
        return t if len(t) <= max_len else t[: max_len - 3] + "..."


@dataclass
class Scene:
    id: str
    title: str
    index: int
    segments: List[Segment] = field(default_factory=list)


# --------- Core Segmenter --------- #

class Segmenter:
    """
    Phase 1 segmenter.

    Heuristics:
      - Scene boundaries:
          * Markdown headings (#, ##, ###)
          * Lines starting with '@scene', '@chapter'
          * Plain 'Scene X', 'Chapter X' patterns
      - Dialogue:
          * 'Name: text'
          * 'Name - text'
          * '"Quoted text"' optionally prefixed by '-' or '–'
      - Meta lines:
          * '@tag value'
          * '[meta] ...'
    """

    SCENE_HEADING_RE = re.compile(
        r'^\s*(?:#{1,6}\s*(?P<h1>.+?)\s*$|@scene\s*(?P<scene_tag>.+)?$|@chapter\s*(?P<chap_tag>.+)?$|(?P<label>(Scene|Chapter)\s+\d+.*))',
        re.IGNORECASE,
    )

    DIALOGUE_RE = re.compile(
        r'^\s*(?:(?P<name>[A-Z][A-Za-z0-9_\- ]{0,40})\s*[:\-]\s*)?(?P<line>"[^"]+"|“[^”]+”|\'[^\']+\')\s*$'
    )

    META_RE = re.compile(r'^\s*@(?P<key>[A-Za-z0-9_\-]+)\s*(?P<value>.*)$')
    ACTION_RE = re.compile(r'^\s*\[(?P<act>[A-Za-z0-9_ ]+)\]\s*$')

    def __init__(self) -> None:
        pass

    # ---- public API ---- #

    def segment_text(self, text: str) -> List[Scene]:
        """
        Main entry point.
        """
        lines = self._normalize(text).splitlines()
        scenes: List[Scene] = []
        current_scene = self._new_scene(index=0, title="(default)")
        scenes.append(current_scene)

        seg_index = 0
        global_meta: Dict[str, str] = {}

        for raw_line in lines:
            line = raw_line.rstrip("\n")

            # Blank
            if not line.strip():
                seg = self._mk_segment(
                    scene=current_scene,
                    seg_index=seg_index,
                    type_="blank",
                    text="",
                )
                current_scene.segments.append(seg)
                seg_index += 1
                continue

            # Scene heading?
            scene_match = self.SCENE_HEADING_RE.match(line)
            if scene_match:
                title = (
                    scene_match.group("h1")
                    or scene_match.group("scene_tag")
                    or scene_match.group("chap_tag")
                    or scene_match.group("label")
                    or "(untitled scene)"
                ).strip()

                current_scene = self._new_scene(index=len(scenes), title=title)
                scenes.append(current_scene)
                seg_index = 0

                seg = self._mk_segment(
                    scene=current_scene,
                    seg_index=seg_index,
                    type_="scene_header",
                    text=line,
                    meta={"title": title},
                )
                current_scene.segments.append(seg)
                seg_index += 1
                continue

            # Meta / tags?
            meta_match = self.META_RE.match(line)
            if meta_match:
                key = meta_match.group("key")
                val = meta_match.group("value").strip()
                global_meta[key] = val
                seg = self._mk_segment(
                    scene=current_scene,
                    seg_index=seg_index,
                    type_="meta",
                    text=line,
                    meta={"key": key, "value": val},
                )
                current_scene.segments.append(seg)
                seg_index += 1
                continue

            # Dialogue?
            dlg_match = self.DIALOGUE_RE.match(line)
            if dlg_match:
                speaker = dlg_match.group("name")
                spoken = dlg_match.group("line").strip()
                spoken = self._strip_quotes(spoken)

                seg = self._mk_segment(
                    scene=current_scene,
                    seg_index=seg_index,
                    type_="dialogue",
                    text=spoken,
                    speaker=speaker,
                    meta={"raw": line},
                )
                current_scene.segments.append(seg)
                seg_index += 1
                continue

            # Action block?
            act_match = self.ACTION_RE.match(line)
            if act_match:
                seg = self._mk_segment(
                    scene=current_scene,
                    seg_index=seg_index,
                    type_="action",
                    text=act_match.group("act").strip(),
                    meta={"raw": line},
                )
                current_scene.segments.append(seg)
                seg_index += 1
                continue

            # Default: narration
            seg = self._mk_segment(
                scene=current_scene,
                seg_index=seg_index,
                type_="narration",
                text=line,
            )
            current_scene.segments.append(seg)
            seg_index += 1

        # propagate global meta to scene-level meta if useful later
        for sc in scenes:
            if not hasattr(sc, "meta"):
                sc.meta = {}
            sc.meta.update(global_meta)

        return scenes

    # ---- helpers ---- #

    def _new_scene(self, index: int, title: str) -> Scene:
        sid = f"scene_{index:03d}_{self._short_uuid()}"
        return Scene(id=sid, title=title, index=index)

    def _mk_segment(
        self,
        scene: Scene,
        seg_index: int,
        type_: str,
        text: str,
        speaker: Optional[str] = None,
        meta: Optional[Dict[str, str]] = None,
    ) -> Segment:
        return Segment(
            id=f"{scene.id}_seg_{seg_index:04d}",
            scene_id=scene.id,
            index=seg_index,
            type=type_,
            text=text,
            speaker=speaker,
            meta=meta or {},
        )

    @staticmethod
    def _normalize(text: str) -> str:
        # Normalize line endings, strip BOM, etc.
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = text.lstrip("\ufeff")
        return text

    @staticmethod
    def _strip_quotes(s: str) -> str:
        s = s.strip()
        if (s.startswith('"') and s.endswith('"')) or (
            s.startswith("“") and s.endswith("”")
        ) or (s.startswith("'") and s.endswith("'")):
            return s[1:-1]
        return s

    @staticmethod
    def _short_uuid() -> str:
        return uuid.uuid4().hex[:8]


# --------- Convenience CLI --------- #

def _print_summary(scenes: Iterable[Scene]) -> None:
    for sc in scenes:
        print(f"\n=== [{sc.index}] {sc.id} :: {sc.title}")
        for seg in sc.segments:
            label = seg.type
            if seg.type == "dialogue" and seg.speaker:
                label = f"dialogue({seg.speaker})"
            print(f"  [{seg.index:03d}] {label}: {seg.short()}")


def main():
    import argparse
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description="Phase 1 Metta Segmenter – raw text → segments"
    )
    parser.add_argument("path", help="path to .md/.txt file ('-' for stdin')")
    args = parser.parse_args()

    if args.path == "-":
        data = sys.stdin.read()
        src = "<stdin>"
    else:
        p = Path(args.path)
        if not p.exists():
            print(f"File not found: {p}", file=sys.stderr)
            sys.exit(1)
        data = p.read_text(encoding="utf-8")
        src = str(p)

    seg = Segmenter()
    scenes = seg.segment_text(data)

    print(f"Source: {src}")
    print(f"Scenes: {len(scenes)}")
    total_segments = sum(len(s.segments) for s in scenes)
    print(f"Segments: {total_segments}")
    _print_summary(scenes)


if __name__ == "__main__":
    main()
