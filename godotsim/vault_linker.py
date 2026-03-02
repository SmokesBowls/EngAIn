#!/usr/bin/env python3
"""
vault_linker.py — EngAIn Vault Linker
======================================
Reads a vault.manifest.json, discovers Obsidian markdown files,
converts them to ZONJ scene dicts, and stores them for sim_runtime
scene loading.

This is an INFRASTRUCTURE module, not a gameplay module.
It belongs alongside sim_runtime.py, NOT inside CommandDispatcher.

Usage (standalone test):
    python3 vault_linker.py /path/to/vault.manifest.json

Usage (imported by sim_runtime):
    from vault_linker import VaultLinker
    linker = VaultLinker()
    result = linker.link(manifest_dict, vault_root="/path/to/vault")
    # result["scenes"] is a dict of scene_id -> zonj dict
"""

import json
import os
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime


class VaultLinker:
    """
    Reads an Obsidian vault via manifest, discovers .md files,
    converts each to a ZONJ-compatible scene dict.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.scenes: Dict[str, dict] = {}
        self.manifest: dict = {}
        self.vault_root: Optional[Path] = None
        self.last_link_time: Optional[str] = None

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def link(self, manifest: Union[dict, str], vault_root: str) -> dict:
        """
        Main entry point. Accepts a manifest dict OR path string.
        """
        # If manifest is a path, load it
        if isinstance(manifest, str):
            import json
            with open(manifest, 'r') as f:
                manifest = json.load(f)
        
        self.manifest = manifest
        self.vault_root = Path(vault_root).expanduser().resolve()

        if not self.vault_root.is_dir():
            return {
                "status": "error",
                "error": f"vault root not found: {self.vault_root}"
            }

        # Resolve source dir from manifest
        source_rel = manifest.get("content", {}).get("source_markdown", {}).get("dir", ".")
        source_dir = self.vault_root / source_rel

        if not source_dir.is_dir():
            return {
                "status": "error",
                "error": f"source_markdown dir not found: {source_dir}"
            }

        # Resolve cache dir from manifest (or use default)
        build_cfg = manifest.get("build", {})
        cache_path = build_cfg.get("output_dir")
        if cache_path:
            self.cache_dir = Path(cache_path).expanduser().resolve()

        # Discover markdown files
        md_files = self._discover_markdown(source_dir)

        if not md_files:
            return {
                "status": "warning",
                "warning": "no .md files found in vault",
                "vault_root": str(self.vault_root),
                "source_dir": str(source_dir)
            }

        # Convert each to ZONJ scene dict
        self.scenes = {}
        errors = []
        for md_path in md_files:
            try:
                scene = self._md_to_zonj(md_path, source_dir)
                if scene:
                    sid = scene.get("@id", scene.get("scene_id", "unknown"))
                    self.scenes[sid] = scene
            except Exception as e:
                errors.append({"file": str(md_path), "error": str(e)})

        # Optionally write cache
        if self.cache_dir:
            self._write_cache()

        self.last_link_time = datetime.utcnow().isoformat() + "Z"

        return {
            "status": "ok",
            "vault_id": manifest.get("vault_id", "unknown"),
            "vault_root": str(self.vault_root),
            "files_found": len(md_files),
            "scenes_extracted": len(self.scenes),
            "scene_ids": sorted(self.scenes.keys()),
            "errors": errors,
            "linked_at": self.last_link_time
        }

    def get_scene(self, scene_id: str) -> Optional[dict]:
        """Retrieve a linked scene by ID."""
        return self.scenes.get(scene_id)

    def get_all_scenes(self) -> Dict[str, dict]:
        """Return all linked scenes."""
        return dict(self.scenes)

    def get_status(self) -> dict:
        """Return current linker status."""
        return {
            "linked": bool(self.scenes),
            "vault_id": self.manifest.get("vault_id"),
            "vault_root": str(self.vault_root) if self.vault_root else None,
            "scene_count": len(self.scenes),
            "linked_at": self.last_link_time
        }

    # ------------------------------------------------------------------
    # MARKDOWN DISCOVERY
    # ------------------------------------------------------------------

    def _discover_markdown(self, source_dir: Path) -> List[Path]:
        """
        Walk the source directory and collect .md files.
        Skips hidden dirs, .obsidian/, .trash/, templates/.
        """
        skip_dirs = {".obsidian", ".trash", ".git", "templates", ".engain"}
        md_files = []

        for root, dirs, files in os.walk(source_dir):
            # Prune skipped directories
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]

            for f in sorted(files):
                if f.endswith(".md") and not f.startswith("."):
                    md_files.append(Path(root) / f)

        return md_files

    # ------------------------------------------------------------------
    # MARKDOWN → ZONJ CONVERSION
    # ------------------------------------------------------------------

    def _md_to_zonj(self, md_path: Path, source_dir: Path) -> Optional[dict]:
        """
        Convert an Obsidian markdown file to a ZONJ-compatible scene dict.

        Extracts:
            @id       — derived from filename
            @where    — derived from folder path
            =segments — paragraphs as narrative beats
            @entities — names detected in text (capitalized words heuristic)
            @tags     — Obsidian #tags and YAML frontmatter tags
        """
        raw = md_path.read_text(encoding="utf-8", errors="ignore")

        # Parse optional YAML frontmatter
        frontmatter, body = self._split_frontmatter(raw)

        # Generate scene ID from filename
        stem = md_path.stem  # e.g., "Chapter 12 - The Nephilim Summoning"
        scene_id = self._stem_to_scene_id(stem)

        # Detect chapter number if present
        chapter_num = self._extract_chapter_num(stem)

        # Extract relative path as location hint
        rel = md_path.relative_to(source_dir)
        where = str(rel.parent) if str(rel.parent) != "." else "vault_root"

        # Split body into segments (paragraphs)
        segments = self._extract_segments(body)

        if not segments:
            return None  # skip empty files

        # Extract entities (simple capitalized-word heuristic)
        entities = self._extract_entities(body)

        # Extract Obsidian tags
        tags = self._extract_tags(body, frontmatter)

        # Build ZONJ dict
        zonj = {
            "@id": scene_id,
            "scene_id": scene_id,
            "@where": where,
            "@source": str(rel),
            "=segments": segments,
            "@entities": entities,
            "@tags": tags,
        }

        if chapter_num is not None:
            zonj["@chapter"] = chapter_num

        # Merge frontmatter fields (title, aliases, etc.)
        if frontmatter:
            for k, v in frontmatter.items():
                if k not in ("tags",):  # tags already handled
                    zonj[f"@fm_{k}"] = v

        return zonj

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def _split_frontmatter(self, raw: str) -> tuple:
        """Split YAML frontmatter from body. Returns (dict|None, body_str)."""
        if not raw.startswith("---"):
            return None, raw

        parts = raw.split("---", 2)
        if len(parts) < 3:
            return None, raw

        fm_text = parts[1].strip()
        body = parts[2]

        # Simple YAML-ish parse (key: value per line)
        fm = {}
        for line in fm_text.split("\n"):
            line = line.strip()
            if ":" in line:
                key, _, val = line.partition(":")
                key = key.strip()
                val = val.strip()
                # Handle list values
                if val.startswith("[") and val.endswith("]"):
                    val = [v.strip().strip('"').strip("'")
                           for v in val[1:-1].split(",")]
                fm[key] = val

        return fm, body

    def _stem_to_scene_id(self, stem: str) -> str:
        """Convert a filename stem to a canonical scene_id."""
        # "Chapter 12 - The Nephilim Summoning" -> "scene.12_the_nephilim_summoning"
        # "My Random Note" -> "scene.my_random_note"
        s = stem.lower().strip()
        s = re.sub(r"chapter\s*(\d+)\s*[-–—:]\s*", r"\1_", s)
        s = re.sub(r"[^a-z0-9_]+", "_", s)
        s = re.sub(r"_+", "_", s).strip("_")
        if not s:
            s = "untitled"
        return f"scene.{s}"

    def _extract_chapter_num(self, stem: str) -> Optional[int]:
        """Extract chapter number from stem if present."""
        m = re.search(r"chapter\s*(\d+)", stem, re.IGNORECASE)
        if m:
            return int(m.group(1))
        m = re.match(r"^(\d+)\s*[-–—_]", stem)
        if m:
            return int(m.group(1))
        return None

    def _extract_segments(self, body: str) -> List[dict]:
        """
        Split body text into paragraph-based segments.
        Each segment is a narrative beat.
        """
        segments = []
        paragraphs = re.split(r"\n\s*\n", body.strip())

        for i, para in enumerate(paragraphs):
            text = para.strip()
            if not text:
                continue
            # Skip pure heading lines (they become segment labels)
            if text.startswith("#") and "\n" not in text:
                continue

            seg = {
                "index": i,
                "text": text,
            }

            # Detect dialogue lines
            if re.search(r'["""].+?["""]', text) or re.match(r"^\w+:\s+", text):
                seg["type"] = "dialogue"
            else:
                seg["type"] = "narration"

            segments.append(seg)

        return segments

    def _extract_entities(self, body: str) -> List[str]:
        """
        Simple entity extraction: find capitalized multi-letter words
        that appear 2+ times. Filter out common English words.
        """
        stop_words = {
            "The", "This", "That", "These", "Those", "They", "Their",
            "There", "Then", "When", "Where", "What", "Which", "While",
            "With", "From", "Into", "Upon", "After", "Before", "About",
            "Above", "Below", "Between", "Through", "During", "Without",
            "Within", "Along", "Among", "Around", "Against", "Behind",
            "Beyond", "Chapter", "Part", "Book", "Note", "Scene",
            "However", "Although", "Because", "Since", "Until",
            "Also", "Still", "Just", "Only", "Even", "Much", "Many",
            "Every", "Each", "Some", "Most", "Other", "Another",
            "First", "Last", "Next", "Both", "Such", "Like",
        }

        words = re.findall(r"\b([A-Z][a-z]{2,})\b", body)
        counts: Dict[str, int] = {}
        for w in words:
            if w not in stop_words:
                counts[w] = counts.get(w, 0) + 1

        # Return words appearing 2+ times, sorted by frequency
        entities = [w for w, c in sorted(counts.items(), key=lambda x: -x[1]) if c >= 2]
        return entities[:30]  # cap at 30

    def _extract_tags(self, body: str, frontmatter: Optional[dict]) -> List[str]:
        """Extract Obsidian #tags from body + frontmatter tags field."""
        tags = set()

        # Obsidian inline tags
        for m in re.finditer(r"#([a-zA-Z0-9_/-]+)", body):
            tag = m.group(1)
            if not tag[0].isdigit():  # skip #123 style headings
                tags.add(tag)

        # Frontmatter tags
        if frontmatter and "tags" in frontmatter:
            fm_tags = frontmatter["tags"]
            if isinstance(fm_tags, list):
                tags.update(fm_tags)
            elif isinstance(fm_tags, str):
                tags.update(t.strip() for t in fm_tags.split(","))

        return sorted(tags)

    def _write_cache(self):
        """Write extracted scenes to cache directory as .zonj.json files."""
        if not self.cache_dir:
            return

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        for sid, scene in self.scenes.items():
            safe_name = sid.replace(".", "_").replace("/", "_")
            out_path = self.cache_dir / f"{safe_name}.zonj.json"
            out_path.write_text(
                json.dumps(scene, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )

        # Write index
        index = {
            "vault_id": self.manifest.get("vault_id"),
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "scene_count": len(self.scenes),
            "scenes": {sid: f"{sid.replace('.','_').replace('/','_')}.zonj.json"
                       for sid in sorted(self.scenes.keys())}
        }
        (self.cache_dir / "_index.json").write_text(
            json.dumps(index, indent=2), encoding="utf-8"
        )


# ==================================================================
# STANDALONE TEST
# ==================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 vault_linker.py /path/to/vault.manifest.json")
        print("       (manifest must live inside or reference the vault root)")
        sys.exit(1)

    manifest_path = Path(sys.argv[1]).expanduser().resolve()
    if not manifest_path.exists():
        print(f"ERROR: manifest not found: {manifest_path}")
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text())

    # Vault root is the directory containing the manifest
    vault_root = manifest_path.parent

    linker = VaultLinker()
    result = linker.link(manifest, str(vault_root))

    print(json.dumps(result, indent=2))

    if result.get("status") == "ok":
        print(f"\n--- First 3 scene previews ---")
        for sid in result["scene_ids"][:3]:
            sc = linker.get_scene(sid)
            segs = sc.get("=segments", [])
            print(f"\n  {sid}: {len(segs)} segments, "
                  f"{len(sc.get('@entities', []))} entities")
            if segs:
                print(f"    first: {segs[0].get('text', '')[:80]}...")
