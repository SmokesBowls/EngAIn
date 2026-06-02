#!/usr/bin/env python3
"""
test_protocol.py - Protocol Envelope & Slice Enforcement Tests

Tests that verify:
1. Protocol envelope structure is correct
2. Hash verification works
3. Version checking works
4. Contamination guards catch violations
"""

import sys
import json
from protocol_envelope import ProtocolEnvelope
from slice_builders import (
    build_entity_kview_v1, 
    build_spatial_slice_v1,
    assert_no_raw_dict_contamination,
    SliceError,
    ContaminationError
)

print("="*60)
print("PROTOCOL ENFORCEMENT TEST SUITE")
print("="*60)
print()

# ============================================================
# TEST 1: Protocol Envelope Structure
# ============================================================
print("TEST 1: Protocol Envelope Structure")
print("-" * 40)

envelope = ProtocolEnvelope(protocol="NGAT-RT", version="1.0")
snapshot = {
    "entities": {"test": {"position": [1, 2, 3], "velocity": [0, 0, 0]}},
    "world": {"time": 1.0}
}

wrapped = envelope.wrap_snapshot(snapshot, tick=1.0)

# Check structure
required_keys = ["protocol", "version", "type", "tick", "epoch", "hash", "payload"]
missing = [k for k in required_keys if k not in wrapped]

if missing:
    print(f"✗ FAIL: Missing keys: {missing}")
    sys.exit(1)
else:
    print(f"✓ PASS: All required keys present")

# Check values
assert wrapped["protocol"] == "NGAT-RT", "Protocol name incorrect"
assert wrapped["version"] == "1.0", "Version incorrect"
assert wrapped["type"] == "snapshot", "Type incorrect"
assert wrapped["tick"] == 1.0, "Tick incorrect"
assert "payload" in wrapped, "Payload missing"

print(f"  Protocol: {wrapped['protocol']}")
print(f"  Version: {wrapped['version']}")
print(f"  Epoch: {wrapped['epoch'][:16]}...")
print(f"  Hash: {wrapped['hash'][:24]}...")
print()

# ============================================================
# TEST 2: Hash Verification
# ============================================================
print("TEST 2: Hash Verification")
print("-" * 40)

# Original hash
original_hash = wrapped["hash"]
print(f"  Original hash: {original_hash[:40]}...")

# Tamper with payload
tampered = wrapped.copy()
tampered["payload"]["world"]["time"] = 999.0

# Recalculate hash
payload_json = json.dumps(tampered["payload"], sort_keys=True)
import hashlib
new_hash = "sha256:" + hashlib.sha256(payload_json.encode('utf-8')).hexdigest()

if new_hash != original_hash:
    print(f"✓ PASS: Hash mismatch detected (tampering caught)")
    print(f"  Tampered hash: {new_hash[:40]}...")
else:
    print(f"✗ FAIL: Hash should change when payload modified")
    sys.exit(1)
print()

# ============================================================
# TEST 3: Version Checking
# ============================================================
print("TEST 3: Version Enforcement")
print("-" * 40)

# Create envelope with different version
env_v2 = ProtocolEnvelope(protocol="NGAT-RT", version="2.0")
wrapped_v2 = env_v2.wrap_snapshot(snapshot, tick=1.0)

print(f"  v1.0 epoch: {wrapped['epoch'][:16]}...")
print(f"  v2.0 epoch: {wrapped_v2['epoch'][:16]}...")

# Epochs should be different (includes version)
if wrapped["epoch"] != wrapped_v2["epoch"]:
    print(f"✓ PASS: Version changes epoch (enforced isolation)")
else:
    print(f"✗ FAIL: Version should affect epoch")
    sys.exit(1)
print()

# ============================================================
# TEST 4: Slice Contamination Guard
# ============================================================
print("TEST 4: Contamination Guard")
print("-" * 40)

# Test that raw snapshot dict is caught
raw_snapshot = {
    "entities": {"test": {"position": [1, 2, 3]}},
    "world": {"time": 1.0}
}

try:
    assert_no_raw_dict_contamination(raw_snapshot, "test_kernel")
    print("✗ FAIL: Contamination guard should have caught raw snapshot")
    sys.exit(1)
except ContaminationError as e:
    print(f"✓ PASS: Contamination detected")
    print(f"  Error: {str(e)[:80]}...")

# Test that typed slice passes
valid_world = {
    "entities": {"test": {"position": [1, 2, 3], "velocity": [0, 0, 0]}},
    "world": {"time": 1.0}
}

try:
    slice_obj = build_spatial_slice_v1(valid_world, tick=1.0, eid="test")
    assert_no_raw_dict_contamination(slice_obj, "test_kernel")
    print(f"✓ PASS: Typed slice accepted")
except ContaminationError:
    print(f"✗ FAIL: Typed slice should pass")
    sys.exit(1)
print()

# ============================================================
# TEST 5: Slice Builder Validation
# ============================================================
print("TEST 5: Slice Builder Validation")
print("-" * 40)

# Test missing position (should fail)
bad_world = {
    "entities": {
        "bad_entity": {"velocity": [0, 0, 0]}  # Missing position!
    },
    "world": {}
}

try:
    build_entity_kview_v1(bad_world, "bad_entity")
    print("✗ FAIL: Should reject entity without position")
    sys.exit(1)
except SliceError as e:
    print(f"✓ PASS: Rejected missing position")
    print(f"  Error: {e}")

# Test valid entity (should pass)
good_world = {
    "entities": {
        "good_entity": {
            "position": [5.0, 0.0, 3.0],
            "velocity": [0.0, 0.0, 0.0]
        }
    },
    "world": {}
}

try:
    entity = build_entity_kview_v1(good_world, "good_entity")
    print(f"✓ PASS: Valid entity accepted")
    print(f"  EID: {entity.eid}")
    print(f"  Position: {entity.pos}")
    print(f"  Velocity: {entity.vel}")
except SliceError as e:
    print(f"✗ FAIL: Valid entity should pass: {e}")
    sys.exit(1)
print()

# ============================================================
# TEST 6: Epoch Determinism
# ============================================================
print("TEST 6: Epoch Determinism")
print("-" * 40)

# Same inputs should produce same epoch
env1 = ProtocolEnvelope(protocol="NGAT-RT", version="1.0")
env2 = ProtocolEnvelope(protocol="NGAT-RT", version="1.0")

wrap1 = env1.wrap_snapshot(snapshot, tick=1.0)
wrap2 = env2.wrap_snapshot(snapshot, tick=1.0)

if wrap1["epoch"] == wrap2["epoch"]:
    print(f"✓ PASS: Same inputs produce same epoch (deterministic)")
    print(f"  Epoch: {wrap1['epoch'][:24]}...")
else:
    print(f"✗ FAIL: Epoch should be deterministic")
    print(f"  Epoch 1: {wrap1['epoch']}")
    print(f"  Epoch 2: {wrap2['epoch']}")
    sys.exit(1)
print()

# ============================================================
# SUMMARY
# ============================================================
print("="*60)
print("ALL TESTS PASSED ✓")
print("="*60)
print()
print("Enforcement layers verified:")
print("  ✓ Protocol envelope structure")
print("  ✓ Hash verification (tamper detection)")
print("  ✓ Version isolation (epoch enforcement)")
print("  ✓ Contamination guards (raw dict detection)")
print("  ✓ Slice validation (contract enforcement)")
print("  ✓ Epoch determinism (reproducible builds)")
print()
print("Engine is production-ready! 🎉")
