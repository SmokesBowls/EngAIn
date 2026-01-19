"""
zon_bridge.py - Mandatory Serialization Bridge

Enforces typed contracts between narrative pipeline and Empire.
NO loose JSON allowed across this boundary.

Defense Layer 1: Protect engine-agnostic core from data drift.

Flow:
  Narrative Pipeline (.zon/.zonj.json)
    ↓
  ZON Bridge (THIS FILE - type enforcement)
    ↓
  Empire (typed domain models)
    ↓
  Kernels (pure Python)
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import json

# Import domain models from kernels
from combat3d_mr import CombatSnapshot, CombatEntity, DamageEvent

@dataclass
class ZONBridgeError(Exception):
    """Raised when ZON data fails contract validation"""
    message: str
    zone_field: Optional[str] = None
    expected_type: Optional[str] = None
    actual_value: Any = None


class ZONBridge:
    """
    Mandatory serialization layer between narrative and Empire.
    
    Responsibilities:
    1. Deserialize ZON → typed domain models
    2. Serialize domain models → ZON  
    3. Enforce contracts (fail fast on drift)
    4. Audit all conversions
    
    CRITICAL: This is the guardian of engine-agnostic purity.
    If data crosses this boundary without validation, the whole
    architecture collapses.
    """
    
    def __init__(self, strict: bool = True, audit: bool = True):
        self.strict = strict  # Fail on any contract violation
        self.audit = audit    # Log all conversions
        self.conversion_log = []
    
    # ================================================================
    # COMBAT3D CONVERSIONS
    # ================================================================
    
    def deserialize_combat_snapshot(self, zon_data: Dict[str, Any]) -> CombatSnapshot:
        """
        ZON → CombatSnapshot (typed domain model)
        
        Contract enforcement:
        - Must have 'entities' field (dict)
        - Each entity must have: id, health, max_health
        - All numeric fields must be float/int
        
        Raises ZONBridgeError if contract violated.
        """
        if self.audit:
            self._log_conversion("ZON → CombatSnapshot", zon_data)
        
        # Contract: entities field must exist
        if "entities" not in zon_data:
            raise ZONBridgeError(
                message="Missing required field: 'entities'",
                zone_field="entities",
                expected_type="dict",
                actual_value=None
            )
        
        entities_data = zon_data["entities"]
        
        # Contract: entities must be dict
        if not isinstance(entities_data, dict):
            raise ZONBridgeError(
                message="Field 'entities' must be dict",
                zone_field="entities",
                expected_type="dict",
                actual_value=type(entities_data).__name__
            )
        
        # Convert each entity
        entities = {}
        for entity_id, entity_data in entities_data.items():
            try:
                entity = self._deserialize_combat_entity(entity_id, entity_data)
                entities[entity_id] = entity
            except Exception as e:
                raise ZONBridgeError(
                    message=f"Failed to deserialize entity '{entity_id}': {e}",
                    zone_field=f"entities.{entity_id}",
                    actual_value=entity_data
                )
        
        return CombatSnapshot(entities=entities)
    
    def _deserialize_combat_entity(self, entity_id: str, data: Dict) -> CombatEntity:
        """Convert ZON entity data → CombatEntity"""
        
        # Required fields
        required = ["health", "max_health"]
        for field in required:
            if field not in data:
                raise ZONBridgeError(
                    message=f"Entity missing required field: '{field}'",
                    zone_field=f"entities.{entity_id}.{field}",
                    expected_type="float",
                    actual_value=None
                )
        
        # Extract and validate
        health = float(data["health"])
        max_health = float(data["max_health"])
        
        return CombatEntity(entity_id, health, max_health)
    
    def deserialize_damage_event(self, zon_data: Dict[str, Any]) -> DamageEvent:
        """
        ZON → DamageEvent
        
        Contract:
        - Must have: attacker/source_id, target/target_id, amount
        - amount must be numeric
        """
        if self.audit:
            self._log_conversion("ZON → DamageEvent", zon_data)
        
        # Support both "attacker"/"target" (narrative) and "source_id"/"target_id" (kernel)
        source = zon_data.get("attacker") or zon_data.get("source_id")
        target = zon_data.get("target") or zon_data.get("target_id")
        amount = zon_data.get("amount")
        
        if not source:
            raise ZONBridgeError(
                message="Missing required field: 'attacker' or 'source_id'",
                zone_field="attacker/source_id",
                expected_type="string",
                actual_value=None
            )
        
        if not target:
            raise ZONBridgeError(
                message="Missing required field: 'target' or 'target_id'",
                zone_field="target/target_id",
                expected_type="string",
                actual_value=None
            )
        
        if amount is None:
            raise ZONBridgeError(
                message="Missing required field: 'amount'",
                zone_field="amount",
                expected_type="float",
                actual_value=None
            )
        
        return DamageEvent(
            str(source),
            str(target),
            float(amount)
        )
    
    def serialize_combat_snapshot(self, snapshot: CombatSnapshot) -> Dict[str, Any]:
        """
        CombatSnapshot → ZON format
        
        Produces clean, engine-agnostic ZON output.
        """
        if self.audit:
            self._log_conversion("CombatSnapshot → ZON", snapshot)
        
        zon_data = {
            "entities": {}
        }
        
        for entity_id, entity in snapshot.entities.items():
            zon_data["entities"][entity_id] = {
                "health": entity.health,
                "max_health": entity.max_health
            }
        
        return zon_data
    
    def serialize_damage_event(self, event: DamageEvent) -> Dict[str, Any]:
        """DamageEvent → ZON format"""
        if self.audit:
            self._log_conversion("DamageEvent → ZON", event)
        
        return {
            "attacker": event.source_id,  # Use narrative-friendly name
            "target": event.target_id,
            "amount": event.amount
        }
    
    # ================================================================
    # FILE I/O
    # ================================================================
    
    def load_zon_file(self, path: Path) -> Dict[str, Any]:
        """
        Load .zon or .zonj.json file.
        
        Returns raw ZON data (still needs deserialization).
        """
        if not path.exists():
            raise ZONBridgeError(
                message=f"ZON file not found: {path}",
                actual_value=str(path)
            )
        
        # Determine format
        if path.suffix == ".json" or path.name.endswith(".zonj.json"):
            # JSON format
            with path.open("r") as f:
                return json.load(f)
        else:
            # .zon text format (would need parser)
            # For now, assume JSON
            with path.open("r") as f:
                return json.load(f)
    
    def save_zon_file(self, data: Dict[str, Any], path: Path):
        """Save ZON data to file"""
        with path.open("w") as f:
            json.dump(data, f, indent=2)
    
    # ================================================================
    # AUDIT LOG
    # ================================================================
    
    def _log_conversion(self, conversion_type: str, data: Any):
        """Record conversion for audit trail"""
        self.conversion_log.append({
            "type": conversion_type,
            "data_summary": str(data)[:100]  # First 100 chars
        })
    
    def get_audit_log(self) -> List[Dict]:
        """Get conversion audit log"""
        return self.conversion_log.copy()
    
    def clear_audit_log(self):
        """Clear audit log"""
        self.conversion_log = []


# ================================================================
# CONVENIENCE FUNCTIONS
# ================================================================

_global_bridge = ZONBridge(strict=True, audit=True)

def deserialize_combat_snapshot(zon_data: Dict[str, Any]) -> CombatSnapshot:
    """Convenience: ZON → CombatSnapshot"""
    return _global_bridge.deserialize_combat_snapshot(zon_data)

def serialize_combat_snapshot(snapshot: CombatSnapshot) -> Dict[str, Any]:
    """Convenience: CombatSnapshot → ZON"""
    return _global_bridge.serialize_combat_snapshot(snapshot)

def load_zon_combat_snapshot(path: Path) -> CombatSnapshot:
    """Load ZON file and deserialize to CombatSnapshot"""
    zon_data = _global_bridge.load_zon_file(path)
    return _global_bridge.deserialize_combat_snapshot(zon_data)


def deserialize_damage_event(zon_data: Dict[str, Any]) -> DamageEvent:
    """Convenience: ZON → DamageEvent"""
    return _global_bridge.deserialize_damage_event(zon_data)

def serialize_damage_event(event: DamageEvent) -> Dict[str, Any]:
    """Convenience: DamageEvent → ZON"""
    return _global_bridge.serialize_damage_event(event)

def save_combat_snapshot_zon(snapshot: CombatSnapshot, path: Path):
    """Serialize CombatSnapshot and save to ZON file"""
    zon_data = _global_bridge.serialize_combat_snapshot(snapshot)
    _global_bridge.save_zon_file(zon_data, path)
