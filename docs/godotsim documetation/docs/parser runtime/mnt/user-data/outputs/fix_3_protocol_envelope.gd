# FIX 3: PROTOCOL ENVELOPE VALIDATION
# Survivable Transport Layer

extends Node

"""
PROBLEM: HTTP transport lacks integrity guarantees
- No versioning (server/client mismatch undetected)
- No tick validation (out-of-order packets accepted)
- No hash verification (corruption goes unnoticed)

RESULT: Silent drift, impossible deterministic replay

SOLUTION: Mandatory protocol envelope with hard rejection
"""

# =============================================================================
# PROTOCOL ENVELOPE SPECIFICATION
# =============================================================================

const PROTOCOL_VERSION = "1.0.0"  # Semantic versioning
const COMPATIBLE_VERSIONS = ["1.0.0", "1.0.1"]  # Backwards compat list

# Envelope fields (MANDATORY)
const REQUIRED_ENVELOPE_FIELDS = [
	"version",      # Protocol version (semver)
	"tick",         # Server tick number
	"epoch",        # Session/world epoch identifier  
	"content_hash"  # SHA256 of content for integrity
]

# Validation state
var last_accepted_tick = -1
var current_epoch = ""
var validation_stats = {
	"total_received": 0,
	"accepted": 0,
	"rejected_version": 0,
	"rejected_tick": 0,
	"rejected_hash": 0,
	"rejected_missing_fields": 0
}

# =============================================================================
# ENVELOPE VALIDATION - Hard Rejection Logic
# =============================================================================

func validate_and_unwrap_envelope(raw_snapshot: Dictionary) -> Dictionary:
	"""
	Validate protocol envelope and extract payload
	
	Returns:
		{success: bool, payload: Dictionary, error: String}
	
	On failure: Triggers pusher, halts state propagation
	"""
	
	validation_stats.total_received += 1
	
	# STEP 1: Check envelope presence
	var missing_fields = []
	for field in REQUIRED_ENVELOPE_FIELDS:
		if not raw_snapshot.has(field):
			missing_fields.append(field)
	
	if missing_fields.size() > 0:
		validation_stats.rejected_missing_fields += 1
		return _reject_snapshot(
			"MISSING_ENVELOPE_FIELDS",
			"Required fields missing: %s" % str(missing_fields)
		)
	
	# STEP 2: Version compatibility check
	var received_version = raw_snapshot.version
	
	if not _is_version_compatible(received_version):
		validation_stats.rejected_version += 1
		return _reject_snapshot(
			"INCOMPATIBLE_VERSION",
			"Received v%s, compatible: %s" % [received_version, str(COMPATIBLE_VERSIONS)]
		)
	
	# STEP 3: Epoch consistency
	var received_epoch = raw_snapshot.epoch
	
	if current_epoch == "":
		# First snapshot - establish epoch
		current_epoch = received_epoch
		print("[ENVELOPE] Epoch established: ", current_epoch)
	elif current_epoch != received_epoch:
		# Epoch mismatch - possible server restart or world change
		push_warning("EPOCH MISMATCH: %s != %s (server restart?)" % [received_epoch, current_epoch])
		current_epoch = received_epoch
		last_accepted_tick = -1  # Reset tick tracking
	
	# STEP 4: Tick ordering validation
	var received_tick = raw_snapshot.tick
	
	if received_tick <= last_accepted_tick:
		validation_stats.rejected_tick += 1
		return _reject_snapshot(
			"OUT_OF_ORDER_TICK",
			"Received tick %d <= last accepted %d" % [received_tick, last_accepted_tick]
		)
	
	# STEP 5: Content hash verification (END-TO-END INTEGRITY)
	var received_hash = raw_snapshot.content_hash
	var payload = raw_snapshot.get("payload", {})
	
	var calculated_hash = _calculate_content_hash(payload)
	
	if calculated_hash != received_hash:
		validation_stats.rejected_hash += 1
		return _reject_snapshot(
			"HASH_MISMATCH",
			"Calculated %s != received %s (CORRUPTION DETECTED)" % [calculated_hash, received_hash]
		)
	
	# ALL CHECKS PASSED - Accept snapshot
	last_accepted_tick = received_tick
	validation_stats.accepted += 1
	
	return {
		"success": true,
		"payload": payload,
		"tick": received_tick,
		"version": received_version,
		"error": ""
	}


func _is_version_compatible(version: String) -> bool:
	"""Check if version is in compatible list"""
	return version in COMPATIBLE_VERSIONS


func _calculate_content_hash(content: Dictionary) -> String:
	"""
	Calculate SHA256 hash of content
	
	Application-level integrity guarantee:
	- Validates from source to destination
	- Not just network layer checksum
	"""
	
	var json_string = JSON.stringify(content)
	var hash = json_string.sha256_text()
	
	return hash


func _reject_snapshot(error_code: String, error_message: String) -> Dictionary:
	"""
	Hard rejection - stop state propagation
	
	Critical: Corrupt data MUST NOT leak into game state
	"""
	
	push_error("[ENVELOPE VIOLATION] %s: %s" % [error_code, error_message])
	
	# Could trigger additional safety measures:
	# - Request snapshot resend
	# - Enter safe mode
	# - Log to telemetry
	
	return {
		"success": false,
		"payload": {},
		"error": error_message
	}


# =============================================================================
# SIGNAL-DRIVEN POLLING - Eliminate Request Overlap
# =============================================================================

var _http_request: HTTPRequest
var _snapshot_request_in_flight = false
var _server_url = "http://localhost:8000/snapshot"

func _ready():
	"""Initialize signal-driven polling"""
	
	_http_request = HTTPRequest.new()
	add_child(_http_request)
	
	# CRITICAL: Signal-driven, not time-based
	_http_request.request_completed.connect(_on_snapshot_completed)
	
	# Start polling loop
	_request_next_snapshot()


func _request_next_snapshot():
	"""
	Request next snapshot - ONLY if no request in flight
	
	Eliminates overlap errors completely
	"""
	
	if _snapshot_request_in_flight:
		push_warning("Snapshot request already in flight - skipping")
		return
	
	_snapshot_request_in_flight = true
	
	var error = _http_request.request(_server_url)
	
	if error != OK:
		push_error("HTTP request failed: ", error)
		_snapshot_request_in_flight = false


func _on_snapshot_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
	"""
	Snapshot received - validate envelope, then request next
	
	ADAPTIVE POLLING: Next request only after current completes
	Client naturally adapts to server performance
	"""
	
	_snapshot_request_in_flight = false
	
	if result != HTTPRequest.RESULT_SUCCESS:
		push_error("HTTP request failed with result: ", result)
		# Wait before retry
		await get_tree().create_timer(1.0).timeout
		_request_next_snapshot()
		return
	
	if response_code != 200:
		push_error("HTTP response code: ", response_code)
		await get_tree().create_timer(1.0).timeout
		_request_next_snapshot()
		return
	
	# Parse JSON
	var json = JSON.new()
	var parse_result = json.parse(body.get_string_from_utf8())
	
	if parse_result != OK:
		push_error("JSON parse failed")
		_request_next_snapshot()
		return
	
	var raw_snapshot = json.data
	
	# VALIDATE ENVELOPE (Critical)
	var validation_result = validate_and_unwrap_envelope(raw_snapshot)
	
	if not validation_result.success:
		# HARD REJECTION - Do not propagate corrupt state
		push_error("Snapshot rejected: ", validation_result.error)
		
		# Request next snapshot (skip corrupted one)
		_request_next_snapshot()
		return
	
	# Envelope valid - propagate to game state
	var payload = validation_result.payload
	var tick = validation_result.tick
	
	_process_validated_snapshot(payload, tick)
	
	# Request next snapshot (signal-driven polling)
	_request_next_snapshot()


func _process_validated_snapshot(payload: Dictionary, tick: int):
	"""
	Process snapshot AFTER envelope validation
	
	At this point, we GUARANTEE:
	- Version compatible
	- Tick ordering correct
	- Content hash verified
	- No corruption
	"""
	
	# Your existing snapshot processing logic here
	# e.g., update entity positions, etc.
	
	print("[SNAPSHOT] Tick %d accepted and applied" % tick)


# =============================================================================
# DIAGNOSTIC REPORTING
# =============================================================================

func get_validation_report() -> Dictionary:
	"""
	Get transport integrity statistics
	
	Use for monitoring and debugging
	"""
	
	var total = validation_stats.total_received
	var acceptance_rate = 0.0
	
	if total > 0:
		acceptance_rate = float(validation_stats.accepted) / float(total)
	
	return {
		"total_received": total,
		"accepted": validation_stats.accepted,
		"acceptance_rate": acceptance_rate,
		"rejections": {
			"version": validation_stats.rejected_version,
			"tick_order": validation_stats.rejected_tick,
			"hash_mismatch": validation_stats.rejected_hash,
			"missing_fields": validation_stats.rejected_missing_fields
		},
		"current_epoch": current_epoch,
		"last_accepted_tick": last_accepted_tick
	}


func print_validation_stats():
	"""Debug: Print validation statistics"""
	
	var report = get_validation_report()
	var separator = "============================================================"
	
	print(separator)
	print("PROTOCOL ENVELOPE VALIDATION STATS")
	print(separator)
	print("Total received:    ", report.total_received)
	print("Accepted:          ", report.accepted)
	print("Acceptance rate:   %.1f%%" % (report.acceptance_rate * 100))
	print("\nRejections:")
	print("  Version mismatch:  ", report.rejections.version)
	print("  Tick out-of-order: ", report.rejections.tick_order)
	print("  Hash mismatch:     ", report.rejections.hash_mismatch)
	print("  Missing fields:    ", report.rejections.missing_fields)
	print("\nCurrent state:")
	print("  Epoch:             ", report.current_epoch)
	print("  Last tick:         ", report.last_accepted_tick)
	print(separator)


# =============================================================================
# SERVER-SIDE ENVELOPE GENERATION (Python Example)
# =============================================================================

"""
Python server must generate envelope:

```python
import hashlib
import json
import time

def create_snapshot_envelope(payload: dict, tick: int, epoch: str) -> dict:
    # Calculate content hash
    content_json = json.dumps(payload, sort_keys=True)
    content_hash = hashlib.sha256(content_json.encode()).hexdigest()
    
    # Create envelope
    envelope = {
        "version": "1.0.0",
        "tick": tick,
        "epoch": epoch,
        "content_hash": content_hash,
        "payload": payload,
        "timestamp": time.time()  # Optional
    }
    
    return envelope

# Usage in HTTP handler
snapshot_payload = {
    "spatial3d": {
        "entities": {...}
    }
}

envelope = create_snapshot_envelope(snapshot_payload, current_tick, world_epoch)
return JSONResponse(envelope)
```

CRITICAL: Hash must be calculated EXACTLY same way on both sides
"""


# =============================================================================
# INTEGRATION NOTES
# =============================================================================

"""
USAGE:

1. Replace existing ZWRuntime polling:
   
   OLD:
   func _process(delta):
       if time_to_poll:
           http_request.request(url)
   
   NEW:
   # Signal-driven (see _ready() above)
   # Automatic adaptive polling

2. Server must send envelopes:
   
   See Python example above

3. Monitor validation:
   
   # Call periodically
   print_validation_stats()
   
   # Check acceptance rate
   var report = get_validation_report()
   if report.acceptance_rate < 0.95:
       push_warning("Low acceptance rate - investigate!")

GUARANTEES:

✓ Version compatibility enforced
✓ Tick ordering verified  
✓ End-to-end integrity (hash)
✓ No request overlap
✓ Adaptive polling rate
✓ Hard rejection on corruption

RESULT: Survivable Transport Architecture
"""
