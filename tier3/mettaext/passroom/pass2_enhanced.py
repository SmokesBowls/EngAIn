#!/usr/bin/env python3
"""
pass2_enhanced.py - Enhanced inference extraction for complex narratives

Handles:
- Rich emotional states
- Multiple characters with traits
- Relationship dynamics
- Contextual actions
- Temporal progression

Compatible with pass3_merge.py output format.
"""

import os
import re
import sys
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Set
from collections import defaultdict

# ============================================================
# SPEECH VERBS (mirrors pass1_explicit — kept independent)
# ============================================================

_SPEECH_VERBS = (
    "said", "asked", "whispered", "murmured", "replied", "shouted",
    "called", "answered", "observed", "confirmed", "added", "reported",
    "noted", "admitted", "agreed", "continued", "began", "interrupted",
    "conceded", "declared", "acknowledged", "responded", "concluded",
    "insisted", "corrected", "explained", "suggested", "proposed",
    "commanded", "instructed", "requested", "urged", "warned", "promised",
    "announced", "stated", "offered", "protested", "objected", "clarified",
    "reminded", "assured", "argued", "breathed", "muttered", "summarized",
    "decided", "finished", "repeated", "cautioned", "countered", "pointed",
    "pressed", "projected", "extended", "realized", "thought",
)
_VERB_ALT = "|".join(re.escape(v) for v in _SPEECH_VERBS)

# "said Mordain," — verb before name
_CONT_VERB_NAME_RE = re.compile(
    r'^(?P<verb>' + _VERB_ALT + r')\s+(?P<speaker>[A-Z][a-zA-Z]{2,})\s*[,\.]',
    re.IGNORECASE,
)
# "Mordain said," — name before verb
_CONT_NAME_VERB_RE = re.compile(
    r'^(?P<speaker>[A-Z][a-zA-Z]{2,})\s+(?P<verb>' + _VERB_ALT + r')\b',
    re.IGNORECASE,
)
# pronoun attribution: "she observed," — needs context to resolve
_CONT_PRONOUN_RE = re.compile(
    r'^(?:she|he|they|it)\s+(?:' + _VERB_ALT + r')\b',
    re.IGNORECASE,
)

# ============================================================
# ENHANCED CONFIG
# ============================================================

# Character name detection patterns
NAME_PATTERN = re.compile(r'\b[A-Z][a-z]{3,}\b')  # Capitalized 4+ letter words

# Emotion detection - expanded
EMOTION_KEYWORDS = {
    # Basic emotions
    "fear": "fear", "afraid": "fear", "terror": "fear", "terrified": "fear",
    "anger": "anger", "angry": "anger", "rage": "anger", "furious": "anger",
    "joy": "joy", "happy": "joy", "delight": "joy", "elated": "joy",
    "sadness": "sadness", "sad": "sadness", "sorrow": "sadness",
    
    # Complex emotions
    "hope": "hope", "hopeful": "hope",
    "gratitude": "gratitude", "grateful": "gratitude", "thankful": "gratitude",
    "wonder": "wonder", "awe": "wonder", "amazement": "wonder",
    "triumph": "triumph", "triumphant": "triumph", "victory": "triumph",
    "relief": "relief", "relieved": "relief",
    "anticipation": "anticipation", "eager": "anticipation", "excited": "anticipation",
    "anxiety": "anxiety", "anxious": "anxiety", "nervous": "anxiety",
    "uncertainty": "uncertainty", "uncertain": "uncertainty", "doubt": "uncertainty",
    "curiosity": "curiosity", "curious": "curiosity",
    "caution": "caution", "cautious": "caution", "wary": "caution",
    "exhaustion": "exhaustion", "exhausted": "exhaustion", "tired": "exhaustion",
    "gentleness": "gentleness", "gentle": "gentleness",
    "patience": "patience", "patient": "patience",
    "vulnerability": "vulnerability", "vulnerable": "vulnerability",
}

# Action keywords - expanded
ACTION_KEYWORDS = {
    # Movement
    "retreated": "retreat", "withdraw": "retreat", "fled": "flee",
    "approached": "approach", "advance": "approach",
    "huddled": "huddle", "gathered": "gather",
    
    # Vrill/magic
    "vrill-manipulation": "vrill_manipulation",
    "vrill-energy": "vrill_energy",
    "manipulating": "manipulation",
    "shaped": "shaping", "shaping": "shaping",
    
    # Communication
    "said": "speak", "asked": "question", "answered": "respond",
    "observed": "observe", "watched": "observe",
    
    # Physical actions
    "knelt": "submission", "kneeling": "submission",
    "attacking": "attack", "attack": "attack",
}

# Character trait indicators
TRAIT_KEYWORDS = {
    "practical": "pragmatic",
    "analytical": "analytical",
    "artistic": "creative",
    "gentle": "compassionate",
    "curious": "inquisitive",
    "patient": "patient",
}

# Relationship indicators
RELATIONSHIP_PATTERNS = {
    "trust": ["trusted", "trust", "trusting"],
    "fear_of": ["afraid of", "feared", "terrified of"],
    "respect": ["respected", "respecting", "admired"],
    "collaborate": ["worked with", "partnered", "together"],
}

# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Segment:
    tag_line_no: int
    text_line_no: int
    type: str
    speaker: Optional[str]
    text: str

@dataclass
class Character:
    """Track character information"""
    name: str
    mentions: int = 0
    traits: Set[str] = None
    relationships: Dict[str, str] = None
    known: Optional[bool] = None
    spawnable: Optional[bool] = None
    classification: str = "unclassified"
    
    def __post_init__(self):
        if self.traits is None:
            self.traits = set()
        if self.relationships is None:
            self.relationships = {}

@dataclass
class SceneObject:
    """Track non-character scene content observations"""
    name: str
    category: str
    normalized_type: Optional[str] = None
    mentions: int = 1


SCENE_OBJECT_PATTERNS: List[Tuple[str, str, str, bool]] = [
    # (pattern_phrase_lower, category, normalized_type, is_proper_noun)
    ("falcon ridge enclave", "settlement", "settlement", True),
    ("falcon ridge", "settlement", "settlement", True),
    ("star needle spire", "landmark", "spire", True),
    ("star needle", "landmark", "spire", True),
    ("irrigated fields", "settlement_feature", "fields", False),
    ("irrigation ditches", "settlement_feature", "ditches", False),
    ("perimeter wall", "boundary", "wall", False),
    ("storage cache", "settlement_feature", "cache", False),
    ("crash site", "location", "location", False),
    ("stone archive building", "structure", "building", False),
    ("solid stone building", "structure", "building", False),
    # Standalone nouns
    ("barracks", "structure", "barracks", False),
    ("archive", "structure", "archive", False),
    ("longhouse", "structure", "longhouse", False),
    ("hut", "structure", "hut", False),
    ("huts", "structure", "hut", False),
    ("wall", "boundary", "wall", False),
    ("walls", "boundary", "wall", False),
    ("gate", "boundary", "gate", False),
    ("gates", "boundary", "gate", False),
    ("field", "settlement_feature", "fields", False),
    ("fields", "settlement_feature", "fields", False),
    ("settlement", "settlement", "settlement", False),
    ("stream", "terrain_feature", "stream", False),
    ("waterfall", "terrain_feature", "waterfall", False),
    ("plateau", "terrain_feature", "plateau", False),
    ("ridge", "terrain_feature", "ridge", False),
    ("valley", "terrain_feature", "valley", False),
]


def extract_scene_objects(segments: List[Segment]) -> Dict[str, SceneObject]:
    """Extract non-character scene-content observations using span-local suppression."""
    objects: Dict[str, SceneObject] = {}

    for seg in segments:
        text = seg.text
        if not text:
            continue

        # Find all pattern candidate matches in this segment text
        matches = []
        for phrase_pattern, cat, norm_type, is_proper in SCENE_OBJECT_PATTERNS:
            for m in re.finditer(rf"\b{re.escape(phrase_pattern)}\b", text, re.IGNORECASE):
                start, end = m.span()
                raw_matched_text = text[start:end]
                matches.append((end - start, start, end, phrase_pattern, cat, norm_type, is_proper, raw_matched_text))

        # Sort matches by span length descending (longest phrases first)
        matches.sort(key=lambda x: -x[0])

        claimed_spans: Set[int] = set()
        for length, start, end, phrase_pattern, cat, norm_type, is_proper, raw_text in matches:
            # Check if any character index in this match is already claimed by a longer phrase in this segment
            span_indices = set(range(start, end))
            if claimed_spans.intersection(span_indices):
                continue  # Span overlap -> suppress sub-word fragment in this span

            claimed_spans.update(span_indices)

            # Determine display name
            display_name = raw_text if is_proper else phrase_pattern
            if not is_proper:
                # Standardize plural to singular for single-word non-proper nouns where applicable
                if display_name == "huts":
                    display_name = "hut"
                elif display_name == "walls":
                    display_name = "wall"
                elif display_name == "gates":
                    display_name = "gate"

            if display_name not in objects:
                objects[display_name] = SceneObject(
                    name=display_name,
                    category=cat,
                    normalized_type=norm_type,
                    mentions=1,
                )
            else:
                objects[display_name].mentions += 1

    return objects

# ============================================================
# CHARACTER EXTRACTION
# ============================================================

def extract_characters(segments: List[Segment]) -> Dict[str, Character]:
    """Extract all character names and build profiles"""
    characters = {}
    name_counts = defaultdict(int)
    
    # First pass: count potential names
    for seg in segments:
        text = seg.text
        if not text:
            continue
        
        # Find capitalized words that might be names
        for match in NAME_PATTERN.finditer(text):
            word = match.group()
            # Filter out common words
            if word not in {"The", "They", "Then", "There", "This", "That", "Their", 
                           "When", "Where", "What", "Which", "Each", "Some", "Many"}:
                name_counts[word] += 1
    
    # Second pass: names that appear 3+ times are probably characters
    for name, count in name_counts.items():
        if count >= 3:
            characters[name] = Character(name=name, mentions=count)
    
    # Add explicit speakers
    for seg in segments:
        if seg.speaker and seg.speaker != "unknown":
            if seg.speaker not in characters:
                characters[seg.speaker] = Character(name=seg.speaker)
            characters[seg.speaker].mentions += 1
    
    return characters

def extract_character_traits(segments: List[Segment], 
                            characters: Dict[str, Character]) -> None:
    """Extract character traits from descriptions"""
    for seg in segments:
        text = seg.text.lower()
        
        for name, char in characters.items():
            if name.lower() in text:
                # Look for trait keywords near the name
                for trait_word, trait_label in TRAIT_KEYWORDS.items():
                    if trait_word in text:
                        char.traits.add(trait_label)

# ============================================================
# ENHANCED SPEAKER INFERENCE
# ============================================================

def infer_speakers_enhanced(segments: List[Segment],
                           characters: Dict[str, Character]) -> List[Tuple[int, str, float]]:
    """Enhanced speaker inference using character knowledge and forward-look attribution."""
    atoms = []
    blocked_speakers = {"unknown", "he", "she", "they", "him", "her", "them", "his", "their", "it"}

    for idx, seg in enumerate(segments):
        if seg.type != "dialogue":
            continue

        if seg.speaker and seg.speaker.lower() not in blocked_speakers:
            if seg.speaker in characters:
                atoms.append((seg.text_line_no, seg.speaker, 0.95))
            continue

        # Unknown or pronoun speaker — try to resolve to a character name
        if not seg.speaker or seg.speaker.lower() in blocked_speakers:
            speaker = None
            # Look at the immediately following non-blank segment
            for j in range(idx + 1, min(idx + 3, len(segments))):
                next_seg = segments[j]
                if next_seg.type == "blank":
                    break
                if next_seg.type != "narration":
                    break
                text = next_seg.text.strip()

                cm = _CONT_VERB_NAME_RE.match(text)
                if cm and cm.group("speaker") in characters:
                    speaker = cm.group("speaker")
                    break

                cm = _CONT_NAME_VERB_RE.match(text)
                if cm and cm.group("speaker") in characters:
                    speaker = cm.group("speaker")
                    break

                # Pronoun continuation — resolve from nearest prior character
                if _CONT_PRONOUN_RE.match(text):
                    speaker = _find_nearest_character_backward(segments, idx, characters)
                    break

                break  # only check immediately adjacent segment

            if speaker:
                atoms.append((seg.text_line_no, speaker, 0.80))

    return atoms

# ============================================================
# ENHANCED EMOTION INFERENCE
# ============================================================

def infer_emotions_enhanced(segments: List[Segment],
                           characters: Dict[str, Character]) -> List[Tuple[int, str, str, float]]:
    """Enhanced emotion detection with context awareness"""
    atoms = []
    
    for idx, seg in enumerate(segments):
        text = seg.text
        if not text:
            continue
        
        lower = text.lower()
        
        # PATTERN 1: Single-word emotion lists ("Wonder. Triumph. Relief. Hope.")
        # Look for short sentences that are just emotion words
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        for sent in sentences:
            words = sent.strip().split()
            if len(words) == 1 and words[0].lower() in EMOTION_KEYWORDS:
                # This is a standalone emotion word
                emotion = EMOTION_KEYWORDS[words[0].lower()]
                
                # Find subject by looking backward
                subject = _find_nearest_character_backward(segments, idx, characters)
                if subject:
                    atoms.append((seg.text_line_no, subject, emotion, 1.0))
        
        # PATTERN 2: Contextual emotions ("felt overwhelming fear")
        for emo_word, canonical in EMOTION_KEYWORDS.items():
            if re.search(rf'\b{re.escape(emo_word)}\b', lower):
                # Find subject in current or nearby lines
                subject = None
                
                # Check current line for character names
                for char_name in characters.keys():
                    if char_name.lower() in lower:
                        subject = char_name
                        break
                
                # If not found, look backward
                if not subject:
                    subject = _find_nearest_character_backward(segments, idx, characters)
                
                if subject:
                    # Check for intensity modifiers
                    confidence = 0.9
                    if any(word in lower for word in ["overwhelming", "intense", "deep", "profound"]):
                        confidence = 1.0
                    
                    atoms.append((seg.text_line_no, subject, canonical, confidence))
        
        # PATTERN 3: Thoughts containing emotions
        if seg.type == "internal_monologue":
            for emo_word, canonical in EMOTION_KEYWORDS.items():
                if emo_word in lower:
                    subject = seg.speaker if seg.speaker != "unknown" else \
                             _find_nearest_character_backward(segments, idx, characters)
                    if subject:
                        atoms.append((seg.text_line_no, subject, canonical, 0.95))
    
    # Deduplicate
    return _deduplicate_emotions(atoms)

def _find_nearest_character_backward(segments: List[Segment], 
                                    idx: int,
                                    characters: Dict[str, Character],
                                    max_distance: int = 5) -> Optional[str]:
    """Find nearest character mention looking backward"""
    for j in range(idx, max(0, idx - max_distance), -1):
        text = segments[j].text
        if not text:
            continue
        
        # Check for character names
        for char_name in characters.keys():
            if char_name in text:
                return char_name
        
        # Check for explicit speaker
        if segments[j].speaker and segments[j].speaker != "unknown":
            return segments[j].speaker
    
    return None

def _deduplicate_emotions(atoms: List[Tuple[int, str, str, float]]) \
        -> List[Tuple[int, str, str, float]]:
    """Deduplicate emotions keeping highest confidence"""
    dedup = {}
    for line, subj, emo, conf in atoms:
        key = (line, subj, emo)
        if key not in dedup or conf > dedup[key]:
            dedup[key] = conf
    
    result = []
    for (line, subj, emo), conf in sorted(dedup.items()):
        result.append((line, subj, emo, conf))
    return result

# ============================================================
# ENHANCED ACTION INFERENCE
# ============================================================

def infer_actions_enhanced(segments: List[Segment]) -> List[Tuple[int, str, float]]:
    """Enhanced action detection"""
    atoms = []
    seen = set()
    
    for seg in segments:
        text = seg.text
        if not text:
            continue
        
        lower = text.lower()
        
        for phrase, canonical in ACTION_KEYWORDS.items():
            if phrase in lower:
                key = (seg.text_line_no, canonical)
                if key in seen:
                    continue
                seen.add(key)
                
                # Higher confidence for explicit action descriptions
                confidence = 0.95 if len(phrase.split()) > 1 else 0.9
                atoms.append((seg.text_line_no, canonical, confidence))
    
    return atoms

# ============================================================
# THOUGHT INFERENCE
# ============================================================

def infer_thoughts_enhanced(segments: List[Segment],
                           characters: Dict[str, Character]) -> List[Tuple[int, str, float]]:
    """Enhanced thought detection"""
    atoms = []
    
    for idx, seg in enumerate(segments):
        # Internal monologue type
        if seg.type == "internal_monologue":
            thinker = seg.speaker if seg.speaker != "unknown" else \
                     _find_nearest_character_backward(segments, idx, characters)
            
            confidence = 1.0 if seg.speaker != "unknown" else 0.9
            if thinker:
                atoms.append((seg.text_line_no, thinker, confidence))
        
        # Asterisk thoughts
        if '*' in seg.text:
            # Extract text between asterisks
            thought_matches = re.findall(r'\*([^*]+)\*', seg.text)
            if thought_matches:
                thinker = _find_nearest_character_backward(segments, idx, characters)
                if thinker:
                    atoms.append((seg.text_line_no, thinker, 0.95))
    
    # Deduplicate
    return _deduplicate_thoughts(atoms)

def _deduplicate_thoughts(atoms: List[Tuple[int, str, float]]) \
        -> List[Tuple[int, str, float]]:
    """Deduplicate thoughts keeping highest confidence"""
    dedup = {}
    for line, who, conf in atoms:
        key = (line, who)
        if key not in dedup or conf > dedup[key]:
            dedup[key] = conf
    
    result = []
    for (line, who), conf in sorted(dedup.items()):
        result.append((line, who, conf))
    return result

# ============================================================
# RELATIONSHIP INFERENCE (NEW)
# ============================================================

def infer_relationships(segments: List[Segment],
                       characters: Dict[str, Character]) -> List[Tuple[str, str, str, float]]:
    """Infer relationships between characters"""
    relationships = []
    
    for seg in segments:
        text = seg.text.lower()
        
        # Find pairs of characters mentioned together
        mentioned_chars = [name for name in characters.keys() 
                          if name.lower() in text]
        
        if len(mentioned_chars) >= 2:
            # Look for relationship indicators
            for rel_type, patterns in RELATIONSHIP_PATTERNS.items():
                for pattern in patterns:
                    if pattern in text:
                        # Relationship between first two mentioned characters
                        relationships.append((
                            mentioned_chars[0],
                            mentioned_chars[1],
                            rel_type,
                            0.7  # Medium confidence for inferred relationships
                        ))
    
    return relationships

# ============================================================
# LOADING PASS1 SEGMENTS
# ============================================================

TYPE_RE = re.compile(
    r'^\{type:(?P<type>[a-z_]+)'
    r'(?:,\s*speaker:(?P<speaker>[A-Za-z_]+))?'
    r'\}\s*(?P<text>.*)$'
)

def load_segments(path: str) -> List[Segment]:
    """Load Pass1 output file"""
    segments = []
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]

    for idx, line in enumerate(lines, start=1):
        m = TYPE_RE.match(line.strip())
        if not m:
            continue
        seg_type = m.group("type")
        speaker = m.group("speaker")
        text = m.group("text") or ""
        segments.append(
            Segment(
                tag_line_no=idx,
                text_line_no=idx,
                type=seg_type,
                speaker=speaker,
                text=text,
            )
        )
    return segments

# ============================================================
# METTA OUTPUT
# ============================================================

def write_metta(
    path: str,
    speakers: List[Tuple[int, str, float]],
    emotions: List[Tuple[int, str, str, float]],
    actions: List[Tuple[int, str, float]],
    thoughts: List[Tuple[int, str, float]],
    characters: Dict[str, Character],
    relationships: List[Tuple[str, str, str, float]],
    scene_objects: Optional[Dict[str, SceneObject]] = None,
) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("; PASS2 ENHANCED INFERENCES\n")
        f.write("; Enhanced extraction for complex narratives\n\n")

        # Characters / Entities discovered
        f.write("; ---- Entity Candidates ----\n")
        for name, char in sorted(characters.items()):
            traits_str = ", ".join(char.traits) if char.traits else "none"
            f.write(f"; {name}: {char.mentions} mentions, traits: {traits_str}\n")
            known_str = "true" if char.known else "false"
            spawnable_str = "true" if char.spawnable else "false"
            classification_str = char.classification or "unclassified"
            f.write(
                f"(entity {name} :known {known_str} :spawnable {spawnable_str} "
                f':classification "{classification_str}" :mentions {char.mentions})\n'
            )
        f.write("\n")

        # Scene Objects Discovered
        if scene_objects:
            f.write("; ---- Scene Content Observations ----\n")
            for name, obj in sorted(scene_objects.items()):
                norm_attr = f' :normalized_type "{obj.normalized_type}"' if obj.normalized_type else ""
                f.write(f'(scene_object "{obj.name}" :category "{obj.category}"{norm_attr} :mentions {obj.mentions})\n')
            f.write("\n")

        # Speakers
        f.write("; ---- Speaker Inference ----\n")
        for line, name, conf in speakers:
            f.write(f"(speaker line:{line} {name} :confidence {conf:.2f})\n")
        f.write("\n")

        # Emotions
        f.write("; ---- Emotions ----\n")
        for line, subj, emo, conf in emotions:
            f.write(f"(emotion line:{line} {subj} {emo} :confidence {conf:.2f})\n")
        f.write("\n")

        # Actions
        f.write("; ---- Actions ----\n")
        for line, act, conf in actions:
            f.write(f"(action line:{line} {act} :confidence {conf:.2f})\n")
        f.write("\n")

        # Thoughts
        f.write("; ---- Thoughts ----\n")
        for line, who, conf in thoughts:
            f.write(f"(thought line:{line} {who} :confidence {conf:.2f})\n")
        f.write("\n")

        # Relationships (NEW)
        if relationships:
            f.write("; ---- Relationships ----\n")
            for char1, char2, rel_type, conf in relationships:
                f.write(f"(relationship {char1} {char2} {rel_type} :confidence {conf:.2f})\n")
            f.write("\n")

# ============================================================
# MAIN
# ============================================================

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: pass2_enhanced.py <pass1_output.txt>")
        sys.exit(1)

    infile = sys.argv[1]
    segments = load_segments(infile)

    # Extract characters
    from .pass2_entity_filter import filter_entities
    characters = extract_characters(segments)
    characters = filter_entities(characters)
    extract_character_traits(segments, characters)
    scene_objects = extract_scene_objects(segments)

    # Run enhanced inference
    speakers = infer_speakers_enhanced(segments, characters)
    emotions = infer_emotions_enhanced(segments, characters)
    actions = infer_actions_enhanced(segments)
    thoughts = infer_thoughts_enhanced(segments, characters)
    relationships = infer_relationships(segments, characters)

    base = os.path.basename(infile)
    base_noext = base
    if base_noext.endswith(".txt"):
        base_noext = base_noext[:-4]
    base_noext = base_noext.replace("out_pass1_", "")

    outfile = os.path.join(os.path.dirname(infile), f"out_pass2_{base_noext}.metta")
    write_metta(outfile, speakers, emotions, actions, thoughts, characters, relationships, scene_objects=scene_objects)
    
    print(f"[PASS2 ENHANCED] Analyzed {len(characters)} characters, {len(scene_objects)} scene objects")
    print(f"[PASS2 ENHANCED] Extracted:")
    print(f"  • {len(speakers)} speaker inferences")
    print(f"  • {len(emotions)} emotion inferences")
    print(f"  • {len(actions)} action inferences")
    print(f"  • {len(thoughts)} thought inferences")
    print(f"  • {len(relationships)} relationship inferences")
    print(f"  • {len(scene_objects)} scene content observations")
    print(f"[PASS2 ENHANCED] Wrote → {outfile}")

if __name__ == "__main__":
    main()
