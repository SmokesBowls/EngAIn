# ZWRuntime.gd - CLIENT ASSERTIONS PATCH
# Add these enforcement functions to ZWRuntime.gd

# ============================================================
# HASH VERIFICATION (Add after existing functions)
# ============================================================

func _verify_snapshot_hash(envelope: Dictionary) -> bool:
	"""
	Verify snapshot hash matches payload.
	Detects network corruption and tampering.
	"""
	if not envelope.has("hash") or not envelope.has("payload"):
		push_error("Envelope missing hash or payload")
		return false
	
	var expected_hash = envelope.hash
	var payload = envelope.payload
	
	# Calculate hash of payload
	var json_str = JSON.stringify(payload)
	var actual_hash = "sha256:" + json_str.sha256_text()
	
	if actual_hash != expected_hash:
		push_error("HASH MISMATCH: Snapshot corrupted or tampered!")
		push_error("  Expected: " + expected_hash.substr(0, 40) + "...")
		push_error("  Actual:   " + actual_hash.substr(0, 40) + "...")
		return false
	
	return true

# ============================================================
# VERSION CHECKING (Add after hash verification)
# ============================================================

const EXPECTED_PROTOCOL = "NGAT-RT"
const EXPECTED_VERSION = "1.0"

func _verify_protocol_version(envelope: Dictionary) -> bool:
	"""
	Verify protocol and version match expected values.
	Prevents version drift and incompatibility.
	"""
	if not envelope.has("protocol"):
		push_error("Missing protocol field")
		return false
	
	if envelope.protocol != EXPECTED_PROTOCOL:
		push_error("Protocol mismatch: expected " + EXPECTED_PROTOCOL + ", got " + envelope.protocol)
		return false
	
	if not envelope.has("version"):
		push_error("Missing version field")
		return false
	
	if envelope.version != EXPECTED_VERSION:
		push_error("Version mismatch: expected " + EXPECTED_VERSION + ", got " + envelope.version)
		push_error("Client and server are out of sync - restart both!")
		return false
	
	return true

# ============================================================
# EPOCH TRACKING (Add after version checking)
# ============================================================

var current_epoch: String = ""
var epoch_changes: int = 0

func _verify_epoch_continuity(envelope: Dictionary) -> bool:
	"""
	Track epoch changes to detect world resets.
	Epoch should stay constant during a session.
	"""
	if not envelope.has("epoch"):
		push_error("Missing epoch field")
		return false
	
	var new_epoch = envelope.epoch
	
	# First snapshot
	if current_epoch == "":
		current_epoch = new_epoch
		print("ZWRuntime: World epoch locked to ", current_epoch.substr(0, 16), "...")
		return true
	
	# Epoch change detected
	if new_epoch != current_epoch:
		epoch_changes += 1
		print("ZWRuntime: EPOCH CHANGE detected (world reset #", epoch_changes, ")")
		print("  Old: ", current_epoch.substr(0, 16), "...")
		print("  New: ", new_epoch.substr(0, 16), "...")
		current_epoch = new_epoch
		
		# Could emit signal here for UI to show "World restarted"
		# emit_signal("world_reset", epoch_changes)
	
	return true

# ============================================================
# MODIFIED _on_snapshot_completed (Replace existing function)
# ============================================================

func _on_snapshot_completed(result, response_code, headers, body):
	if is_busy:
		is_busy = false
	
	# 1. HTTP Error
	if response_code != 200:
		print("ZWRuntime: Server error ", response_code)
		_request_next_snapshot()
		return
	
	# 2. JSON Parse
	var json = JSON.new()
	var parse_result = json.parse(body.get_string_from_utf8())
	
	if parse_result != OK:
		print("ZWRuntime: Parse failed")
		_request_next_snapshot()
		return
	
	var data = json.data
	
	# 3. Protocol Validation
	if not data.has("protocol"):
		push_error("INVALID SNAPSHOT: missing protocol envelope")
		_request_next_snapshot()
		return
	
	# 4. ENFORCEMENT: Version Check (NEW!)
	if not _verify_protocol_version(data):
		push_error("ENFORCEMENT: Version check failed - stopping snapshots")
		# Don't request next - force user to restart
		return
	
	# 5. ENFORCEMENT: Hash Verification (NEW!)
	if not _verify_snapshot_hash(data):
		push_error("ENFORCEMENT: Hash verification failed - snapshot corrupted")
		_request_next_snapshot()  # Try next snapshot
		return
	
	# 6. ENFORCEMENT: Epoch Tracking (NEW!)
	if not _verify_epoch_continuity(data):
		push_error("ENFORCEMENT: Epoch verification failed")
		_request_next_snapshot()
		return
	
	# 7. Process Content
	var snapshot = data.get("payload", {})
	last_snapshot = snapshot
	
	if rendering_paused:
		print("ZWRuntime: Snapshot received but rendering paused")
		_request_next_snapshot()
		return
	
	current_snapshot = snapshot
	state_updated.emit(current_snapshot)
	_request_next_snapshot()

# ============================================================
# USAGE INSTRUCTIONS
# ============================================================

# 1. Add the three verification functions (_verify_snapshot_hash, 
#    _verify_protocol_version, _verify_epoch_continuity) to ZWRuntime.gd

# 2. Add the constants (EXPECTED_PROTOCOL, EXPECTED_VERSION) near top of file

# 3. Add epoch tracking variables (current_epoch, epoch_changes) near top of file

# 4. Replace the _on_snapshot_completed function with the version above

# This adds three enforcement layers:
#   - Version checking (prevents drift)
#   - Hash verification (detects corruption)
#   - Epoch tracking (detects world resets)
