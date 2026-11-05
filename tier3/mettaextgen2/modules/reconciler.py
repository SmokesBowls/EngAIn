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
  4. Anything else is a prose-only CANDIDATE.
  Rejections become REJECTED declarations, unless the same surface was
  accepted elsewhere in the scene.

Presence (v0.2). Author metadata outranks prose; prose evidence is low
confidence and recorded in `notes` with its lines and in `evidence` spans:
  prose-only entity:  absence -> absent; physical -> present; referenced
                      (memory) -> referenced; communication or mention alone
                      -> unknown. Speaking never establishes physical presence.
  contradictions are kept for review as `continuity_flag` annotations, never
  resolved: prose physical vs prose absence (presence stays unknown), and
  metadata vs prose (metadata present vs prose absence; metadata absent or
  referenced vs prose physical). The metadata value is kept.

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


# Grammatical bases are first-class name evidence, like a mid-sentence capital.
GRAMMAR_BASES = {"proper_capital", "speech_tag_speaker", "grammatical_subject", "possessor_of_subject"}


def _word_forms(word: str) -> set:
    w = _norm(word)
    return {w, w + "s", w[:-1] if w.endswith("s") else w}


class Reconciler(Module):
    name = "reconciler"
    version = "0.2.0"
    implementation_kind = "rules"
    requires = frozenset({"entity_mention", "entity_rejection", "presence", "presence_evidence",
                          "metadata_constraint", "region"})
    produces = frozenset({"reconciled_entity", "reconciled_location", "alias_candidate", "continuity_flag"})

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
        linked: Dict[str, str] = {k: k for k in entities}   # normalised prose surface -> entity key
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
            linked[key] = target
            ent["evidence"].append(m.span)
            ent["prose_mentions"] += 1
            basis = m.value["basis"] + (f" (chapter line {m.value['context_line']})" if m.value.get("context_line") else "")
            if basis not in ent.setdefault("bases", []):
                ent["bases"].append(basis)
            if m.value["basis"] in GRAMMAR_BASES:
                ent["only_corroborated"] = False

        prose_presence: Dict[str, List[Annotation]] = {}
        for ev in view.by_kind("presence_evidence"):
            target = linked.get(_norm(ev.value["surface"]))
            if target is not None:
                prose_presence.setdefault(target, []).append(ev)

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

        flags: List[Tuple[str, Span, str, List[Span]]] = []
        for key, item in ordered:
            prose_ev = prose_presence.get(key, [])
            kinds = {e.value["kind"] for e in prose_ev}
            item["evidence"] += [e.span for e in prose_ev]
            prose_note = "; ".join(sorted({f"{e.value['kind']} L{e.span.line} ({e.value['cue']})" for e in prose_ev}))
            prose_note = f"; prose presence evidence (low confidence): {prose_note}" if prose_note else ""
            spans_of = lambda *ks: [e.span for e in prose_ev if e.value["kind"] in ks]  # noqa: E731
            if {"physical", "absence"} <= kinds:
                flags.append((key, item["primary"], "prose presence evidence conflicts: physical vs absence",
                              spans_of("physical", "absence")))
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
                meta = item["presence"]
                if (meta == "present" and "absence" in kinds) or (meta in ("absent", "referenced") and "physical" in kinds):
                    flags.append((key, item["primary"],
                                  f"presence: author metadata '{meta}' vs prose {sorted(kinds & {'absence', 'physical'})}",
                                  [item["primary"]] + spans_of("absence", "physical")))
                value = {
                    "local_ref": ref_of[key], "surface": item["surface"],
                    "entity_type": "group" if item["number_headed"] else "character",
                    "status": "OBSERVED", "presence": item["presence"], "evidence_class": "AUTHOR_METADATA",
                    "evidence": evidence, "alternatives": [],
                    "notes": (f"author qualifier: {item['qualifier']}" if item["qualifier"] else
                              "author participant, no qualifier") + prose_note,
                }
                confidence = 0.95 if item["prose_mentions"] else 0.90
            else:
                confidence = min(0.85, 0.55 + 0.10 * (item["prose_mentions"] - 1))
                if item["only_corroborated"]:
                    confidence -= 0.10
                if {"physical", "absence"} <= kinds:
                    presence = "unknown"
                elif "absence" in kinds:
                    presence = "absent"
                elif "physical" in kinds:
                    presence = "present"
                elif "referenced" in kinds and "communication" not in kinds:
                    presence = "referenced"
                else:
                    presence = "unknown"
                value = {
                    "local_ref": ref_of[key], "surface": item["surface"], "entity_type": "unknown",
                    "status": "CANDIDATE", "presence": presence, "evidence_class": "PROSE",
                    "evidence": evidence, "alternatives": [],
                    "notes": "prose-only; basis: " + ", ".join(item.get("bases", [])) + (
                        prose_note or "; presence not inferred from mention"),
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

        for key, primary, issue, spans in flags:
            out.annotations.append(NewAnnotation("continuity_flag", primary, {
                "subject_ref": ref_of[key], "issue": issue,
                "source_spans": sorted(set(spans), key=lambda s: s.char_start),
            }))

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
