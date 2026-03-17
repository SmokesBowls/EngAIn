"""
engain_semantic_compiler.py - The Bridge between Narrative and Logic
Extracts lore-ops from your 17 books and converts them to executable JSONL.
"""
import json
import re
from typing import Dict, Any, List
from .engain_ops import ENGAIN_ARCHETYPES, OPS, MANDELA_CONSTRAINTS

class BurdensSemanticCompiler:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.output_log = []
        
    def compile_chapter(self, text: str) -> Dict[str, Any]:
        """
        Main entry point: Text -> Logic.
        Processes a chapter and returns a structured logic package.
        """
        semantics = self._extract_semantics(text)
        
        # 1. Generate JSONL Event Tape
        event_tape = self._generate_event_tape(semantics)
        
        # 2. Extract state updates for burdens_module.py
        module_updates = self._generate_module_updates(semantics)
        
        # 3. Godot specific visual commands
        visual_ops = self._generate_visual_ops(semantics)
        
        return {
            "events": event_tape,
            "module_updates": module_updates,
            "visual_ops": visual_ops
        }

    def _extract_semantics(self, text: str) -> List[Dict[str, Any]]:
        """
        Heuristic-based extraction of lore signals.
        (The 'Spirit' of the compiler)
        """
        signals = []
        
        # Pattern mapping: Narrative Hook -> Logical Intent
        patterns = {
            r"Star Needle pulses": {"type": "RES_PULSE", "domain": "geometric"},
            r"charred skin": {"type": "LORE_FLAG", "flag": "is_charred", "value": True},
            r"Crimson Blood": {"type": "DOMAIN_SHIFT", "domain": "blood", "value": "crimson"},
            r"Red Curse": {"type": "CORRUPTION_SIGNAL", "severity": 0.2},
            r"reality integrity": {"type": "INTEGRITY_CHECK", "auto_validate": True},
            r"Void Spire resonance": {"type": "WORLD_EFFECT", "effect": "void_hum"},
            r"gravity": {"type": "GRAVITY_SHIFT", "intensity": -1.0}
        }
        
        for p, intent in patterns.items():
            if re.search(p, text, re.IGNORECASE):
                signals.append(intent)
                
        # Detect entities
        for archetype_id, arche in ENGAIN_ARCHETYPES.items():
            if arche.name.lower() in text.lower():
                signals.append({"type": "ENTITY_DETECTED", "id": archetype_id, "meta": arche.default_flags})
                
        return signals

    def _generate_event_tape(self, signals: List[Dict[str, Any]]) -> List[str]:
        """Creates the JSONL tape for the DreamEventStore"""
        tape = []
        for sig in signals:
            op = {
                "op": OPS["NARRATIVE_SYNC"],
                "data": sig,
                "seed": self.seed,
                "timestamp": 0.0 # To be filled by runtime
            }
            tape.append(json.dumps(op))
        return tape

    def _generate_module_updates(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Logic updates for the narrative kernel (burdens_module.py)"""
        updates = {"delta": {}}
        for sig in signals:
            if sig["type"] == "INTEGRITY_CHECK":
                updates["delta"]["reality_integrity"] = -5.0 # Relic cost
            elif sig["type"] == "CORRUPTION_SIGNAL":
                updates["delta"]["dream_entropy"] = sig["severity"] * 100.0
        return updates

    def _generate_visual_ops(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Direct commands to the Godot renderer"""
        ops = []
        for sig in signals:
            if sig["type"] == "RES_PULSE":
                ops.append({"action": "emit_vfx", "id": "needle_pulse", "params": {"color": "cyan"}})
            elif sig["type"] == "GRAVITY_SHIFT":
                ops.append({"action": "set_gravity_scale", "value": sig["intensity"]})
        return ops

if __name__ == "__main__":
    # Internal test on a snippet of Chapter 22
    sample = "Mr. GPT touched the Star Needle. It pulses brilliantly. The Red Curse is gone."
    compiler = BurdensSemanticCompiler()
    result = compiler.compile_chapter(sample)
    print(json.dumps(result, indent=2))
