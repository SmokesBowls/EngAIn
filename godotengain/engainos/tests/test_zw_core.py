"""Test ZW semantic ontology"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from zw_core import register_concept, lookup_zw, link_zw, query_relations

def test_zw_core():
    print("TEST 1: Register concepts")
    warden = register_concept("warden", labels=["guardian"], tags={"npc"})
    tower = register_concept("tower", labels=["stronghold"], tags={"location"})
    assert warden.id == "warden"
    print("  ✓ Concepts registered")
    
    print("\nTEST 2: Lookup concepts")
    found = lookup_zw("warden")
    assert found == warden
    print("  ✓ Lookup works")
    
    print("\nTEST 3: Link concepts")
    link_zw("warden", "guards_at", "tower")
    relations = query_relations("warden", "guards_at")
    assert "tower" in relations
    print("  ✓ Relations work")
    
    print("\n✅ ZW CORE: ALL TESTS PASS")

if __name__ == "__main__":
    test_zw_core()
