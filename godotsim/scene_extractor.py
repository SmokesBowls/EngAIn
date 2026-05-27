#!/usr/bin/env python3
"""
scene_extractor.py — The Spell
================================
Extracts interactive entity cards from narrative segments.

Two layers:
  - EXTRACTED: derived from story text (read-only reference)
  - OVERRIDE:  editable game design layer (takes priority)

Usage:
    from scene_extractor import SceneExtractor
    ext = SceneExtractor()
    cards = ext.extract(scene_doc)
    # cards["torhh"] = { type, role, mood, knowledge, dialogue, segments, ... }

The story is law. The override is freedom.
If override is null, extracted speaks. If override exists, it rules.
Delete the override, and the story comes back.
"""

import re
import os
import json
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

# ── Stop words: capitalized words that aren't entities ──────────────
STOP_WORDS = {
    "The", "They", "Their", "Them", "This", "That", "These", "Those",
    "But", "And", "Not", "When", "Where", "What", "Which", "Who",
    "How", "Why", "Then", "Than", "From", "Into", "With", "Without",
    "Each", "Every", "Some", "Many", "Most", "More", "Other", "Another",
    "Its", "His", "Her", "She", "He", "It", "Our", "All", "Both",
    "Here", "There", "Now", "Still", "Yet", "Just", "Even", "Only",
    "Perhaps", "Maybe", "Also", "Already", "Never", "Ever", "Once",
    "Between", "Through", "After", "Before", "During", "Until",
    "Above", "Below", "Under", "Over", "Across", "Along", "Around",
    "Day", "Night", "Year", "Month", "Part", "Chapter", "Section",
    "Something", "Nothing", "Everything", "Anything", "Someone",
    "No", "Yes", "Like", "Because", "Since", "Although", "Though",
    "If", "So", "Very", "Too", "Quite", "Rather", "Enough",
    "First", "Second", "Third", "Last", "Next",
    "Could", "Would", "Should", "Might",
    "For", "Nor", "Or", "As",
}

# ── Mood keywords ───────────────────────────────────────────────────
MOOD_PATTERNS = {
    "curious":     r"\bcurio(?:us|sity)\b",
    "fearful":     r"\bfear(?:ful|ed|ing)?\b|\bafraid\b|\bterrif",
    "hostile":     r"\bhostil(?:e|ity)\b|\baggress|\battack|\bthreat",
    "defensive":   r"\bdefensi|\bguard(?:ed|ing)\b|\bprotect",
    "calm":        r"\bcalm(?:ly|ness)?\b|\bseren|\bpeace",
    "determined":  r"\bdetermin|\bresol(?:ute|ved)\b|\bfirm(?:ly)?\b",
    "wary":        r"\bwar(?:y|ily|iness)\b|\bcautio(?:us|n)\b",
    "awed":        r"\bawe(?:d|some|struck)?\b|\bwonder(?:ment)?\b",
    "grief":       r"\bgrief\b|\bgriev|\bmourning?\b|\bsorrow",
    "hopeful":     r"\bhope(?:ful)?\b|\boptimis",
    "desperate":   r"\bdesper(?:ate|ation)\b",
    "commanding":  r"\bcommand(?:ed|ing)?\b|\bordered\b|\bauthorit",
}

# ── Entity type hints ───────────────────────────────────────────────
TYPE_HINTS = {
    "giant":    r"\bgiant(?:s)?\b",
    "neferati": r"\bneferati\b",
    "dragon":   r"\bdragon(?:s)?\b",
    "sage":     r"\bsage(?:s)?\b",
    "keeper":   r"\bkeeper(?:s)?\b|\baeon\s*keeper",
    "nephilim": r"\bnephilim\b",
    "human":    r"\bhuman(?:s)?\b",
    "reptilian": r"\breptili(?:an|ans)\b|\bgruulith\b|\bdregan\b",
}

# ── Role hints ──────────────────────────────────────────────────────
ROLE_HINTS = {
    "leader":   r"\bleader\b|\bcommander\b|\brunning\b|\bin\s+charge\b",
    "ally":     r"\bally\b|\balliance\b|\bfriend\b|\btrust",
    "enemy":    r"\benemy\b|\bfoe\b|\bhostile\b|\battack",
    "observer": r"\bwatch(?:ed|ing|er)\b|\bobserv",
    "protector": r"\bprotect(?:or|ed|ing)?\b|\bguard(?:ian)?\b",
    "teacher":  r"\bteach(?:er|es|ing)?\b|\binstruct|\blesson\b",
    "healer":   r"\bheal(?:er|ing|ed)?\b",
    "scout":    r"\bscout(?:ed|ing)?\b|\breconnaissance\b",
}


class EntityCard:
    """A character/entity extracted from narrative with override support."""

    def __init__(self, name: str):
        self.name = name
        self.name_lower = name.lower()

        # ── Extracted layer (from narrative — read-only reference) ──
        self.extracted = {
            "type": None,         # giant, neferati, dragon, etc.
            "role": None,         # leader, ally, observer, etc.
            "moods": [],          # [mood, ...] detected across segments
            "knowledge": [],      # what they know about / are associated with
            "dialogue": [],       # [{line, context, segment_idx}, ...]
            "descriptions": [],   # narrative descriptions of this entity
            "segment_refs": [],   # which segments mention them
            "first_mention": None,
            "mention_count": 0,
        }

        # ── Override layer (game design — editable, takes priority) ──
        self.override = {
            "type": None,
            "role": None,
            "mood": None,
            "dialogue": [],       # [{line, context}, ...] — designer-authored
            "description": None,  # custom examine text
            "flags": {},          # arbitrary game state flags
        }

    def get(self, field: str, default=None):
        """Get field: override wins, then extracted, then default."""
        ov = self.override.get(field)
        if ov is not None:
            return ov
        ex = self.extracted.get(field)
        if ex is not None:
            return ex
        return default

    def get_mood(self) -> str:
        """Primary mood: override > most common extracted > 'neutral'."""
        if self.override.get("mood"):
            return self.override["mood"]
        if self.extracted["moods"]:
            # Most frequently detected mood
            from collections import Counter
            c = Counter(self.extracted["moods"])
            return c.most_common(1)[0][0]
        return "neutral"

    def get_description(self) -> str:
        """For 'examine' command: override > extracted descriptions."""
        if self.override.get("description"):
            return self.override["description"]
        if self.extracted["descriptions"]:
            return " ".join(self.extracted["descriptions"][:3])
        return f"{self.name} is here."

    def get_dialogue(self) -> List[Dict]:
        """For 'talk to' command: override dialogue + extracted dialogue."""
        result = []
        if self.override.get("dialogue"):
            result.extend(self.override["dialogue"])
        if self.extracted.get("dialogue"):
            result.extend(self.extracted["dialogue"])
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.get("type", "unknown"),
            "role": self.get("role", "unknown"),
            "mood": self.get_mood(),
            "mention_count": self.extracted["mention_count"],
            "first_mention": self.extracted["first_mention"],
            "knowledge": self.extracted["knowledge"],
            "dialogue_count": len(self.get_dialogue()),
            "has_override": any(v for v in self.override.values() if v),
        }


class SceneExtractor:
    """
    Extracts entity cards from a ZONJ scene's segments.

    The story is law. The override is freedom.
    """

    def __init__(self, override_dir: Optional[str] = None):
        """
        Args:
            override_dir: directory for override JSON files.
                          If None, uses ~/.engain/overrides/
        """
        self.override_dir = override_dir or os.path.expanduser(
            "~/.engain/overrides"
        )
        os.makedirs(self.override_dir, exist_ok=True)

    def extract(self, scene: Dict[str, Any]) -> Dict[str, EntityCard]:
        """
        Extract entity cards from a scene document.

        Args:
            scene: ZONJ scene dict with segments, entities, etc.

        Returns:
            dict of entity_name_lower → EntityCard
        """
        segments = scene.get("=segments") or scene.get("segments", [])
        raw_entities = scene.get("@entities") or scene.get("entities", [])
        scene_id = scene.get("@id") or scene.get("scene_id", "unknown")

        # ── Phase 1: Discover entities ──────────────────────────────
        cards: Dict[str, EntityCard] = {}

        # Seed from scene's entity list
        for ent in raw_entities:
            name = ent if isinstance(ent, str) else str(ent)
            if name in STOP_WORDS or len(name) < 3:
                continue
            key = name.lower()
            if key not in cards:
                cards[key] = EntityCard(name)

        # Also discover from segment text (catch names the heuristic missed)
        all_text = self._collect_text(segments)
        discovered = self._discover_entities(all_text)
        for name in discovered:
            key = name.lower()
            if key not in cards:
                cards[key] = EntityCard(name)

        # ── Phase 2: Analyze each segment ───────────────────────────
        for idx, seg in enumerate(segments):
            text = self._seg_text(seg)
            if not text:
                continue

            text_lower = text.lower()

            for key, card in cards.items():
                if card.name_lower not in text_lower and card.name not in text:
                    continue

                # Track mentions
                card.extracted["mention_count"] += 1
                card.extracted["segment_refs"].append(idx)
                if card.extracted["first_mention"] is None:
                    card.extracted["first_mention"] = idx

                # ── Type detection ──
                if not card.extracted["type"]:
                    card.extracted["type"] = self._detect_type(
                        card.name, text, all_text
                    )

                # ── Role detection ──
                if not card.extracted["role"]:
                    card.extracted["role"] = self._detect_role(
                        card.name, text
                    )

                # ── Mood detection ──
                # Check 2-sentence window around entity mention
                mood = self._detect_mood(card.name, text)
                if mood:
                    card.extracted["moods"].append(mood)

                # ── Dialogue extraction ──
                dialogue = self._extract_dialogue(card.name, text, idx)
                if dialogue:
                    card.extracted["dialogue"].extend(dialogue)

                # ── Description extraction ──
                desc = self._extract_description(card.name, text)
                if desc:
                    card.extracted["descriptions"].append(desc)

                # ── Knowledge extraction ──
                knowledge = self._extract_knowledge(card.name, text)
                for k in knowledge:
                    if k not in card.extracted["knowledge"]:
                        card.extracted["knowledge"].append(k)

        # ── Phase 3: Load overrides ─────────────────────────────────
        self._load_overrides(scene_id, cards)

        # Filter out low-signal entities (mentioned only once, no dialogue)
        result = {}
        for key, card in cards.items():
            if (card.extracted["mention_count"] >= 2 or
                    card.extracted["dialogue"] or
                    any(v for v in card.override.values() if v)):
                result[key] = card

        return result

    # ── Text helpers ────────────────────────────────────────────────

    def _seg_text(self, seg) -> str:
        if isinstance(seg, str):
            return seg
        if isinstance(seg, dict):
            return (seg.get("text") or seg.get("narration") or
                    seg.get("dialogue") or "")
        return ""

    def _collect_text(self, segments: List) -> str:
        return "\n".join(self._seg_text(s) for s in segments)

    # ── Entity discovery ────────────────────────────────────────────

    def _discover_entities(self, text: str) -> List[str]:
        """Find capitalized multi-occurrence names not in stop list."""
        words = re.findall(r'\b([A-Z][a-z]{2,})\b', text)
        counts = defaultdict(int)
        for w in words:
            if w not in STOP_WORDS:
                counts[w] += 1
        return [
            w for w, c in counts.items()
            if (
                c >= 3
                and len(w) >= 4
                and w.lower() not in {
                    "she", "they", "them", "through", "earth",
                    "life", "physical", "yes", "one"
                }
            )
        ]

    # ── Type detection ──────────────────────────────────────────────

    def _detect_type(self, name: str, context: str, all_text: str) -> Optional[str]:
        name_lower = name.lower()
        # Direct type patterns: "X the Giant", "X, a Neferati"
        for type_name, pattern in TYPE_HINTS.items():
            # Check if type word appears near entity name
            nearby = self._get_context(name, all_text, window=200)
            if re.search(pattern, nearby, re.IGNORECASE):
                return type_name
        return None

    def _get_context(self, name: str, text: str, window: int = 150) -> str:
        idx = text.lower().find(name.lower())
        if idx < 0:
            return ""
        start = max(0, idx - window)
        end = min(len(text), idx + len(name) + window)
        return text[start:end]

    # ── Role detection ──────────────────────────────────────────────

    def _detect_role(self, name: str, text: str) -> Optional[str]:
        name_lower = name.lower()
        # Look for role patterns near the entity name
        context = self._get_context(name, text, 100)
        for role, pattern in ROLE_HINTS.items():
            if re.search(pattern, context, re.IGNORECASE):
                return role
        return None

    # ── Mood detection ──────────────────────────────────────────────

    def _detect_mood(self, name: str, text: str) -> Optional[str]:
        context = self._get_context(name, text, 120)
        for mood, pattern in MOOD_PATTERNS.items():
            if re.search(pattern, context, re.IGNORECASE):
                return mood
        return None

    # ── Dialogue extraction ─────────────────────────────────────────

    def _extract_dialogue(
        self, name: str, text: str, seg_idx: int
    ) -> List[Dict]:
        """Extract dialogue lines attributed to this entity."""
        results = []
        name_lower = name.lower()

        # Pattern 1: "Speaker said, 'words'" / "Speaker: words"
        patterns = [
            # "Name said/spoke/replied, "..."
            rf'{name}\s+(?:said|spoke|replied|whispered|murmured|stated|announced|offered|countered|asked|demanded|continued)\s*[,:]?\s*["\u201c](.+?)["\u201d]',
            # Direct quotes following name mention in same sentence
            rf'{name}[^.]*?["\u201c](.+?)["\u201d]',
        ]

        for pat in patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                line = match.group(1).strip()
                if len(line) > 5:
                    results.append({
                        "line": line,
                        "segment_idx": seg_idx,
                        "source": "extracted",
                    })

        # Pattern 2: Standalone quoted text where previous context names speaker
        # (handled at segment level by looking at adjacent segments)

        return results

    # ── Description extraction ──────────────────────────────────────

    def _extract_description(self, name: str, text: str) -> Optional[str]:
        """Extract physical/behavioral descriptions of entity."""
        name_lower = name.lower()

        # Patterns for descriptive passages
        desc_patterns = [
            # "whose stone-flesh carried..." / "whose eyes..."
            rf'{name}[^.]*?whose\s+(.{{15,120}})',
            # "the jade-green Giant" / "the burnt-red one"
            rf'(?:the\s+[\w-]+\s+){name}',
            # "X was/stood/sat..." (descriptive action)
            rf'{name}\s+(?:was|stood|sat|knelt|emerged|appeared)[^.]+',
        ]

        for pat in desc_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                desc = m.group(0).strip()
                if len(desc) > 20:
                    return desc[:250]

        return None

    # ── Knowledge extraction ────────────────────────────────────────

    def _extract_knowledge(self, name: str, text: str) -> List[str]:
        """What is this entity associated with / knowledgeable about?"""
        knowledge = []
        context = self._get_context(name, text, 200).lower()

        # Topic patterns
        topics = {
            "water_patterns": r"water.?pattern|water.?shap",
            "vrill_energy": r"vrill|vrill.?energy|vrill.?resonance",
            "prime_connection": r"prime.?connection|consciousness.?link",
            "construction": r"build|construct|pyramid|structure|architect",
            "combat": r"fight|attack|weapon|defense|battle|warrior",
            "healing": r"heal|mend|restore|cure",
            "stone_shaping": r"stone.?flesh|stone.?shap|rock.?form",
            "communication": r"communicat|language|speak|signal",
            "observation": r"observ|watch|analyz|stud(?:y|ied)",
            "leadership": r"lead(?:er|ing)?|command|organiz|direct",
            "navigation": r"navig|scout|explor|path.?find",
            "ritual": r"ritual|ceremony|sacred|rite",
            "telepathy": r"telepat|mind.?link|consciousness.?touch",
        }

        for topic, pattern in topics.items():
            if re.search(pattern, context):
                knowledge.append(topic)

        return knowledge

    # ── Override system ─────────────────────────────────────────────

    def _override_path(self, scene_id: str) -> str:
        safe_id = re.sub(r'[^\w.-]', '_', scene_id)
        return os.path.join(self.override_dir, f"{safe_id}.overrides.json")

    def _load_overrides(
        self, scene_id: str, cards: Dict[str, EntityCard]
    ):
        """Load override file if it exists."""
        path = self._override_path(scene_id)
        if not os.path.exists(path):
            return

        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return

        for key, ov in data.items():
            key_lower = key.lower()
            if key_lower in cards:
                card = cards[key_lower]
                for field in ("type", "role", "mood", "dialogue",
                              "description", "flags"):
                    if field in ov and ov[field] is not None:
                        card.override[field] = ov[field]

    def save_overrides(
        self, scene_id: str, cards: Dict[str, EntityCard]
    ):
        """Save override layer to disk."""
        path = self._override_path(scene_id)
        data = {}
        for key, card in cards.items():
            # Only save cards that have overrides
            if any(v for v in card.override.values() if v):
                data[key] = card.override

        if data:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    def save_override_template(
        self, scene_id: str, cards: Dict[str, EntityCard]
    ):
        """
        Save a template override file showing all entities with null slots.
        Designers fill in what they want to override.
        """
        path = self._override_path(scene_id).replace(
            ".overrides.json", ".template.json"
        )
        data = {}
        for key, card in cards.items():
            data[key] = {
                "type": card.extracted["type"],
                "role": card.extracted["role"],
                "mood": card.get_mood(),
                "dialogue": [
                    {"line": None, "context": f"default greeting from {card.name}"},
                    {"line": None, "context": f"when asked about their role"},
                ],
                "description": None,
                "flags": {},
                "_extracted_ref": {
                    "mention_count": card.extracted["mention_count"],
                    "knowledge": card.extracted["knowledge"],
                    "existing_dialogue": len(card.extracted["dialogue"]),
                },
            }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return path


# ── Standalone test ─────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 scene_extractor.py <scene.zonj.json>")
        print("       python3 scene_extractor.py --test")
        sys.exit(1)

    if sys.argv[1] == "--test":
        # Quick self-test with inline data
        test_scene = {
            "@id": "test_convergence",
            "@entities": ["Senareth", "Torhh", "Vairis", "Elyraen", "Korrhan"],
            "=segments": [
                "Chapter 4: The Convergence",
                "The first tremor came on day nine. Senareth felt it through the soles of their feet.",
                "Torhh had frozen mid-motion, those deep ocean eyes fixed on the interior.",
                "The jade-green Giant released a low rumble that made sand vibrate.",
                'Vairis said, "We should establish shelter before nightfall."',
                '"Shelter might seem threatening," Elyraen countered.',
                "Korrhan of the Ash Giants stood at the edge, its burnt-red stone-flesh cracked.",
                "Torhh was curious about the Neferati, watching them shape water patterns.",
                "Senareth had selected three Neferati to approach the tree line at first light.",
                "The plan was simple: demonstrate vulnerability through deliberate exposure.",
            ],
        }

        ext = SceneExtractor(override_dir="/tmp/engain_test_overrides")
        cards = ext.extract(test_scene)

        print("=== ENTITY CARDS ===\n")
        for key, card in sorted(cards.items()):
            c = card.to_dict()
            print(f"  [{c['name']}]")
            print(f"    type: {c['type']}, role: {c['role']}, mood: {c['mood']}")
            print(f"    mentions: {c['mention_count']}, knowledge: {c['knowledge']}")
            print(f"    dialogue: {c['dialogue_count']} lines")
            if card.extracted["descriptions"]:
                print(f"    desc: {card.extracted['descriptions'][0][:80]}...")
            print()

        # Save template
        path = ext.save_override_template("test_convergence", cards)
        print(f"Template saved: {path}")

    else:
        # Load a real ZONJ file
        with open(sys.argv[1], 'r') as f:
            scene = json.load(f)

        ext = SceneExtractor()
        cards = ext.extract(scene)

        print(f"=== {scene.get('@id', scene.get('scene_id', 'unknown'))} ===")
        print(f"Entities extracted: {len(cards)}\n")

        for key, card in sorted(cards.items(), key=lambda x: -x[1].extracted["mention_count"]):
            c = card.to_dict()
            print(f"  [{c['name']}]  ({c['type'] or '?'} / {c['role'] or '?'} / {c['mood']})")
            print(f"    mentions={c['mention_count']}  knowledge={c['knowledge']}")
            if card.extracted["dialogue"]:
                print(f"    dialogue ({len(card.extracted['dialogue'])} lines):")
                for d in card.extracted["dialogue"][:3]:
                    print(f"      \"{d['line'][:70]}\"")
            if card.extracted["descriptions"]:
                print(f"    desc: \"{card.extracted['descriptions'][0][:100]}\"")
            print()
