#!/usr/bin/env python3
"""
engain_ingest.py — Unified Ingest System for EngAIn

Consumes three source formats and routes them through the appropriate pipeline:

  FORMAT A: Obsidian .md files (narrative chapters)
    .md → strip frontmatter → raw text → Pass 1 → Pass 2 → Pass 3 → ZONJ

  FORMAT B: TRIXEL .jsonl score files (art assets)
    .jsonl → parse brush actions → reconstruct image → register asset

  FORMAT C: ChatGPT conversation exports (.txt/.json)
    .txt/.json → extract code blocks + conversation → structured knowledge

Usage:
  # Ingest an entire Obsidian vault
  python3 engain_ingest.py --vault ~/obsidian/burdens_vault --out ./zonj_scenes/

  # Ingest a single chapter
  python3 engain_ingest.py --file chapter_03.md --out ./zonj_scenes/

  # Ingest TRIXEL score files
  python3 engain_ingest.py --trixel .zw/scores/ --out ./assets/

  # Ingest a ChatGPT export
  python3 engain_ingest.py --chatgpt export.txt --out ./knowledge/

  # Ingest everything in a directory (auto-detect formats)
  python3 engain_ingest.py --scan ~/Downloads/EngAIn/ --out ./ingest_output/

  # POST results to live runtime
  python3 engain_ingest.py --vault ~/obsidian/ --out ./zonj/ --runtime http://localhost:5000

Requirements:
  Python 3.10+
  pass1_explicit.py, pass2_core.py, pass3_merge.py in same dir or on PYTHONPATH
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import hashlib
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

def __hook__(chain, event, module=None, file=None, func=None, **kw):
    """Instrumentation hook for the ingest generator."""
    if event == "call":
        if func in ("batch_ingest", "run_narrative_pipeline", "ingest_trixel_file"):
            chain.append({
                "type": "ingest_checkpoint",
                "event": event,
                "func": func,
                "module": module,
                "ts": datetime.now().isoformat()
            })
    elif event == "init":
         chain.append({"type": "module_init", "module": module, "file": file})


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SUPPORTED_NARRATIVE = {".md", ".txt", ".text"}
SUPPORTED_TRIXEL = {".jsonl"}
SUPPORTED_CHATGPT = set()  # detected by content, not extension

YAML_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
CHATGPT_MARKER_RE = re.compile(r"^(You said:|ChatGPT said:|Human:|Assistant:)", re.MULTILINE)
CODE_BLOCK_RE = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class IngestResult:
    source_path: str
    source_format: str  # "obsidian_md", "trixel_jsonl", "chatgpt_export", "raw_text"
    output_path: str
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestManifest:
    timestamp: str
    source_dir: str
    output_dir: str
    results: List[IngestResult] = field(default_factory=list)

    @property
    def summary(self) -> Dict[str, int]:
        total = len(self.results)
        ok = sum(1 for r in self.results if r.success)
        fail = total - ok
        by_format = {}
        for r in self.results:
            by_format[r.source_format] = by_format.get(r.source_format, 0) + 1
        return {"total": total, "success": ok, "failed": fail, "by_format": by_format}


# ---------------------------------------------------------------------------
# FORMAT A: Obsidian Markdown → Narrative Pipeline
# ---------------------------------------------------------------------------

def strip_obsidian_frontmatter(text: str) -> str:
    """Remove YAML frontmatter (---...---) from Obsidian .md files."""
    m = YAML_FRONTMATTER_RE.match(text)
    if m:
        return text[m.end():]
    return text


def extract_obsidian_metadata(text: str) -> Dict[str, str]:
    """Extract YAML frontmatter fields if present."""
    meta = {}
    m = YAML_FRONTMATTER_RE.match(text)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                key, _, val = line.partition(":")
                meta[key.strip()] = val.strip().strip('"').strip("'")
    return meta


def strip_obsidian_links(text: str) -> str:
    """Convert [[wiki links]] to plain text and remove #tags."""
    # [[display|link]] → display
    text = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\1", text)
    # [[link]] → link
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    # Remove inline #tags but keep # headers
    text = re.sub(r"(?<!\n)#(\w+)", r"\1", text)
    return text


def strip_obsidian_callouts(text: str) -> str:
    """Convert Obsidian callouts (> [!note]) to plain text."""
    text = re.sub(r"^>\s*\[!(\w+)\]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    return text


def is_narrative_content(text: str) -> bool:
    """Heuristic: does this .md file contain narrative prose (not just notes)?"""
    lines = text.strip().splitlines()
    if len(lines) < 5:
        return False
    # Check for dialogue markers or substantial prose
    dialogue_count = sum(1 for l in lines if '"' in l or '\u201c' in l)
    word_count = len(text.split())
    # Narrative chapters typically have 500+ words
    return word_count > 300 or dialogue_count > 3


def prepare_obsidian_for_pass1(md_path: Path) -> Tuple[Optional[Path], Dict[str, Any]]:
    """
    Read an Obsidian .md file, strip all Obsidian-specific syntax,
    and write a clean .txt ready for pass1_explicit.py.

    Returns (clean_txt_path, metadata) or (None, metadata) if not narrative.
    """
    raw = md_path.read_text(encoding="utf-8", errors="replace")
    meta = extract_obsidian_metadata(raw)

    # Strip Obsidian formatting
    clean = strip_obsidian_frontmatter(raw)
    clean = strip_obsidian_links(clean)
    clean = strip_obsidian_callouts(clean)

    # Check if this is narrative content
    if not is_narrative_content(clean):
        meta["_skip_reason"] = "not_narrative"
        return None, meta

    # Write clean text for pipeline
    stem = md_path.stem
    clean_path = md_path.parent / f"_clean_{stem}.txt"
    clean_path.write_text(clean, encoding="utf-8")

    meta["word_count"] = len(clean.split())
    meta["line_count"] = len(clean.splitlines())
    return clean_path, meta


def run_narrative_pipeline(
    input_txt: Path,
    output_dir: Path,
    pipeline_dir: Optional[Path] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Run Pass 1 → Pass 2 → Pass 3 on a clean text file.
    Returns (success, output_path_or_error, metadata).
    """
    if pipeline_dir is None or not (pipeline_dir / "pass1_explicit.py").exists():
        return False, "Cannot find pass1_explicit.py — set --pipeline-dir", {}

    stem = input_txt.stem
    if stem.startswith("_clean_"):
        stem = stem[7:]  # strip our temp prefix

    # Ensure output dir exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Work in a temp area
    work_dir = output_dir / "_work"
    work_dir.mkdir(exist_ok=True)

    # All intermediates go in work_dir so pass3 can find pass1+pass2 outputs
    pass1_out = work_dir / f"out_pass1_{stem}.txt"
    pass2_out = work_dir / f"out_pass2_{stem}.metta"
    pass3_out = output_dir / f"zonj_{stem}.json"

    meta = {"stem": stem}

    try:
        # Pass 1 — run from pipeline_dir so it finds any local resources
        r = subprocess.run(
            [sys.executable, str(pipeline_dir / "pass1_explicit.py"),
             str(input_txt), str(pass1_out)],
            capture_output=True, text=True, timeout=120,
            cwd=str(pipeline_dir),
        )
        if r.returncode != 0:
            return False, f"Pass 1 failed: {r.stderr[:500] or r.stdout[:500]}", meta

        if not pass1_out.exists():
            return False, f"Pass 1 produced no output at {pass1_out}", meta

        # Pass 2 — same working dir as pass1
        r = subprocess.run(
            [sys.executable, str(pipeline_dir / "pass2_core.py"),
             str(pass1_out), str(pass2_out)],
            capture_output=True, text=True, timeout=120,
            cwd=str(pipeline_dir),
        )
        if r.returncode != 0:
            return False, f"Pass 2 failed: {r.stderr[:500] or r.stdout[:500]}", meta

        if not pass2_out.exists():
            # Pass 2 may use different naming — check work_dir
            alt = list(work_dir.glob(f"out_pass2*{stem}*"))
            if alt:
                pass2_out = alt[0]
            else:
                return False, f"Pass 2 produced no output at {pass2_out}", meta

        # Pass 3 — run from work_dir so it can find both pass1 and pass2 files
        r = subprocess.run(
            [sys.executable, str(pipeline_dir / "pass3_merge.py"),
             str(pass1_out), str(pass2_out)],
            capture_output=True, text=True, timeout=120,
            cwd=str(work_dir),  # critical: pass3 looks for files relative to cwd
        )
        if r.returncode != 0:
            return False, f"Pass 3 failed: {r.stderr[:500] or r.stdout[:500]}", meta

        # Find the ZONJ output — check work_dir first (where pass3 ran), then output_dir
        zonj_candidates = list(work_dir.glob(f"zonj*{stem}*.json")) + \
                          list(work_dir.glob(f"zonj*.json")) + \
                          list(output_dir.glob(f"zonj*{stem}*.json"))
        if zonj_candidates:
            final = zonj_candidates[0]
            dest = output_dir / f"zonj_{stem}.json"
            shutil.move(str(final), str(dest))
            meta["zonj_path"] = str(dest)
            meta["zonj_size_kb"] = dest.stat().st_size / 1024
        else:
            return False, f"Pass 3 ran but no ZONJ output found in {work_dir}", meta

        return True, str(meta.get("zonj_path", "unknown")), meta

    except subprocess.TimeoutExpired:
        return False, "Pipeline timed out (120s)", meta
    except Exception as e:
        return False, str(e), meta


# ---------------------------------------------------------------------------
# FORMAT B: TRIXEL JSONL Score Files → Art Assets
# ---------------------------------------------------------------------------

def parse_trixel_score(jsonl_path: Path) -> Tuple[List[Dict], Dict[str, Any]]:
    """
    Parse a TRIXEL score .jsonl file.
    Each line is a JSON object with brush actions.
    Returns (actions, metadata).
    """
    actions = []
    errors = 0
    meta = {"path": str(jsonl_path)}

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                # Normalize: action may be nested or flat
                action = obj.get("action", obj)
                if isinstance(action.get("x"), (int, float)) and \
                   isinstance(action.get("y"), (int, float)):
                    actions.append(obj)
            except json.JSONDecodeError:
                errors += 1

    meta["total_actions"] = len(actions)
    meta["parse_errors"] = errors

    # Extract canvas bounds
    if actions:
        xs = [a.get("action", a).get("x", 0) for a in actions]
        ys = [a.get("action", a).get("y", 0) for a in actions]
        meta["canvas_bounds"] = {
            "min_x": min(xs), "max_x": max(xs),
            "min_y": min(ys), "max_y": max(ys),
        }

        # Extract unique colors
        colors = set()
        for a in actions:
            c = a.get("action", a).get("color")
            if isinstance(c, list) and len(c) == 3:
                colors.add(tuple(c))
        meta["unique_colors"] = len(colors)

    return actions, meta


def reconstruct_trixel_image(
    actions: List[Dict],
    output_path: Path,
    canvas_size: int = 64,
) -> bool:
    """
    Reconstruct a PNG image from TRIXEL brush actions.
    Returns True on success.
    """
    try:
        from PIL import Image
    except ImportError:
        print("  [WARN] Pillow not installed — skipping image reconstruction")
        print("         Install with: pip install pillow --break-system-packages")
        return False

    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    pixels = img.load()

    for a in actions:
        action = a.get("action", a)
        x = action.get("x", -1)
        y = action.get("y", -1)
        color = action.get("color", [0, 0, 0])

        if 0 <= x < canvas_size and 0 <= y < canvas_size:
            if isinstance(color, list) and len(color) >= 3:
                pixels[x, y] = (color[0], color[1], color[2], 255)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path))
    return True


def ingest_trixel_score(
    jsonl_path: Path,
    output_dir: Path,
) -> IngestResult:
    """Full TRIXEL ingest: parse → reconstruct → register."""
    actions, meta = parse_trixel_score(jsonl_path)
    stem = jsonl_path.stem

    if not actions:
        return IngestResult(
            source_path=str(jsonl_path),
            source_format="trixel_jsonl",
            output_path="",
            success=False,
            error="No valid brush actions found",
            metadata=meta,
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine canvas size from bounds
    bounds = meta.get("canvas_bounds", {})
    canvas_size = max(
        bounds.get("max_x", 63) + 1,
        bounds.get("max_y", 63) + 1,
        64,
    )

    # Reconstruct image
    img_path = output_dir / f"{stem}.png"
    img_ok = reconstruct_trixel_image(actions, img_path, canvas_size)

    # Save asset manifest
    asset_manifest = {
        "type": "trixel_asset",
        "id": stem,
        "source": str(jsonl_path),
        "canvas_size": canvas_size,
        "total_strokes": len(actions),
        "unique_colors": meta.get("unique_colors", 0),
        "image_path": str(img_path) if img_ok else None,
        "timestamp": datetime.now().isoformat(),
    }

    manifest_path = output_dir / f"{stem}_asset.json"
    manifest_path.write_text(json.dumps(asset_manifest, indent=2), encoding="utf-8")
    meta["asset_manifest"] = str(manifest_path)

    return IngestResult(
        source_path=str(jsonl_path),
        source_format="trixel_jsonl",
        output_path=str(manifest_path),
        success=True,
        metadata=meta,
    )


# ---------------------------------------------------------------------------
# FORMAT C: ChatGPT Conversation Exports → Knowledge Extraction
# ---------------------------------------------------------------------------

def is_chatgpt_export(file_path: Path) -> bool:
    """Detect if a file is a ChatGPT conversation export."""
    try:
        head = file_path.read_text(encoding="utf-8", errors="replace")[:2000]
        return bool(CHATGPT_MARKER_RE.search(head))
    except Exception:
        return False


def parse_chatgpt_export(file_path: Path) -> Dict[str, Any]:
    """
    Parse a ChatGPT conversation export into structured data.
    Extracts: conversation turns, code blocks, topics.
    """
    text = file_path.read_text(encoding="utf-8", errors="replace")

    # Split into turns
    turns = []
    current_speaker = None
    current_lines = []

    for line in text.splitlines():
        # Check for speaker markers
        if line.strip() == "You said:" or line.strip() == "Human:":
            if current_speaker and current_lines:
                turns.append({"speaker": current_speaker, "text": "\n".join(current_lines)})
            current_speaker = "user"
            current_lines = []
        elif line.strip().startswith("ChatGPT said:") or line.strip() == "Assistant:":
            if current_speaker and current_lines:
                turns.append({"speaker": current_speaker, "text": "\n".join(current_lines)})
            current_speaker = "assistant"
            current_lines = []
        elif line.strip().startswith("Thought for"):
            continue  # Skip thinking markers
        else:
            current_lines.append(line)

    if current_speaker and current_lines:
        turns.append({"speaker": current_speaker, "text": "\n".join(current_lines)})

    # Extract code blocks
    code_blocks = []
    for i, turn in enumerate(turns):
        for m in CODE_BLOCK_RE.finditer(turn["text"]):
            lang = m.group(1) or "unknown"
            code = m.group(2).strip()
            code_blocks.append({
                "turn": i,
                "language": lang,
                "code": code,
                "line_count": len(code.splitlines()),
            })

    # Extract file references
    file_refs = set()
    for turn in turns:
        # Look for file paths
        for m in re.finditer(r'[\w/.-]+\.(py|gd|json|txt|md|tscn|tres|zw|zon|zonb|metta)\b', turn["text"]):
            file_refs.add(m.group(0))

    return {
        "source": str(file_path),
        "turns": len(turns),
        "user_turns": sum(1 for t in turns if t["speaker"] == "user"),
        "assistant_turns": sum(1 for t in turns if t["speaker"] == "assistant"),
        "code_blocks": code_blocks,
        "code_block_count": len(code_blocks),
        "languages": list(set(cb["language"] for cb in code_blocks)),
        "file_references": sorted(file_refs),
        "total_words": sum(len(t["text"].split()) for t in turns),
    }


def ingest_chatgpt_export(
    file_path: Path,
    output_dir: Path,
) -> IngestResult:
    """Parse ChatGPT export and save structured knowledge."""
    try:
        data = parse_chatgpt_export(file_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        stem = file_path.stem
        out_path = output_dir / f"knowledge_{stem}.json"
        out_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

        # Also extract code blocks into separate files
        if data["code_blocks"]:
            code_dir = output_dir / f"{stem}_code"
            code_dir.mkdir(exist_ok=True)
            for i, cb in enumerate(data["code_blocks"]):
                ext = {
                    "python": ".py", "py": ".py",
                    "gdscript": ".gd", "gd": ".gd",
                    "json": ".json", "bash": ".sh",
                    "javascript": ".js", "js": ".js",
                }.get(cb["language"], ".txt")
                code_file = code_dir / f"block_{i:03d}{ext}"
                code_file.write_text(cb["code"], encoding="utf-8")

        return IngestResult(
            source_path=str(file_path),
            source_format="chatgpt_export",
            output_path=str(out_path),
            success=True,
            metadata={
                "turns": data["turns"],
                "code_blocks": data["code_block_count"],
                "languages": data["languages"],
                "file_refs": len(data["file_references"]),
            },
        )
    except Exception as e:
        return IngestResult(
            source_path=str(file_path),
            source_format="chatgpt_export",
            output_path="",
            success=False,
            error=str(e),
        )


# ---------------------------------------------------------------------------
# Format Detection
# ---------------------------------------------------------------------------

def detect_format(file_path: Path) -> str:
    """Auto-detect the format of a file."""
    ext = file_path.suffix.lower()

    if ext == ".jsonl":
        return "trixel_jsonl"

    if ext == ".md":
        return "obsidian_md"

    if ext in (".txt", ".text", ""):
        # Check if it's a ChatGPT export
        if is_chatgpt_export(file_path):
            return "chatgpt_export"
        return "raw_text"

    if ext == ".json":
        # Could be ChatGPT JSON export or TRIXEL memory
        try:
            data = json.loads(file_path.read_text(encoding="utf-8")[:5000])
            if isinstance(data, list) and data and "message" in data[0]:
                return "chatgpt_export"
        except Exception:
            pass
        return "json_data"

    return "unknown"


# ---------------------------------------------------------------------------
# Batch Ingest
# ---------------------------------------------------------------------------

def scan_directory(
    root: Path,
    recursive: bool = True,
) -> List[Tuple[Path, str]]:
    """Walk a directory and classify all files by format."""
    results = []
    pattern = "**/*" if recursive else "*"

    for p in sorted(root.glob(pattern)):
        if p.is_file() and not p.name.startswith("_") and not p.name.startswith("."):
            fmt = detect_format(p)
            if fmt != "unknown":
                results.append((p, fmt))

    return results


def ingest_file(
    file_path: Path,
    fmt: str,
    output_dir: Path,
    pipeline_dir: Optional[Path] = None,
) -> IngestResult:
    """Ingest a single file based on its detected format."""

    if fmt == "obsidian_md":
        clean_path, meta = prepare_obsidian_for_pass1(file_path)
        if clean_path is None:
            return IngestResult(
                source_path=str(file_path),
                source_format="obsidian_md",
                output_path="",
                success=False,
                error=meta.get("_skip_reason", "not_narrative"),
                metadata=meta,
            )
        ok, result, pipe_meta = run_narrative_pipeline(
            clean_path, output_dir / "scenes", pipeline_dir
        )
        meta.update(pipe_meta)
        # Clean up temp file
        clean_path.unlink(missing_ok=True)
        return IngestResult(
            source_path=str(file_path),
            source_format="obsidian_md",
            output_path=result if ok else "",
            success=ok,
            error=None if ok else result,
            metadata=meta,
        )

    elif fmt == "raw_text":
        # Raw text goes straight to narrative pipeline
        ok, result, meta = run_narrative_pipeline(
            file_path, output_dir / "scenes", pipeline_dir
        )
        return IngestResult(
            source_path=str(file_path),
            source_format="raw_text",
            output_path=result if ok else "",
            success=ok,
            error=None if ok else result,
            metadata=meta,
        )

    elif fmt == "trixel_jsonl":
        return ingest_trixel_score(file_path, output_dir / "assets")

    elif fmt == "chatgpt_export":
        return ingest_chatgpt_export(file_path, output_dir / "knowledge")

    else:
        return IngestResult(
            source_path=str(file_path),
            source_format=fmt,
            output_path="",
            success=False,
            error=f"Unsupported format: {fmt}",
        )


def batch_ingest(
    files: List[Tuple[Path, str]],
    output_dir: Path,
    pipeline_dir: Optional[Path] = None,
    runtime_url: Optional[str] = None,
) -> IngestManifest:
    """Ingest a batch of files and produce a manifest."""
    manifest = IngestManifest(
        timestamp=datetime.now().isoformat(),
        source_dir=str(files[0][0].parent) if files else "",
        output_dir=str(output_dir),
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    for i, (path, fmt) in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {fmt:20s} → {path.name}")
        result = ingest_file(path, fmt, output_dir, pipeline_dir)

        if result.success:
            print(f"  ✓ {result.output_path}")

            # POST to runtime if configured
            if runtime_url and fmt in ("obsidian_md", "raw_text") and result.output_path:
                try:
                    import urllib.request
                    zonj_data = Path(result.output_path).read_text(encoding="utf-8")
                    req = urllib.request.Request(
                        f"{runtime_url}/scene/load",
                        data=zonj_data.encode(),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        print(f"  ↗ Runtime: {resp.status}")
                except Exception as e:
                    print(f"  ⚠ Runtime POST failed: {e}")
        else:
            print(f"  ✗ {result.error}")

        manifest.results.append(result)

    # Save manifest
    manifest_path = output_dir / "ingest_manifest.json"
    manifest_path.write_text(
        json.dumps(asdict(manifest), indent=2, default=str),
        encoding="utf-8",
    )

    return manifest


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="EngAIn Unified Ingest System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --vault ~/obsidian/burdens/ --out ./ingested/
  %(prog)s --file chapter_03.md --out ./scenes/
  %(prog)s --trixel .zw/scores/ --out ./assets/
  %(prog)s --chatgpt export.txt --out ./knowledge/
  %(prog)s --scan ~/Downloads/EngAIn/ --out ./all_ingested/
        """,
    )

    # Input sources (pick one)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--vault", help="Obsidian vault directory to ingest")
    group.add_argument("--file", help="Single file to ingest (auto-detect format)")
    group.add_argument("--trixel", help="Directory of TRIXEL .jsonl score files")
    group.add_argument("--chatgpt", help="ChatGPT export file to parse")
    group.add_argument("--scan", help="Scan directory and auto-detect all formats")
    group.add_argument("--load-zonj", help="Load existing ZONJ files (skip pipeline, just feed to runtime)")

    # Output
    ap.add_argument("--out", help="Output directory (defaults to build.output_dir in vault.manifest.json if found)")

    # Options
    ap.add_argument("--pipeline-dir", help="Directory containing pass1/2/3 scripts")
    ap.add_argument("--runtime", help="Runtime URL (e.g. http://localhost:5000) to POST scenes")
    ap.add_argument("--no-recursive", action="store_true", help="Don't recurse into subdirs")
    ap.add_argument("--dry-run", action="store_true", help="Scan and classify only, don't ingest")

    args = ap.parse_args()

    # Automatic output_dir discovery via manifest
    manifest_out = None
    vault_root = None
    if args.vault:
        vault_root = Path(args.vault).expanduser().resolve()
    elif args.file:
        # Check parent of file for manifest
        parent = Path(args.file).expanduser().resolve().parent
        if (parent / "vault.manifest.json").exists():
            vault_root = parent
    
    if not vault_root and (Path.cwd() / "vault.manifest.json").exists():
        vault_root = Path.cwd()

    if vault_root:
        mpath = vault_root / "vault.manifest.json"
        if mpath.exists():
            try:
                with open(mpath, "r", encoding="utf-8") as f:
                    mdata = json.load(f)
                    m_out = mdata.get("build", {}).get("output_dir")
                    if m_out:
                        p_out = Path(m_out)
                        if not p_out.is_absolute():
                            p_out = vault_root / p_out
                        manifest_out = p_out.resolve()
                        print(f"  (Manifest detected: using output_dir {manifest_out})")
            except Exception as e:
                print(f"  ⚠ Failed to parse manifest at {mpath}: {e}", file=sys.stderr)

    if args.out:
        output_dir = Path(args.out)
    elif manifest_out:
        output_dir = manifest_out
    else:
        print("ERROR: --out required if no vault.manifest.json found", file=sys.stderr)
        return 1

    pipeline_dir = Path(args.pipeline_dir) if args.pipeline_dir else None

    files: List[Tuple[Path, str]] = []

    if args.vault:
        vault = Path(args.vault).expanduser()
        if not vault.is_dir():
            print(f"ERROR: Vault directory not found: {vault}", file=sys.stderr)
            return 1
        mpath = vault / "vault.manifest.json"
        if not mpath.exists():
            print(f"ERROR: Missing vault manifest: {mpath}", file=sys.stderr)
            return 1
        try:
            mdata = json.loads(mpath.read_text(encoding="utf-8"))
        except Exception:
            print(f"ERROR: Invalid JSON in vault manifest: {mpath}", file=sys.stderr)
            return 1
        source_files = mdata.get("source_files")
        if not isinstance(source_files, list) or not source_files:
            print("ERROR: vault.manifest.json must contain non-empty 'source_files' list", file=sys.stderr)
            return 1
        for src in source_files:
            if not isinstance(src, str) or not src.strip():
                print("ERROR: vault.manifest.json source_files entries must be non-empty strings", file=sys.stderr)
                return 1
            p = Path(src)
            if not p.is_absolute():
                p = mpath.parent / p
            if not p.exists() or not p.is_file():
                print(f"ERROR: source_files entry does not exist: {p}", file=sys.stderr)
                return 1
            fmt = detect_format(p)
            files.append((p, fmt))

    elif args.file:
        fp = Path(args.file).expanduser()
        if not fp.exists():
            print(f"ERROR: File not found: {fp}", file=sys.stderr)
            return 1
        fmt = detect_format(fp)
        files.append((fp, fmt))

    elif args.trixel:
        tdir = Path(args.trixel).expanduser()
        if not tdir.is_dir():
            print(f"ERROR: Directory not found: {tdir}", file=sys.stderr)
            return 1
        for p in sorted(tdir.glob("*.jsonl")):
            files.append((p, "trixel_jsonl"))

    elif args.chatgpt:
        fp = Path(args.chatgpt).expanduser()
        if not fp.exists():
            print(f"ERROR: File not found: {fp}", file=sys.stderr)
            return 1
        files.append((fp, "chatgpt_export"))

    elif args.scan:
        scan_dir = Path(args.scan).expanduser()
        if not scan_dir.is_dir():
            print(f"ERROR: Directory not found: {scan_dir}", file=sys.stderr)
            return 1
        files = scan_directory(scan_dir, recursive=not args.no_recursive)

    elif args.load_zonj:
        # Special mode: skip pipeline, just collect existing ZONJ files
        zonj_source = Path(args.load_zonj).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)

        zonj_files = []
        if zonj_source.is_file() and zonj_source.suffix == ".json":
            zonj_files = [zonj_source]
        elif zonj_source.is_dir():
            zonj_files = sorted(zonj_source.rglob("*.json"))
        else:
            print(f"ERROR: Not a file or directory: {zonj_source}", file=sys.stderr)
            return 1

        # Filter to actual ZONJ scene files
        valid_zonj = []
        for zf in zonj_files:
            try:
                with open(zf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # ZONJ files should have segments or type=scene
                if isinstance(data, dict) and any(k in data for k in ("segments", "scene_id", "entities", "events", "locations")) or data.get("type") == "scene":
                    valid_zonj.append(zf)
            except Exception:
                pass

        print(f"\n{'='*60}")
        print(f"  EngAIn ZONJ Loader")
        print(f"  ZONJ files found: {len(valid_zonj)} / {len(zonj_files)} scanned")
        print(f"  Runtime: {args.runtime or 'none (copy only)'}")
        print(f"{'='*60}\n")

        if args.dry_run:
            for zf in valid_zonj:
                print(f"  [zonj] {zf}")
            return 0

        loaded = 0
        for zf in valid_zonj:
            dest = output_dir / zf.name
            if dest.exists():
                dest.chmod(0o644)  # ensure writable
            if zf != dest:
                shutil.copy2(str(zf), str(dest))
                dest.chmod(0o644)  # keep writable for next run

            if args.runtime:
                try:
                    import urllib.request
                    zonj_data = zf.read_text(encoding="utf-8")
                    req = urllib.request.Request(
                        f"{args.runtime}/scene/load",
                        data=zonj_data.encode(),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        print(f"  ✓ {zf.stem} → runtime ({resp.status})")
                        loaded += 1
                except Exception as e:
                    print(f"  ⚠ {zf.stem} → runtime failed: {e}")
            else:
                print(f"  ✓ {zf.stem} → {dest}")
                loaded += 1

        print(f"\n  Loaded {loaded}/{len(valid_zonj)} scenes")
        return 0

    if not files:
        print("No files found to ingest.")
        return 0

    # Report what we found
    print(f"\n{'='*60}")
    print(f"  EngAIn Ingest System")
    print(f"  Files found: {len(files)}")
    by_fmt = {}
    for _, fmt in files:
        by_fmt[fmt] = by_fmt.get(fmt, 0) + 1
    for fmt, count in sorted(by_fmt.items()):
        print(f"    {fmt}: {count}")
    print(f"  Output: {output_dir}")
    print(f"{'='*60}\n")

    if args.dry_run:
        print("DRY RUN — listing files only:\n")
        for p, fmt in files:
            print(f"  [{fmt:20s}] {p}")
        return 0

    # Run ingest
    manifest = batch_ingest(files, output_dir, pipeline_dir, args.runtime)

    # Print summary
    s = manifest.summary
    print(f"\n{'='*60}")
    print(f"  INGEST COMPLETE")
    print(f"  Total: {s['total']}  Success: {s['success']}  Failed: {s['failed']}")
    for fmt, count in s["by_format"].items():
        print(f"    {fmt}: {count}")
    print(f"  Manifest: {output_dir / 'ingest_manifest.json'}")
    print(f"{'='*60}\n")

    return 0 if s["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
