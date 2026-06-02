from spatial_pattern_matcher import extract_spatial_facts

def extract_from_vault_md(md_text: str) -> Dict[str, Any]:
    # ... existing markdown parsing ...
    
    # 1. Harvest raw spatial facts
    pattern_facts = extract_spatial_facts(md_text)
    
    # 2. Merge into authority structure
    for rid, rdata in pattern_facts["regions"].items():
        if rid not in authority["regions"]:
            authority["regions"][rid] = rdata
            
    # 3. Append edges to spatial graph
    authority["spatial_graph"]["edges"].extend(pattern_facts["edges"])
    
    return authority
