#!/usr/bin/env python3
"""Gen2 orchestrator: one Chapterroom scene -> mettaext.parse_artifact.v2.

Builds the module DAG from declared requires/produces, runs it fail-closed
(GEN2_MODULES.md §1.1 rule 6), then assembles and validates the artifact.

Usage (from repo root, PYTHONPATH=.):
  python3 -m tier3.mettaextgen2.orchestrator \\
      --chapter-id chapter.book009.048_the_ledger_born \\
      --scene-id scene.book009.048_the_ledger_born.scene005 \\
      [--chapterroom-root tier3/mettaext/stageroom/output/chapterroom] [--output FILE]

Without --output the artifact is printed to stdout. Gen2 never dispatches,
never requests admission, and never writes outside --output.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Sequence

from .lib.annotations import AnnotationStore, Module
from .modules import source_loader
from .modules.artifact_assembler import AssemblyError, assemble
from .modules.entity_extractor import EntityExtractor
from .modules.linguistic_annotator import LinguisticAnnotator
from .modules.metadata_reader import MetadataReader
from .modules.presence_detector import PresenceDetector
from .modules.reconciler import Reconciler
from .modules.scene_segmenter import SceneSegmenter

DEFAULT_CHAPTERROOM_ROOT = Path(__file__).resolve().parents[1] / "mettaext" / "stageroom" / "output" / "chapterroom"


def default_modules() -> List[Module]:
    return [SceneSegmenter(), MetadataReader(), LinguisticAnnotator(), EntityExtractor(),
            PresenceDetector(), Reconciler()]


def order_modules(modules: Sequence[Module]) -> List[Module]:
    """Topological order: a module runs after every module producing a kind it requires."""
    producers: Dict[str, List[Module]] = {}
    for m in modules:
        for kind in m.produces:
            producers.setdefault(kind, []).append(m)
    for m in modules:
        missing = [k for k in m.requires if k not in producers]
        if missing:
            raise ValueError(f"{m.name} requires kinds no module produces: {sorted(missing)}")
    ordered: List[Module] = []
    pending = list(modules)
    while pending:
        ready = [m for m in pending
                 if all(p in ordered for k in m.requires for p in producers[k] if p is not m)]
        if not ready:
            raise ValueError(f"module dependency cycle among {[m.name for m in pending]}")
        ordered.append(ready[0])
        pending.remove(ready[0])
    return ordered


def run_scene(chapterroom_root: Path, chapter_id: str, scene_id: str,
              modules: Sequence[Module] | None = None) -> dict:
    doc, scene = source_loader.load_scene_source(chapterroom_root, chapter_id, scene_id)
    store = AnnotationStore()
    warnings: List[str] = []
    failed: set = set()
    descriptions = [{"name": source_loader.NAME, "version": source_loader.VERSION, "implementation_kind": "rules"}]
    for module in order_modules(modules or default_modules()):
        descriptions.append(module.describe())
        blocked = [k for k in module.requires if k in failed]
        if blocked:
            warnings.append(f"module_skipped: {module.name} (inputs unavailable: {sorted(blocked)})")
            failed.update(module.produces)
            continue
        try:
            output = module.run(doc, scene, store.view())
            store.add(module, output)
        except Exception:
            warnings.append(f"module_failed: {module.name}: {traceback.format_exc(limit=3).strip()}")
            failed.update(module.produces)
            continue
        warnings.extend(f"{d.level}: {module.name}: {d.message}" for d in output.diagnostics)
    descriptions.append({"name": "artifact_assembler", "version": "0.1.0", "implementation_kind": "rules"})
    challenges = [{"by_module": by, "target_annotation": c.target_annotation_id, "reason": c.reason}
                  for by, c in store.challenges]
    return assemble(doc, scene, store.view(), descriptions, warnings, challenges)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--chapter-id", required=True)
    parser.add_argument("--scene-id", required=True)
    parser.add_argument("--chapterroom-root", type=Path, default=DEFAULT_CHAPTERROOM_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        artifact = run_scene(args.chapterroom_root, args.chapter_id, args.scene_id)
    except (source_loader.SourceLoadError, AssemblyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(artifact, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
