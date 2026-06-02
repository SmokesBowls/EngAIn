# 1. Update import
from spatial_pattern_matcher import extract_spatial_facts, normalize_id, extract_location_mentions

# 2. Update LocationRecord dataclass (add files_mentioned)
@dataclass
class LocationRecord:
    canonical_id: str
    aliases: List[str] = field(default_factory=list)
    evidence: List[SpatialEvidence] = field(default_factory=list)
    files_mentioned: List[str] = field(default_factory=list) # NEW
    terrain_hints: List[str] = field(default_factory=list)
    placement_status: str = "draft"
    authority_tier: int = 1
    confidence: float = 0.0
    conflicts: List[str] = field(default_factory=list)
