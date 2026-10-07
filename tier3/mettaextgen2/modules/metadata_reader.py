"""metadata_reader (GEN2_MODULES.md §2.3).

Input:   metadata_yaml / metadata_plain regions.
Output:  `metadata_constraint` annotations: assertion / presence_qualifier /
         editorial_placement / unresolved_state / non_inference
         (GEN2_OUTPUT_CONTRACT.md §3 "Metta is structured evidence"). Each one
         spans the exact raw text it came from. Participant entries get one
         presence_qualifier each, spanning that entry.
Allowed: reading author metadata as higher-authority evidence; tolerating both
         yaml layouts (nested `scene meta:` or top-level keys).
Forbidden: turning metadata names into entity declarations (entity_extractor
         decides); resolving anything marked unresolved; dropping unknown keys
         (they become plain assertions).
Failure: unparseable yaml leaves the region unread (warning, no constraints).
Values are read with yaml BaseLoader, so nothing is type-coerced.
"""

from __future__ import annotations

import re
from typing import Iterator, List, Optional, Tuple

import yaml

from ..lib.annotations import AnnotationView, Diagnostic, Module, ModuleOutput, NewAnnotation, SceneInput
from ..lib.source import SourceDocument, Span, SpanError

_NON_INFERENCE = re.compile(
    r"\b(?:no|not|nor|never)\b[^.;]*?\b(?:inferred|established|invented|imported|inserted|proven)\b",
    re.IGNORECASE,
)
_UNRESOLVED = re.compile(
    r"\b(?:unresolved|unknown|unshown|unstaged|indeterminate|unidentified|unclear|unconfirmed)\b",
    re.IGNORECASE,
)
_EDITORIAL_KEYS = {"time", "date qualification", "chronology qualification", "temporal sub-anchor"}
_PARTICIPANT_ENTRY = re.compile(r"^(?P<name>[^()]+?)\s*(?:\((?P<qualifier>[^)]*)\))?\s*$")


def classify(key: str, text: str) -> str:
    """Priority: non_inference > unresolved_state > editorial_placement > assertion."""
    if _NON_INFERENCE.search(text):
        return "non_inference"
    if _UNRESOLVED.search(text):
        return "unresolved_state"
    if key.lower() in _EDITORIAL_KEYS or "editorial" in text.lower():
        return "editorial_placement"
    return "assertion"


def _subject_from_key(key: str) -> Optional[str]:
    m = re.match(r"^(?P<subject>.+?)\s+state$", key, re.IGNORECASE)
    return m.group("subject") if m else None


def split_entries(raw: str, base: int) -> Iterator[Tuple[str, int, int]]:
    """Split a participants value on ';' (or ',' if no ';'), ignoring separators
    inside parentheses. Yields (entry_text, start, end) with absolute offsets,
    trimmed of surrounding whitespace."""
    sep = ";" if ";" in raw else ","
    depth, start = 0, 0
    pieces: List[Tuple[int, int]] = []
    for i, ch in enumerate(raw):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch == sep and depth == 0:
            pieces.append((start, i))
            start = i + 1
    pieces.append((start, len(raw)))
    for s, e in pieces:
        chunk = raw[s:e]
        lead = len(chunk) - len(chunk.lstrip())
        text = chunk.strip()
        if text:
            yield text, base + s + lead, base + s + lead + len(text)


class MetadataReader(Module):
    name = "metadata_reader"
    version = "0.1.0"
    implementation_kind = "rules"
    requires = frozenset({"region"})
    produces = frozenset({"metadata_constraint"})

    def run(self, doc: SourceDocument, scene: SceneInput, view: AnnotationView) -> ModuleOutput:
        out = ModuleOutput()
        for region in view.by_kind("region"):
            rtype = region.value["region_type"]
            if rtype == "metadata_yaml":
                self._read_yaml(doc, region.value, out)
            elif rtype == "metadata_plain":
                self._read_plain(doc, region.value, out)
        return out

    # -- emission ---------------------------------------------------------

    def _emit(self, doc: SourceDocument, out: ModuleOutput, key: str, text: str,
              span: Span, raw_value: str, raw_start: int) -> None:
        leaf = key.split(".")[-1]
        if leaf.strip().lower() == "participants":
            for entry, s, e in split_entries(raw_value, raw_start):
                m = _PARTICIPANT_ENTRY.match(entry)
                name = m.group("name").strip() if m else entry
                qualifier = m.group("qualifier").strip() if m and m.group("qualifier") else None
                out.annotations.append(NewAnnotation("metadata_constraint", doc.span(s, e), {
                    "kind": "presence_qualifier", "key": key, "subject": name,
                    "qualifier": qualifier, "text": entry,
                }))
            return
        if leaf.strip().lower() == "location":
            for segment, s, e in split_location(raw_value, raw_start):
                out.annotations.append(NewAnnotation("metadata_constraint", doc.span(s, e), {
                    "kind": "assertion", "key": key, "subject": segment, "text": segment,
                }))
            return
        out.annotations.append(NewAnnotation("metadata_constraint", span, {
            "kind": classify(leaf, text), "key": key, "subject": _subject_from_key(leaf), "text": text,
        }))

    # -- yaml -------------------------------------------------------------

    def _read_yaml(self, doc: SourceDocument, region: dict, out: ModuleOutput) -> None:
        if not region.get("terminated", False):
            out.diagnostics.append(Diagnostic("warning", f"yaml at line {region['first_line']} unterminated; not read"))
            return
        body_start = doc.line_start(region["first_line"] + 1)
        body_end = doc.line_start(region["last_line"])
        body = doc.text[body_start:body_end]
        try:
            node = yaml.compose(body, Loader=yaml.BaseLoader)
        except yaml.YAMLError as exc:
            out.diagnostics.append(Diagnostic("warning", f"yaml at line {region['first_line']} unparseable: {exc}".replace("\n", " ")))
            return
        if node is None:
            return
        if not isinstance(node, yaml.MappingNode):
            out.diagnostics.append(Diagnostic("warning", f"yaml at line {region['first_line']} is not a mapping"))
            return
        if (len(node.value) == 1 and node.value[0][0].value.strip().lower() == "scene meta"
                and isinstance(node.value[0][1], yaml.MappingNode)):
            node = node.value[0][1]
        self._walk(doc, node, body_start, "", out)

    def _walk(self, doc: SourceDocument, node: yaml.MappingNode, base: int, prefix: str, out: ModuleOutput) -> None:
        for key_node, value_node in node.value:
            key = f"{prefix}{key_node.value}"
            if isinstance(value_node, yaml.MappingNode):
                self._walk(doc, value_node, base, f"{key}.", out)
                continue
            if isinstance(value_node, yaml.SequenceNode):
                items = [v for v in value_node.value if isinstance(v, yaml.ScalarNode)]
                text = "; ".join(v.value for v in items)
            else:
                text = value_node.value
            start = base + value_node.start_mark.index
            end = base + value_node.end_mark.index
            raw = doc.text[start:end]
            end = start + len(raw.rstrip())
            if end <= start or not text.strip():
                continue
            try:
                span = doc.span(start, end)
            except SpanError as exc:
                out.diagnostics.append(Diagnostic("warning", f"metadata key {key!r}: {exc}"))
                continue
            plain = isinstance(value_node, yaml.ScalarNode) and value_node.style is None and raw.strip() == text
            if plain:
                self._emit(doc, out, key, text, span, doc.text[start:end], start)
            else:
                # Quoted / block / sequence values: the span covers the raw block;
                # sub-entry spans are not attempted (offsets would not be exact).
                leaf = key.split(".")[-1].strip().lower()
                if leaf in ("participants", "location"):
                    out.diagnostics.append(Diagnostic("info", f"{key}: non-plain yaml value; entries not split"))
                # A non-plain location value is kept as one unsplit segment.
                subject = text if leaf == "location" else _subject_from_key(key.split(".")[-1])
                out.annotations.append(NewAnnotation("metadata_constraint", span, {
                    "kind": classify(key.split(".")[-1], text), "key": key,
                    "subject": subject, "text": text,
                }))

    # -- plain `scene meta:` blocks ----------------------------------------

    def _read_plain(self, doc: SourceDocument, region: dict, out: ModuleOutput) -> None:
        for line in range(region["first_line"] + 1, region["last_line"] + 1):
            line_text = doc.line_text(line)
            m = re.match(r"^(?P<indent>\s*)(?P<key>[A-Za-z][A-Za-z _]*):\s*(?P<value>.*?)\s*$", line_text)
            if not m or not m.group("value"):
                continue
            start = doc.line_start(line) + m.start("value")
            end = doc.line_start(line) + m.end("value")
            self._emit(doc, out, m.group("key"), m.group("value"), doc.span(start, end), m.group("value"), start)


def split_location(raw: str, base: int) -> Iterator[Tuple[str, int, int]]:
    """'Mika's grave / Falcon Ridge / departure path' -> three segments."""
    pos = 0
    for part in raw.split(" / "):
        lead = len(part) - len(part.lstrip())
        text = part.strip()
        if text:
            yield text, base + pos + lead, base + pos + lead + len(text)
        pos += len(part) + 3
