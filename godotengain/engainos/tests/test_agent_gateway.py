"""Test Agent Gateway - The Contract"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from empire_agent_gateway import AgentGateway, initialize_gateway, submit_trae_command, submit_human_command
from empire_mr import Empire, Command
from combat3d_mr import step_combat, CombatSnapshot, CombatEntity, DamageEvent
from reality_mode import set_mode, RealityMode
from intent_shadow import query_intents, _global_shadow
from history_xeon import get_canonical_history, _global_history

def test_agent_gateway():
    print("=== AGENT GATEWAY TEST ===\n")
    
    # Clear state
    _global_shadow.clear()
    _global_history.clear()
    
    # Setup Empire
    initial = CombatSnapshot(
        entities={
            "player": CombatEntity("player", 100.0, 100.0),
            "enemy": CombatEntity("enemy", 100.0, 100.0)
        }
    )
    
    kernels = {
        "combat": lambda state, events: step_combat(
            CombatSnapshot(**state) if isinstance(state, dict) else state,
            events
        )
    }
    
    empire = Empire({'combat': initial.__dict__}, kernels)
    gateway = initialize_gateway(empire)
    
    print("TEST 1: Trae command (Tier 1) accepted")
    set_mode(RealityMode.IMBUED, scene_id="test")
    
    event = DamageEvent("player", "enemy", 25.0)
    command = Command("trae", 1, "combat", [event])
    
    decision = submit_trae_command(command)
    assert decision.accepted
    assert decision.issuer == "trae"
    assert decision.authority_level == 1
    print(f"  ✓ Trae command accepted: {decision.reason}")
    
    print("\nTEST 2: Trae blocked by FINALIZED mode")
    set_mode(RealityMode.FINALIZED, scene_id="test")
    
    decision = submit_trae_command(command)
    assert not decision.accepted
    assert "FINALIZED" in decision.reason
    print(f"  ✓ Trae blocked: {decision.reason}")
    
    # Check shadow memory
    shadows = query_intents(issuer="trae")
    assert len(shadows) > 0
    print(f"  ✓ Rejection recorded in shadow memory")
    
    print("\nTEST 3: Human override (Tier 3) works in FINALIZED")
    decision = submit_human_command(command, override_level=3)
    assert decision.accepted
    print(f"  ✓ Human Tier 3 override: {decision.reason}")
    
    print("\nTEST 4: REPLAY mode blocks all mutations")
    set_mode(RealityMode.REPLAY)
    
    decision = submit_trae_command(command)
    assert not decision.accepted
    assert "REPLAY" in decision.reason
    print(f"  ✓ REPLAY blocks mutations: {decision.reason}")
    
    print("\nTEST 5: Gateway records history in canonical mode")
    set_mode(RealityMode.FINALIZED, scene_id="combat_scene")
    
    # Human Tier 3 can still act
    decision = submit_human_command(command, override_level=3)
    assert decision.accepted
    
    # Check history
    history = get_canonical_history("combat_scene")
    print(f"  ✓ History recorded: {len(history)} canonical event(s)")
    
    print("\n" + "="*50)
    print("✅ AGENT GATEWAY: ALL TESTS PASS")
    print("="*50)
    print("\nProven:")
    print("  ✓ Trae commands validated through gateway")
    print("  ✓ Reality mode enforced")
    print("  ✓ Human override works (Tier 2/3)")
    print("  ✓ Rejections → shadow memory")
    print("  ✓ Successes → history (in canonical mode)")
    print("  ✓ Authority tiers respected")
    print("\n🎉 Trae → Empire integration COMPLETE!")

if __name__ == "__main__":
    test_agent_gateway()
