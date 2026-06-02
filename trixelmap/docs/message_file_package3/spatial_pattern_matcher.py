# Add this function to spatial_pattern_matcher.py (after LOCATION_SUFFIXES)

def extract_location_mentions(text: str) -> List[str]:
    """
    Pass B: Extracts ALL location mentions, regardless of relationships.
    Handles both 'Name Suffix' (e.g., Iron Spire) and Compound (e.g., Ironspire).
    """
    found = []
    
    # 1. Standard Pattern: "Name Suffix" (Space separated)
    standard_pattern = r'(?:the\s+)?\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(' + '|'.join(LOCATION_SUFFIXES) + r')\b'
    for m in re.finditer(standard_pattern, text, re.IGNORECASE):
        found.append(normalize_id(m.group(0)))
        
    # 2. Compound Pattern: "NameSuffix" (e.g., Ironspire)
    word_pattern = r'\b([A-Z][a-zA-Z]+)\b'
    for m in re.finditer(word_pattern, text):
        word = m.group(0)
        # Check if word ends with a known suffix
        for suffix in LOCATION_SUFFIXES:
            if word.lower().endswith(suffix.lower()) and len(word) > len(suffix):
                found.append(normalize_id(word))
                break
                
    return list(set(found))
