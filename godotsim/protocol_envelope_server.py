#!/usr/bin/env python3
"""
SERVER-SIDE PROTOCOL ENVELOPE GENERATOR
Complements FIX 3: Protocol Envelope Validation

Generates snapshots with mandatory integrity envelope:
- Version (semantic)
- Tick (ordering)
- Epoch (world session)
- Content hash (integrity)
"""

import hashlib
import json
import time
from typing import Dict, Any
from dataclasses import dataclass, asdict

# =============================================================================
# PROTOCOL CONFIGURATION
# =============================================================================

PROTOCOL_VERSION = "1.0.0"  # Matches client expectation
HASH_ALGORITHM = "sha256"

@dataclass
class ProtocolEnvelope:
    """Protocol envelope wrapping game state snapshot"""
    version: str
    tick: int
    epoch: str
    content_hash: str
    payload: Dict[str, Any]
    timestamp: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)


# =============================================================================
# ENVELOPE GENERATION
# =============================================================================

def create_snapshot_envelope(payload: Dict[str, Any],
                            tick: int,
                            epoch: str) -> Dict[str, Any]:
    """
    Wrap snapshot payload in protocol envelope
    
    Args:
        payload: Game state snapshot (spatial3d, etc.)
        tick: Current server tick
        epoch: World/session identifier
        
    Returns:
        Complete envelope ready for wire transmission
    """
    
    # Calculate content hash (deterministic)
    content_hash = calculate_content_hash(payload)
    
    # Create envelope
    envelope = ProtocolEnvelope(
        version=PROTOCOL_VERSION,
        tick=tick,
        epoch=epoch,
        content_hash=content_hash,
        payload=payload,
        timestamp=time.time()
    )
    
    return envelope.to_dict()


def calculate_content_hash(content: Dict[str, Any]) -> str:
    """
    Calculate deterministic hash of content
    
    CRITICAL: Must match client-side calculation exactly
    - Same JSON serialization (sorted keys)
    - Same hash algorithm
    """
    
    # Deterministic JSON serialization
    content_json = json.dumps(content, sort_keys=True, separators=(',', ':'))
    
    # Calculate hash
    hash_obj = hashlib.sha256(content_json.encode('utf-8'))
    content_hash = hash_obj.hexdigest()
    
    return content_hash


# =============================================================================
# INTEGRATION WITH EXISTING SERVER
# =============================================================================

class SnapshotEnvelopeMiddleware:
    """
    Middleware to wrap snapshots with protocol envelope
    
    Usage:
        middleware = SnapshotEnvelopeMiddleware()
        
        # In HTTP handler
        raw_snapshot = sim_runtime.get_snapshot()
        envelope = middleware.wrap(raw_snapshot, current_tick)
        return JSONResponse(envelope)
    """
    
    def __init__(self, world_epoch: str = None):
        self.world_epoch = world_epoch or self._generate_epoch()
        self.last_tick = 0
        
        # Statistics
        self.stats = {
            'envelopes_created': 0,
            'total_bytes_sent': 0,
            'hash_collisions': 0
        }
    
    def wrap(self, payload: Dict[str, Any], tick: int) -> Dict[str, Any]:
        """Wrap snapshot in protocol envelope"""
        
        # Validate tick ordering
        if tick <= self.last_tick:
            raise ValueError(f"Tick regression: {tick} <= {self.last_tick}")
        
        self.last_tick = tick
        
        # Create envelope
        envelope = create_snapshot_envelope(payload, tick, self.world_epoch)
        
        # Update stats
        self.stats['envelopes_created'] += 1
        envelope_json = json.dumps(envelope)
        self.stats['total_bytes_sent'] += len(envelope_json)
        
        return envelope
    
    def reset_epoch(self):
        """Reset epoch (server restart, world reload)"""
        old_epoch = self.world_epoch
        self.world_epoch = self._generate_epoch()
        self.last_tick = 0
        
        print(f"[ENVELOPE] Epoch changed: {old_epoch} → {self.world_epoch}")
        return self.world_epoch
    
    def _generate_epoch(self) -> str:
        """Generate unique epoch identifier"""
        timestamp = int(time.time() * 1000)
        return f"epoch_{timestamp}"
    
    def get_stats(self) -> Dict:
        """Get envelope statistics"""
        avg_bytes = 0
        if self.stats['envelopes_created'] > 0:
            avg_bytes = self.stats['total_bytes_sent'] / self.stats['envelopes_created']
        
        return {
            **self.stats,
            'current_epoch': self.world_epoch,
            'last_tick': self.last_tick,
            'avg_envelope_bytes': avg_bytes
        }


# =============================================================================
# EXAMPLE HTTP SERVER INTEGRATION
# =============================================================================

"""
FastAPI Example:

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from protocol_envelope import SnapshotEnvelopeMiddleware

app = FastAPI()
envelope_middleware = SnapshotEnvelopeMiddleware()

# Your existing simulation runtime
sim_runtime = EngAInSimulation()

@app.get("/snapshot")
async def get_snapshot():
    # Get raw snapshot from sim
    raw_snapshot = {
        "spatial3d": {
            "entities": sim_runtime.get_entities()
        }
    }
    
    current_tick = sim_runtime.current_tick
    
    # Wrap in protocol envelope
    envelope = envelope_middleware.wrap(raw_snapshot, current_tick)
    
    return JSONResponse(envelope)

@app.get("/envelope/stats")
async def envelope_stats():
    return envelope_middleware.get_stats()
```
"""


# =============================================================================
# VALIDATION & TESTING
# =============================================================================

def validate_envelope_structure(envelope: Dict) -> bool:
    """Validate envelope has all required fields"""
    
    required = ['version', 'tick', 'epoch', 'content_hash', 'payload']
    
    for field in required:
        if field not in envelope:
            print(f"✗ Missing required field: {field}")
            return False
    
    return True


def verify_hash_integrity(envelope: Dict) -> bool:
    """Verify hash matches payload"""
    
    received_hash = envelope['content_hash']
    payload = envelope['payload']
    
    calculated_hash = calculate_content_hash(payload)
    
    if calculated_hash != received_hash:
        print(f"✗ Hash mismatch!")
        print(f"  Received:   {received_hash}")
        print(f"  Calculated: {calculated_hash}")
        return False
    
    return True


# =============================================================================
# DEMONSTRATION
# =============================================================================

if __name__ == "__main__":
    print("="*70)
    print("PROTOCOL ENVELOPE GENERATOR - SERVER SIDE")
    print("="*70)
    
    # Create middleware
    middleware = SnapshotEnvelopeMiddleware()
    
    print(f"\n✓ Middleware initialized")
    print(f"  Epoch: {middleware.world_epoch}")
    print(f"  Protocol version: {PROTOCOL_VERSION}")
    
    # Simulate snapshot sequence
    print("\n[TEST] Generating snapshot sequence...\n")
    
    for tick in range(1, 6):
        # Simulate game state
        payload = {
            "spatial3d": {
                "entities": {
                    "player": {
                        "id": "player",
                        "position": [tick * 1.0, 0.0, 0.0],
                        "velocity": [1.0, 0.0, 0.0]
                    }
                }
            }
        }
        
        # Wrap in envelope
        envelope = middleware.wrap(payload, tick)
        
        # Validate
        structure_ok = validate_envelope_structure(envelope)
        hash_ok = verify_hash_integrity(envelope)
        
        status = "✓" if (structure_ok and hash_ok) else "✗"
        print(f"Tick {tick}: {status} Envelope valid")
        print(f"   Hash: {envelope['content_hash'][:16]}...")
    
    # Show stats
    print("\n" + "="*70)
    print("STATISTICS")
    print("="*70)
    
    stats = middleware.get_stats()
    print(f"Envelopes created:  {stats['envelopes_created']}")
    print(f"Total bytes sent:   {stats['total_bytes_sent']}")
    print(f"Avg envelope size:  {stats['avg_envelope_bytes']:.0f} bytes")
    print(f"Current tick:       {stats['last_tick']}")
    
    print("\n" + "="*70)
    print("INTEGRATION READY")
    print("="*70)
    print("""
Add to your HTTP server:

from protocol_envelope import SnapshotEnvelopeMiddleware

middleware = SnapshotEnvelopeMiddleware()

@app.get("/snapshot")
async def get_snapshot():
    raw = sim.get_snapshot()
    envelope = middleware.wrap(raw, sim.current_tick)
    return JSONResponse(envelope)

Client will validate:
✓ Version compatibility
✓ Tick ordering
✓ Hash integrity
✓ Epoch consistency

Result: End-to-end transport integrity
    """)
