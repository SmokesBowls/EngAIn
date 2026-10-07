"""scene_segmenter (GEN2_MODULES.md §2.2).

Input:   SourceDocument scene region; inherited SceneInput.
Output:  `region` annotations: scene_header / metadata_yaml / metadata_plain /
         structural_heading / separator / prose. One annotation per prose
         line (paragraph); one per metadata block.
Allowed: classifying source structure; reading the label from the marker.
Forbidden: minting or deriving scene ids; re-segmenting the scene.
Failure: an unterminated yaml fence is classified `metadata_yaml` up to the
         region end, and a warning diagnostic is emitted; its text is never
         treated as prose.
"""

from __future__ import annotations

import re

from ..lib.annotations import AnnotationView, Diagnostic, Module, ModuleOutput, NewAnnotation, SceneInput
from ..lib.source import SourceDocument

_MARKER = re.compile(r"^(?:#{1,6}[ \t]+)?scene\s+(?P<label>\d+\.\d+)\s+[—-]\s+(?P<title>.+)$", re.IGNORECASE)
_YAML_OPEN = re.compile(r"^```ya?ml\s*$", re.IGNORECASE)
_FENCE_CLOSE = re.compile(r"^```\s*$")
_PLAIN_META = re.compile(r"^scene meta:\s*$", re.IGNORECASE)
_META_FIELD = re.compile(r"^[A-Za-z][A-Za-z _]*:\s*.*$")
# Structural headings need a numeral after the keyword, so prose such as
# "Act quickly," or "Book in hand, he..." is never swallowed.
_STRUCTURAL = re.compile(
    r"^(?:#{1,6}[ \t]+.*"
    r"|(?:act|epic|part|book|chapter)[ \t]+(?:\d+|(?-i:[IVXLC]+))\b.*"
    r"|end of chapter\b.*)$",
    re.IGNORECASE,
)
_SEPARATOR = re.compile(r"^(?:-{3,}|\*{3,}|_{3,})$")


class SceneSegmenter(Module):
    name = "scene_segmenter"
    version = "0.1.0"
    implementation_kind = "rules"
    requires = frozenset()
    produces = frozenset({"region"})

    def run(self, doc: SourceDocument, scene: SceneInput, view: AnnotationView) -> ModuleOutput:
        out = ModuleOutput()
        line = doc.region_first_line
        last = doc.region_last_line
        while line <= last:
            text = doc.line_text(line).strip()
            if not text:
                line += 1
                continue
            marker = _MARKER.match(text)
            if marker:
                label = marker.group("label")
                if scene.source_scene_label is not None and label != scene.source_scene_label:
                    out.diagnostics.append(Diagnostic(
                        "warning",
                        f"scene_boundary_mismatch: marker label {label} at line {line} "
                        f"differs from inherited label {scene.source_scene_label}",
                    ))
                out.annotations.append(NewAnnotation("region", doc.line_span(line),
                                                     {"region_type": "scene_header", "label": label}))
                line += 1
                continue
            if _YAML_OPEN.match(text):
                end = line + 1
                while end <= last and not _FENCE_CLOSE.match(doc.line_text(end).strip()):
                    end += 1
                terminated = end <= last
                if not terminated:
                    end = last
                    out.diagnostics.append(Diagnostic("warning", f"unterminated yaml fence at line {line}"))
                out.annotations.append(NewAnnotation(
                    "region", doc.span(doc.line_start(line), doc.line_end(end)),
                    {"region_type": "metadata_yaml", "first_line": line, "last_line": end,
                     "terminated": terminated},
                ))
                line = end + 1
                continue
            if _PLAIN_META.match(text):
                end = line
                while end + 1 <= last and _META_FIELD.match(doc.line_text(end + 1).strip()):
                    end += 1
                out.annotations.append(NewAnnotation(
                    "region", doc.span(doc.line_start(line), doc.line_end(end)),
                    {"region_type": "metadata_plain", "first_line": line, "last_line": end},
                ))
                line = end + 1
                continue
            if _SEPARATOR.match(text):
                region_type = "separator"
            elif _STRUCTURAL.match(text):
                region_type = "structural_heading"
            else:
                region_type = "prose"
            out.annotations.append(NewAnnotation("region", doc.line_span(line), {"region_type": region_type}))
            line += 1
        return out
