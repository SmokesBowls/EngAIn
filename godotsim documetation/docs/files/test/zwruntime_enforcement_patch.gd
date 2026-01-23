extends Node
## ZWRuntime Enforcement Patch
## Add these functions to your ZWRuntime.gd file

# Add these constants near the top of ZWRuntime.gd (after extends Node):
# const EXPECTED_PROTOCOL = "NGAT-RT"
# const EXPECTED_VERSION = "1.0"
# var current_epoch: String = ""
# var epoch_changes: int = 0


## Hash Verification - Detects corruption and tampering
func _verify_snapshot_hash(envelope: Dictionary) -> bool:
	if not envelope.has("hash") or not envelope.has("payload"):
		push_error("ENFORCEMENT: Missing hash or payload")
		return false
	
	var expected_hash = envelope["hash"]
	var payload = envelope["payload"]
	
	# Compute hash from payload
	var payload_json = JSON.stringify(payload)
	var computed_hash = "sha256:" + payload_json.sha256_text()
	
	if expected_hash != computed_hash:
		push_error("ENFORCEMENT: Hash mismatch! Snapshot corrupted or tampered!")
		push_error("  Expected: %s" % expected_hash.substr(0, 24))
		push_error("  Computed: %s" % computed_hash.substr(0, 24))
		return false
	
	return true


## Protocol Version Check - Ensures client/server compatibility
func _verify_protocol_version(envelope: Dictionary) -> bool:
	if not envelope.has("protocol") or not envelope.has("version"):
		push_error("ENFORCEMENT: Missing protocol or version")
		return false
	
	var protocol = envelope["protocol"]
	var version = envelope["version"]
	
	if protocol != EXPECTED_PROTOCOL:
		push_error("ENFORCEMENT: Protocol mismatch!")
		push_error("  Expected: %s" % EXPECTED_PROTOCOL)
		push_error("  Received: %s" % protocol)
		push_error("Client and server are incompatible - restart required")
		return false
	
	if version != EXPECTED_VERSION:
		push_error("ENFORCEMENT: Version mismatch!")
		push_error("  Expected: %s" % EXPECTED_VERSION)
		push_error("  Received: %s" % version)
		push_error("Client and server are incompatible - restart required")
		return false
	
	return true


## Epoch Continuity - Tracks world resets and session changes
func _verify_epoch_continuity(envelope: Dictionary) -> bool:
	if not envelope.has("epoch"):
		push_error("ENFORCEMENT: Missing epoch")
		return false
	
	var epoch = envelope["epoch"]
	
	# First snapshot - lock to this epoch
	if current_epoch == "":
		current_epoch = epoch
		print("ZWRuntime: World epoch locked to %s..." % epoch.substr(0, 24))
		return true
	
	# Check continuity
	if epoch != current_epoch:
		epoch_changes += 1
		print("ZWRuntime: Epoch changed! World was reset.")
		print("  Old: %s..." % current_epoch.substr(0, 16))
		print("  New: %s..." % epoch.substr(0, 16))
		print("  Total changes: %d" % epoch_changes)
		current_epoch = epoch
		return true
	
	return true


# INTEGRATION INSTRUCTIONS:
# 1. Add the constants at the top of ZWRuntime.gd
# 2. Add these three functions before _on_snapshot_completed
# 3. Update _on_snapshot_completed to call these functions:
#
#    # After protocol validation
#    if not _verify_protocol_version(data):
#        push_error("ENFORCEMENT: Version check failed")
#        return
#    
#    if not _verify_snapshot_hash(data):
#        push_error("ENFORCEMENT: Hash verification failed")
#        _request_next_snapshot()
#        return
#    
#    if not _verify_epoch_continuity(data):
#        push_error("ENFORCEMENT: Epoch verification failed")
#        _request_next_snapshot()
#        return
