# protocol_envelope.py
import hashlib
import json
from typing import Dict, Any, Optional
import time

class ProtocolError(Exception):
    """Exception for protocol violations"""
    pass

class ProtocolEnvelope:
    """Wraps game state in a standardized envelope with metadata and hashing"""
    
    PROTOCOL_NAME = "EngAIn"
    version = "1.0.1"
    epoch_id = "runtime_alpha"

    def __init__(self):
        self.start_time = time.time()

    def wrap_snapshot(self, state: Dict[str, Any], tick: float) -> Dict[str, Any]:
        """
        Wraps the raw simulation state in the protocol format.
        
        Args:
            state: The raw game state dictionary
            tick: Current simulation time
            
        Returns:
            Dictionary containing protocol metadata and the state payload
        """
        # Create deterministic JSON string for hashing
        # We convert sets to sorted lists and handle non-serializable types
        serializable_state = self._make_serializable(state)
        payload_str = json.dumps(serializable_state, sort_keys=True, default=str)
        
        # Generate hash for state integrity verification
        state_hash = hashlib.sha256(payload_str.encode()).hexdigest()
        
        envelope = {
            "protocol": self.PROTOCOL_NAME,
            "version": self.version,
            "epoch": self.epoch_id,
            "tick": tick,
            "hash": state_hash,
            "timestamp": time.time() - self.start_time,
            "payload": state
        }
        
        return envelope

    def unwrap_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses and validates an incoming command envelope.
        (Optional implementation for command validation)
        """
        # Basic validation could go here
        return command_data

    def _make_serializable(self, obj):
        """Recursively converts objects into JSON-serializable formats"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, set):
            return sorted([self._make_serializable(item) for item in obj])
        # Handle numpy arrays or other common game types if needed
        elif hasattr(obj, 'tolist'): 
            return obj.tolist()
        else:
            return obj

def create_envelope_for_runtime() -> ProtocolEnvelope:
    """Factory function to initialize the protocol envelope"""
    return ProtocolEnvelope()
