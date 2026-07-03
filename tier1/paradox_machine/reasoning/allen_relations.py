ALLEN_BASIC_RELATIONS = {
    "BEFORE",
    "AFTER",
    "MEETS",
    "MET_BY",
    "OVERLAPS",
    "OVERLAPPED_BY",
    "STARTS",
    "STARTED_BY",
    "DURING",
    "CONTAINS",
    "FINISHES",
    "FINISHED_BY",
    "EQUALS",
    "SIMULTANEOUS",
}

INVERSE_RELATION = {
    "BEFORE": "AFTER",
    "AFTER": "BEFORE",
    "MEETS": "MET_BY",
    "MET_BY": "MEETS",
    "OVERLAPS": "OVERLAPPED_BY",
    "OVERLAPPED_BY": "OVERLAPS",
    "STARTS": "STARTED_BY",
    "STARTED_BY": "STARTS",
    "DURING": "CONTAINS",
    "CONTAINS": "DURING",
    "FINISHES": "FINISHED_BY",
    "FINISHED_BY": "FINISHES",
    "EQUALS": "EQUALS",
    "SIMULTANEOUS": "SIMULTANEOUS",
}


def normalize_relation(rel_type: str) -> str:
    rel = rel_type.strip().upper().replace("-", "_")
    if rel == "BEGINS":
        return "STARTS"
    if rel == "IDENTITY":
        return "EQUALS"
    return rel


def is_supported_relation(rel_type: str) -> bool:
    return normalize_relation(rel_type) in ALLEN_BASIC_RELATIONS
