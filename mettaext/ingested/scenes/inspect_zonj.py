#!/usr/bin/env python3
"""
inspect_zonj.py — EngAIn ZONJ File Inspector
Reveals the actual key structure of a .zonj.json file so you can see
why _normalize_scene() returns scene_id:"unknown" and segments:0.

Usage:
  python3 inspect_zonj.py /path/to/12_nephilim_summoning.zonj.json
  python3 inspect_zonj.py   # defaults to nephilim scene
"""
import json
import sys
from pathlib import Path

DEFAULT = Path.home() / "burdens_of_a_forgotten_past/EngAIn/mettaext/ingested/scenes/12_nephilim_summoning.zonj.json"


def inspect(path: Path):
    print(f"\n{'='*60}")
    print(f"  ZONJ Inspector — {path.name}")
    print(f"{'='*60}\n")

    raw = path.read_text(encoding="utf-8", errors="ignore")
    print(f"File size: {len(raw)} bytes")

    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        return

    print(f"Root type: {type(doc).__name__}")

    # --- Handle list-of-docs case ---
    if isinstance(doc, list):
        print(f"Root is a LIST with {len(doc)} items")
        if doc:
            first = doc[0]
            print(f"  first item type: {type(first).__name__}")
            if isinstance(first, dict):
                print(f"  first item keys: {sorted(first.keys())[:30]}")
                _inspect_dict(first, label="doc[0]")
        return

    if not isinstance(doc, dict):
        print(f"Unexpected root type: {type(doc).__name__}")
        return

    _inspect_dict(doc, label="root")


def _inspect_dict(doc: dict, label: str = "root"):
    keys = sorted(doc.keys())
    print(f"\n[{label}] Top-level keys ({len(keys)}):")
    for k in keys:
        v = doc[k]
        vtype = type(v).__name__
        if isinstance(v, str):
            preview = repr(v[:120]) + ("..." if len(v) > 120 else "")
            print(f"  {k:25s}  str     = {preview}")
        elif isinstance(v, list):
            print(f"  {k:25s}  list    len={len(v)}")
            if v and isinstance(v[0], dict):
                print(f"    [0] keys: {sorted(v[0].keys())[:20]}")
        elif isinstance(v, dict):
            print(f"  {k:25s}  dict    keys={sorted(v.keys())[:15]}")
        elif isinstance(v, (int, float)):
            print(f"  {k:25s}  {vtype:7s} = {v}")
        elif v is None:
            print(f"  {k:25s}  null")
        else:
            print(f"  {k:25s}  {vtype}")

    # --- ID candidates ---
    print(f"\n[{label}] ID Resolution:")
    for k in ("scene_id", "@id", "id", "sceneId", "slug", "name", "key"):
        if k in doc:
            print(f"  ✓ {k} = {repr(doc[k])[:200]}")
    if not any(k in doc for k in ("scene_id", "@id", "id", "sceneId", "slug", "name")):
        print("  ⚠ No standard ID field found → _normalize_scene will hash or use 'unknown'")

    # --- Segment candidates ---
    print(f"\n[{label}] Segment Resolution:")
    for k in ("=segments", "segments"):
        v = doc.get(k)
        present = k in doc
        vtype = type(v).__name__ if present else "N/A"
        vlen = len(v) if isinstance(v, list) else None
        status = "✓" if (isinstance(v, list) and len(v) > 0) else "✗"
        print(f"  {status} {k:15s}  present={present}  type={vtype}  len={vlen}")

    # --- Entity candidates ---
    print(f"\n[{label}] Entity Resolution:")
    for k in ("@entities", "entities"):
        v = doc.get(k)
        present = k in doc
        vlen = len(v) if isinstance(v, list) else None
        print(f"  {'✓' if vlen else '✗'} {k:15s}  present={present}  len={vlen}")

    # --- Metadata candidates ---
    print(f"\n[{label}] Metadata Fields:")
    for k in ("@when", "when", "@where", "where", "@scope", "scope"):
        v = doc.get(k)
        if v is not None:
            print(f"  ✓ {k:15s} = {repr(v)[:120]}")

    # --- Check for nested containers ---
    print(f"\n[{label}] Nested Container Check:")
    found_nested = False
    for nk in ("payload", "scene", "doc", "data", "body", "content", "result"):
        nv = doc.get(nk)
        if isinstance(nv, dict):
            found_nested = True
            print(f"  ✓ {nk} is a dict with keys: {sorted(nv.keys())[:20]}")
            for sk in ("=segments", "segments"):
                sv = nv.get(sk)
                if isinstance(sv, list) and sv:
                    print(f"    ⚡ {nk}.{sk} has {len(sv)} segments — THIS is where your data lives!")
    if not found_nested:
        print("  (none found)")

    # --- Text fallback ---
    print(f"\n[{label}] Text Fallback:")
    for k in ("text", "body", "content"):
        v = doc.get(k)
        if isinstance(v, str) and v.strip():
            print(f"  ✓ {k} = {len(v)} chars (first 100: {repr(v[:100])})")

    # --- Diagnosis ---
    print(f"\n{'='*60}")
    print("  DIAGNOSIS")
    print(f"{'='*60}")

    segs = doc.get("=segments")
    if isinstance(segs, list) and segs:
        print("  ✅ =segments present and non-empty → sim_runtime should work as-is")
    else:
        segs2 = doc.get("segments")
        if isinstance(segs2, list) and segs2:
            print("  ⚠️  segments present but =segments missing")
            print("     → Patch _normalize_scene() to also check 'segments' key")
            print("     → OR rename key before POSTing")
        else:
            # check nested
            for nk in ("payload", "scene", "doc", "data"):
                nv = doc.get(nk)
                if isinstance(nv, dict):
                    for sk in ("=segments", "segments"):
                        sv = nv.get(sk)
                        if isinstance(sv, list) and sv:
                            print(f"  ⚠️  Segments are nested inside '{nk}.{sk}'")
                            print(f"     → Patch _normalize_scene() to unwrap '{nk}' container")
                            return
            text = doc.get("text") or doc.get("body") or doc.get("content")
            if isinstance(text, str) and text.strip():
                print("  ⚠️  No segments at all — but raw text is present")
                print("     → This file was never segmented (Pass 1/2/3 not run)")
                print("     → sim_runtime will use text fallback (segments=0 is expected)")
            else:
                print("  ❌ No segments, no text — this file is metadata-only")
                print("     → The ingestion pipeline did not produce segment data for this scene")
                print("     → Re-run Pass 1→2→3 or check your ingestion scripts")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        p = Path(sys.argv[1])
    else:
        p = DEFAULT

    if not p.exists():
        print(f"File not found: {p}")
        # Try listing available files
        scenes_dir = p.parent
        if scenes_dir.exists():
            matches = sorted(f.name for f in scenes_dir.iterdir() if "nephilim" in f.name.lower())
            if matches:
                print(f"Available nephilim files: {matches}")
        sys.exit(1)

    inspect(p)
