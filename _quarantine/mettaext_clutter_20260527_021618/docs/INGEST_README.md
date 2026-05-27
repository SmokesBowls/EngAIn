# EngAIn Ingest — Quick Reference

## What This Does
Turns your raw content into engine-ready data.
Chapters become ZONJ scenes. TRIXEL scores become sprite assets.
Or — loads ZONJ files you've ALREADY processed straight into the runtime.

## You Already Have Processed Data
Your `mettaext/` directory already contains ZONJ scenes from previous pipeline runs:
- `game_scenes/*.json` — 5 chapters, ready to go
- `narrative_work/zon/*.zonj.json` — 5 more chapters
- `pipeline_work/*.zonj.json` — additional processed chapters

**Start here** — feed what you have to the runtime:

### Load existing ZONJ scenes into running engine
```bash
python3 engain_ingest.py --load-zonj ~/Downloads/EngAIn/mettaext/game_scenes/ --out ./loaded/ --runtime http://localhost:5000
```

### See what ZONJ files you have (dry run)
```bash
python3 engain_ingest.py --load-zonj ~/Downloads/EngAIn/mettaext/ --out ./loaded/ --dry-run
```

## Processing New Chapters

### Process one chapter through the full pipeline
```bash
python3 engain_ingest.py --file 03_Fist_contact.txt --out ./ingested/ --pipeline-dir ~/Downloads/EngAIn/mettaext/
```

### Process ALL chapters in a folder at once
```bash
python3 engain_ingest.py --scan ~/Downloads/EngAIn/mettaext/book/ --out ./ingested/ --pipeline-dir ~/Downloads/EngAIn/mettaext/
```

### See what it WOULD do without doing anything
```bash
python3 engain_ingest.py --scan ~/Downloads/EngAIn/mettaext/ --out ./ingested/ --dry-run
```

### Push scenes straight into the running engine
```bash
python3 engain_ingest.py --file 03_Fist_contact.txt --out ./ingested/ --pipeline-dir ~/Downloads/EngAIn/mettaext/ --runtime http://localhost:5000
```

## Where Things End Up

```
./ingested/
├── scenes/          ← ZONJ files (chapters → playable scenes)
├── assets/          ← TRIXEL PNGs + manifests (art scores → sprites)
├── knowledge/       ← Parsed ChatGPT exports (dev history)
└── ingest_manifest.json  ← What was processed, what succeeded/failed
```

## What Each Format Produces

| Input | Format | Output |
|-------|--------|--------|
| `chapter_03.txt` | raw text | `zonj_chapter_03.json` (scene) |
| `chapter_03.md` | Obsidian note | same, with frontmatter stripped |
| `score.jsonl` | TRIXEL brush strokes | `score.png` + `score_asset.json` |
| `chatgpt_export.txt` | conversation dump | `knowledge_*.json` + extracted code |
| `scene.json` (via --load-zonj) | existing ZONJ | copied + POSTed to runtime |

## Setup
Drop `engain_ingest.py` into `~/Downloads/EngAIn/mettaext/` alongside your pass1/2/3 scripts.
That's it. No install, no dependencies beyond what pass1/2/3 already need.
(Pillow needed only for TRIXEL image reconstruction — `pip install pillow`)
