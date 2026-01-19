"""
protocol_envelope.py - NGAT-RT Protocol Envelope System
Drop-in module for versioned, hashed snapshots

Usage:
    from protocol_envelope import ProtocolEnvelope
    
    envelope = ProtocolEnvelope()
    wrapped = envelope.wrap_snapshot(snapshot, tick=100)
    validated = envelope.unwrap_snapshot(wrapped)
"""
import json
import hashlib
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ProtocolVersion:
    """Protocol version tracking"""
    major: int = 1
    minor: int = 0
    
    def __str__(self):
        return f"{self.major}.{self.minor}"
    
    def compatible_with(self, other: str) -> bool:
        """Check if this version can talk to another"""
        try:
            other_major, other_minor = map(int, other.split('.'))
            # Major version must match
            return self.major == other_major
        except:
            return False

class ProtocolError(Exception):
    """Raised when protocol contract is violated"""
    pass


REQUIRED_EVENT_KEYS = {"@id", "@when", "@where"}


def validate_event(event: dict):
    missing = REQUIRED_EVENT_KEYS - event.keys()
    if missing:
        raise ProtocolError(
            f"Missing required event keys: {sorted(missing)}"
        )
    return True


class ProtocolEnvelope:
    """
    Mandatory envelope for all NGAT-RT messages.
    Enforces version checking and hash verification.
    """
    
    PROTOCOL_NAME = "NGAT-RT"
    
    def __init__(self, version: Optional[ProtocolVersion] = None, epoch_id: Optional[str] = None):
        self.version = version or ProtocolVersion()
        self.epoch_id = epoch_id or "world_default"
    
    def wrap_snapshot(self, payload: Dict[str, Any], tick: float) -> Dict[str, Any]:
        """
        Wrap raw snapshot in protocol envelope with hash.
        
        Returns:
            {
                "protocol": "NGAT-RT",
                "version": "1.0",
                "tick": 2048,
                "epoch": "world_ae91c",
                "type": "snapshot",
                "hash": "sha256:9fae...",
                "payload": { ... }
            }
        """
        # Calculate hash of payload for determinism verification
        payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        payload_hash = hashlib.sha256(payload_json.encode('utf-8')).hexdigest()
        
        envelope = {
            "protocol": self.PROTOCOL_NAME,
            "version": str(self.version),
            "tick": tick,
            "epoch": self.epoch_id,
            "type": "snapshot",
            "hash": f"sha256:{payload_hash}",
            "payload": payload
        }
        
        return envelope
    
    def wrap_command(self, payload: Dict[str, Any], tick: float) -> Dict[str, Any]:
        """Wrap command in protocol envelope"""
        return {
            "protocol": self.PROTOCOL_NAME,
            "version": str(self.version),
            "tick": tick,
            "epoch": self.epoch_id,
            "type": "command",
            "payload": payload
        }
    
    def unwrap(self, envelope: Dict[str, Any], expected_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Generic unwrap and validate protocol envelope.
        HARD REJECTION on any contract violation.
        
        Args:
            envelope: The raw envelope dict
            expected_type: If strict type checking is needed (e.g. "command")
            
        Raises:
            ProtocolError: If envelope is invalid
        """
        # Step 1: Validate envelope structure
        required_keys = ["protocol", "version", "tick", "epoch", "type", "payload"]
        for key in required_keys:
            if key not in envelope:
                raise ProtocolError(f"ENVELOPE_INVALID: Missing required field '{key}'")
        
        # Step 2: Validate protocol name
        if envelope["protocol"] != self.PROTOCOL_NAME:
            raise ProtocolError(
                f"PROTOCOL_MISMATCH: Expected '{self.PROTOCOL_NAME}', got '{envelope['protocol']}'"
            )
        
        # Step 3: Validate version compatibility
        if not self.version.compatible_with(envelope["version"]):
            raise ProtocolError(
                f"VERSION_INCOMPATIBLE: Client supports {self.version}, server sent {envelope['version']}"
            )
        
        # Step 4: Validate type
        if expected_type and envelope["type"] != expected_type:
            raise ProtocolError(f"TYPE_MISMATCH: Expected '{expected_type}', got '{envelope['type']}'")
        
        if envelope["type"] not in ["snapshot", "command", "delta"]:
            raise ProtocolError(f"TYPE_INVALID: Unknown message type '{envelope['type']}'")
        
        # Step 4.5: Validate command event payload
        if envelope["type"] == "command":
            validate_event(envelope["payload"])
        
        # Step 5: Verify hash if it's a snapshot (commands might not need hash but snapshots DO)
        if envelope["type"] == "snapshot":
            if "hash" not in envelope:
                raise ProtocolError("HASH_MISSING: Snapshot must include hash for determinism")
            
            expected_hash = envelope["hash"]
            payload = envelope["payload"]
            
            # Recalculate hash
            payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            actual_hash = f"sha256:{hashlib.sha256(payload_json.encode('utf-8')).hexdigest()}"
            
            if actual_hash != expected_hash:
                raise ProtocolError(
                    f"HASH_MISMATCH: Snapshot corrupted or tampered. "
                    f"Expected {expected_hash}, got {actual_hash}"
                )
        
        # Step 6: Return validated envelope (the whole thing or payload? User code expects envelope["payload"])
        # Actually user code was: envelope = self.runtime.envelope.unwrap(...) ; command = envelope["payload"]
        # which implies unwrap returns the ENVELOPE (verified) not just payload.
        # BUT unwrap_snapshot returned valid PAYLOAD.
        # User said: "envelope = self.runtime.envelope.unwrap(raw, expected_type='command')"
        # "command = envelope['payload']"
        # So it seems valid to return the whole validated envelope dict.
        
        return envelope

    def unwrap_snapshot(self, envelope: Dict[str, Any], verify_hash: bool = True) -> Dict[str, Any]:
        """Legacy helper for snapshots - returns payload directly for convenience"""
        validated_env = self.unwrap(envelope, expected_type="snapshot")
        return validated_env["payload"]
    
    def validate_snapshot_payload(self, payload: Dict[str, Any]) -> None:
        """
        Validate that snapshot payload has required structure.
        HARD REJECTION on missing required fields.
        
        Raises:
            ProtocolError: If payload structure is invalid
        """
        # Required top-level keys
        required = ["entities", "world"]
        for key in required:
            if key not in payload:
                raise ProtocolError(f"PAYLOAD_INVALID: Missing required key '{key}'")
        
        # Validate world structure
        world = payload["world"]
        if not isinstance(world, dict):
            raise ProtocolError("PAYLOAD_INVALID: 'world' must be object")
        
        if "time" not in world:
            raise ProtocolError("PAYLOAD_INVALID: world.time is required")
        
        # Validate entities structure
        entities = payload["entities"]
        if not isinstance(entities, dict):
            raise ProtocolError("PAYLOAD_INVALID: 'entities' must be object")
        
        # Validate each entity has required fields
        for eid, entity in entities.items():
            if not isinstance(entity, dict):
                raise ProtocolError(f"ENTITY_INVALID: Entity {eid} is not object")
            
            # Required entity fields
            entity_required = ["position", "velocity"]
            for field in entity_required:
                if field not in entity:
                    raise ProtocolError(
                        f"ENTITY_INVALID: Entity {eid} missing required field '{field}'"
                    )
                
                # Validate position/velocity are 3-element arrays
                value = entity[field]
                if not isinstance(value, (list, tuple)) or len(value) != 3:
                    raise ProtocolError(
                        f"ENTITY_INVALID: Entity {eid}.{field} must be [x,y,z] array"
                    )


# ============================================================================
# INTEGRATION HELPERS
# ============================================================================

def create_envelope_for_runtime(epoch_id: Optional[str] = None) -> ProtocolEnvelope:
    """Helper to create envelope in sim_runtime.py"""
    import uuid
    if epoch_id is None:
        epoch_id = f"world_{uuid.uuid4().hex[:8]}"
    return ProtocolEnvelope(epoch_id=epoch_id)


def wrap_http_response(envelope: ProtocolEnvelope, snapshot: Dict[str, Any], tick: float) -> Dict[str, Any]:
    """Helper to wrap HTTP response in sim_runtime.py"""
    wrapped = envelope.wrap_snapshot(snapshot, tick)
    return {
        "type": "snapshot",
        "data": wrapped
    }


def unwrap_http_request(envelope: ProtocolEnvelope, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to unwrap HTTP request in sim_runtime.py"""
    if "data" in request_data:
        return envelope.unwrap_snapshot(request_data["data"])
    return request_data


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Runtime wrapping snapshot
    envelope = create_envelope_for_runtime()
    
    raw_snapshot = {
        "entities": {
            "player": {
                "position": [0, 0, 0],
                "velocity": [1, 0, 0]
            }
        },
        "world": {
            "time": 1.5
        }
    }
    
    # Wrap it
    wrapped = envelope.wrap_snapshot(raw_snapshot, tick=100)
    print("Wrapped snapshot:")
    print(json.dumps(wrapped, indent=2))
    
    # Unwrap and verify
    try:
        validated = envelope.unwrap_snapshot(wrapped)
        print("\n✓ Snapshot validated successfully")
        print(f"  Protocol: {wrapped['protocol']}")
        print(f"  Version: {wrapped['version']}")
        print(f"  Hash verified: {wrapped['hash'][:20]}...")
    except ProtocolError as e:
        print(f"\n✗ Validation failed: {e}")
    
    # Example: Version mismatch
    bad_envelope = wrapped.copy()
    bad_envelope["version"] = "2.0"
    
    try:
        envelope.unwrap_snapshot(bad_envelope)
    except ProtocolError as e:
        print(f"\n✓ Correctly rejected version mismatch: {e}")
    
    # Example: Hash corruption
    corrupted = wrapped.copy()
    corrupted["payload"]["entities"]["player"]["position"] = [999, 999, 999]
    
    try:
        envelope.unwrap_snapshot(corrupted)
    except ProtocolError as e:
        print(f"\n✓ Correctly detected hash mismatch: {e}")
