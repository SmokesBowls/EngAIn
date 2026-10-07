"""reconciler (GEN2_MODULES.md §2.16) — intra-run only.

Input:   entity_mention / entity_rejection / presence / metadata_constraint.
Output:  `reconciled_entity`, `reconciled_location`, `alias_candidate`
         annotations carrying run-local refs (ent_NNN / loc_NNN). Refs mean
         nothing outside this run.
Authority ends at the artifact boundary: no registry writes, no canonical ids,
no cross-run decisions.

Linking (deterministic):
  1. A prose mention whose normalised surface equals a participant name links
     to it.
  2. A single-word mention links to participants containing that word
     (singular/plural tolerant). If several qualify, the one whose first word
     matches is primary and the others are kept as alternatives. Every
     non-exact link is also emitted as an ALIAS_CANDIDATE (scope "span").
  3. A prose mention equal to a metadata location segment becomes location
     evidence, not an entity.
  4. Anything else is a prose-only CANDIDATE (presence unknown).
  Rejections become REJECTED declarations, unless the same surface was
  accepted elsewhere in the scene.

Confidence (proposal strength, not truth):
  participant           0.90, +0.05 with prose corroboration
  prose-only candidate  0.55 + 0.10 per extra mention (max 0.85),
                        -0.10 if only corroborated (no mid-sentence capital)
  location              0.80, +0.10 with prose corroboration
  rejected              0.10
  alias candidate       0.75, or 0.60 when alternatives exist
"""

from __future__ import annotations

import re
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

from ..lib.annotations import Annotation, AnnotationView, Module, ModuleOutput, NewAnnotation, SceneInput
from ..lib.source import SourceDocument, Span


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("’", "'")).strip().lower()


def _word_forms(word: str) -> set:
    w = _norm(word)
    return {w, w + "s", w[:-1] if w.endswith("s") else w}


class Reconciler(Module):
    name = "reconciler"
    version = "0.1.0"
    implementation_kind = "rules"
    requires = frozenset({"entity_mention", "entity_rejection", "presence", "metadata_constraint", "region"})
    produces = frozenset({"reconciled_entity", "reconciled_location", "alias_candidate"})

    def run(self, doc: SourceDocument, scene: SceneInput, view: AnnotationView) -> ModuleOutput:
        out = ModuleOutput()
        mentions = view.by_kind("entity_mention")
        presence = {_norm(p.value["subject"]): p for p in view.by_kind("presence")}

        # -- locations from author metadata, corroborated in prose -------------
        locations: "OrderedDict[str, Dict]" = OrderedDict()
        for c in view.by_kind("metadata_constraint"):
            if (c.value.get("key", "").split(".")[-1].strip().lower() == "location"
                    and c.value.get("subject")):
                key = _norm(c.value["subject"])
                loc = locations.setdefault(key, {"surface": c.value["subject"], "primary": c.span, "evidence": []})
                loc["evidence"].append(c.span)
        prose_regions = [r for r in view.by_kind("region") if r.value["region_type"] == "prose"]
        for loc in locations.values():
            loc["evidence"].extend(self._find_phrase(doc, prose_regions, loc["surface"]))

        # -- participants ------------------------------------------------------
        entities: "OrderedDict[str, Dict]" = OrderedDict()
        for m in mentions:
            if m.value["evidence_class"] != "AUTHOR_METADATA":
                continue
            key = _norm(m.value["surface"])
            p = presence.get(key)
            entities[key] = {
                "surface": m.value["surface"], "kind": "participant", "primary": m.span,
                "evidence": [m.span], "prose_mentions": 0, "only_corroborated": True,
                "number_headed": m.value["number_headed"],
                "presence": p.value["presence"] if p else "unknown",
                "qualifier": p.value["qualifier"] if p else None,
            }

        aliases: List[Tuple[Annotation, str, List[str]]] = []
        for m in mentions:
            if m.value["evidence_class"] != "PROSE":
                continue
            key = _norm(m.value["surface"])
            if key in locations:
                locations[key]["evidence"].append(m.span)
                continue
            target, alternatives = self._link(key, entities)
            if target is None:
                ent = entities.setdefault(f"prose:{key}", {
                    "surface": m.value["surface"], "kind": "prose", "primary": m.span, "evidence": [],
                    "prose_mentions": 0, "only_corroborated": True, "number_headed": m.value["number_headed"],
                    "presence": "unknown", "qualifier": None,
                })
                target = f"prose:{key}"
            else:
                ent = entities[target]
                if key != target:
                    aliases.append((m, target, alternatives))
            ent["evidence"].append(m.span)
            ent["prose_mentions"] += 1
            if m.value["basis"] == "proper_capital":
                ent["only_corroborated"] = False

        accepted_surfaces = {_norm(e["surface"]) for e in entities.values()} | set(locations)
        rejected: "OrderedDict[str, Dict]" = OrderedDict()
        for r in view.by_kind("entity_rejection"):
            key = _norm(r.value["surface"])
            if key in accepted_surfaces:
                continue
            rej = rejected.setdefault(key, {"surface": r.value["surface"], "primary": r.span,
                                            "evidence": [], "reasons": []})
            rej["evidence"].append(r.span)
            if r.value["reason"] not in rej["reasons"]:
                rej["reasons"].append(r.value["reason"])

        # -- refs (run-local, ordered by first evidence offset) ----------------
        def first_offset(item: Dict) -> int:
            return min(s.char_start for s in item["evidence"] + [item["primary"]])

        ref_of: Dict[str, str] = {}
        ordered = sorted(list(entities.items()) + [(f"rejected:{k}", v) for k, v in rejected.items()],
                         key=lambda kv: first_offset(kv[1]))
        for n, (key, _) in enumerate(ordered, 1):
            ref_of[key] = f"ent_{n:03d}"

        for key, item in ordered:
            evidence = sorted(set(item["evidence"]), key=lambda s: s.char_start)
            if key.startswith("rejected:"):
                value = {
                    "local_ref": ref_of[key], "surface": item["surface"], "entity_type": "unknown",
                    "status": "REJECTED", "presence": "unknown", "evidence_class": "PROSE",
                    "evidence": evidence, "alternatives": [],
                    "notes": "rejected: " + ", ".join(item["reasons"]),
                }
                confidence = 0.10
            elif item["kind"] == "participant":
                value = {
                    "local_ref": ref_of[key], "surface": item["surface"],
                    "entity_type": "group" if item["number_headed"] else "character",
                    "status": "OBSERVED", "presence": item["presence"], "evidence_class": "AUTHOR_METADATA",
                    "evidence": evidence, "alternatives": [],
                    "notes": f"author qualifier: {item['qualifier']}" if item["qualifier"] else "author participant, no qualifier",
                }
                confidence = 0.95 if item["prose_mentions"] else 0.90
            else:
                confidence = min(0.85, 0.55 + 0.10 * (item["prose_mentions"] - 1))
                if item["only_corroborated"]:
                    confidence -= 0.10
                value = {
                    "local_ref": ref_of[key], "surface": item["surface"], "entity_type": "unknown",
                    "status": "CANDIDATE", "presence": "unknown", "evidence_class": "PROSE",
                    "evidence": evidence, "alternatives": [],
                    "notes": "prose-only; presence not inferred from mention",
                }
            out.annotations.append(NewAnnotation("reconciled_entity", item["primary"], value,
                                                 confidence=round(confidence, 2)))

        for n, (key, loc) in enumerate(sorted(locations.items(), key=lambda kv: first_offset(kv[1])), 1):
            evidence = sorted(set(loc["evidence"]), key=lambda s: s.char_start)
            corroborated = any(s.char_start != loc["primary"].char_start for s in evidence)
            out.annotations.append(NewAnnotation("reconciled_location", loc["primary"], {
                "local_ref": f"loc_{n:03d}", "surface": loc["surface"], "status": "OBSERVED",
                "evidence_class": "AUTHOR_METADATA", "evidence": evidence, "alternatives": [],
            }, confidence=0.90 if corroborated else 0.80))

        for m, target, alternatives in aliases:
            out.annotations.append(NewAnnotation("alias_candidate", m.span, {
                "surface": m.value["surface"], "candidate_ref": ref_of[target],
                "alternatives": [ref_of[a] for a in alternatives], "scope": "span",
                "status": "ALIAS_CANDIDATE", "evidence": [m.span],
            }, confidence=0.60 if alternatives else 0.75))
        return out

    @staticmethod
    def _link(key: str, entities: "OrderedDict[str, Dict]") -> Tuple[Optional[str], List[str]]:
        participants = [k for k, e in entities.items() if e["kind"] == "participant"]
        if key in participants:
            return key, []
        if " " in key:
            return None, []
        forms = _word_forms(key)
        hits = [p for p in participants if forms & set(p.split())]
        if not hits:
            return None, []
        hits.sort(key=lambda p: (p.split()[0] not in forms, participants.index(p)))
        return hits[0], hits[1:]

    @staticmethod
    def _find_phrase(doc: SourceDocument, regions, phrase: str) -> List[Span]:
        needle = _norm(phrase)
        spans: List[Span] = []
        for r in regions:
            hay = r.span.text.replace("’", "'").lower()
            if len(hay) != len(r.span.text):
                continue
            for m in re.finditer(r"(?<![A-Za-z])" + re.escape(needle) + r"(?![A-Za-z])", hay):
                spans.append(doc.span(r.span.char_start + m.start(), r.span.char_start + m.end()))
        return spans
