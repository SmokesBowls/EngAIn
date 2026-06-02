class_name SceneTransitionBouncer
extends Node

# State Machine States
enum State {
	IDLE,
	SCENE_REQUESTED,
	SERVER_COMMITTED,
	TERRAIN_LAYOUT_READY,
	TERRAIN_LOCKED_VISIBLE,
	SNAPSHOT_SYNCED,
	ENTITY_PASS_ATTEMPTED,
	SCENE_READY,
	FAILED
}

# Stage signals returned by gate_passed()
signal server_committed_passed()
signal terrain_layout_ready_passed()
signal terrain_locked_visible_passed()
signal snapshot_synced_passed()
signal entity_pass_attempted_passed()
signal scene_ready_passed()

# Retry/Failure signals
signal retry_requested()
signal transition_failed()

# Internal configuration
@export var max_retries: int = 15

# State Variables
var current_state: State = State.IDLE
var expected_scene_id: String = ""
var active_transition_token: int = 0
var retries: int = 0
var _layout_pending: bool = false

func request_load(target_scene_id: String) -> int:
	active_transition_token += 1
	expected_scene_id = target_scene_id
	retries = 0
	_layout_pending = false
	_transition_to(State.SCENE_REQUESTED)
	print("[Bouncer] New load requested. expected_scene_id=", expected_scene_id, " token=", active_transition_token)
	return active_transition_token

func commit_server(scene_id: String, token: int) -> bool:
	var success = _try_transition(State.SERVER_COMMITTED, scene_id, token)
	if success:
		server_committed_passed.emit()
		if _layout_pending:
			print("[Bouncer] Pending layout found. Transitioning to TERRAIN_LAYOUT_READY.")
			_layout_pending = false
			_transition_to(State.TERRAIN_LAYOUT_READY)
			terrain_layout_ready_passed.emit()
	return success

func layout_ready(scene_id: String, token: int) -> bool:
	if token != active_transition_token:
		print("[Bouncer] Rejecting stale layout callback. expected_token=", active_transition_token, " got=", token)
		return false
	if scene_id != expected_scene_id:
		print("[Bouncer] Layout scene mismatch.")
		return false
	
	if current_state == State.SCENE_REQUESTED:
		_layout_pending = true
		print("[Bouncer] Layout ready received, waiting for server commit.")
		return true
	
	var success = _try_transition(State.TERRAIN_LAYOUT_READY, scene_id, token)
	if success:
		terrain_layout_ready_passed.emit()
	return success

func terrain_locked_visible(scene_id: String, token: int) -> bool:
	var success = _try_transition(State.TERRAIN_LOCKED_VISIBLE, scene_id, token)
	if success:
		terrain_locked_visible_passed.emit()
	return success

func snapshot_synced(scene_id: String, token: int) -> bool:
	var success = _try_transition(State.SNAPSHOT_SYNCED, scene_id, token)
	if success:
		snapshot_synced_passed.emit()
	return success

func entity_pass_attempted(scene_id: String, token: int) -> bool:
	var success = _try_transition(State.ENTITY_PASS_ATTEMPTED, scene_id, token)
	if success:
		entity_pass_attempted_passed.emit()
	return success

func scene_ready(scene_id: String, token: int) -> bool:
	var success = _try_transition(State.SCENE_READY, scene_id, token)
	if success:
		scene_ready_passed.emit()
	return success

func gate_passed(stage_name: String) -> Signal:
	match stage_name:
		"SERVER_COMMITTED":
			return server_committed_passed
		"TERRAIN_LAYOUT_READY":
			return terrain_layout_ready_passed
		"TERRAIN_LOCKED_VISIBLE":
			return terrain_locked_visible_passed
		"SNAPSHOT_SYNCED":
			return snapshot_synced_passed
		"ENTITY_PASS_ATTEMPTED":
			return entity_pass_attempted_passed
		"SCENE_READY":
			return scene_ready_passed
		_:
			push_error("[Bouncer] Unknown gate: ", stage_name)
			return terrain_layout_ready_passed

func _try_transition(next_state: State, scene_id: String, token: int) -> bool:
	# 1. Token mismatch checks
	if token != active_transition_token:
		print("[Bouncer] Rejecting stale callback. expected_token=", active_transition_token, " got=", token)
		return false

	# 2. Scene validation checks
	if scene_id != expected_scene_id:
		retries += 1
		if retries > max_retries:
			print("[Bouncer] Scene mismatch: max retries reached. Transition FAILED. expected=", expected_scene_id, " got=", scene_id)
			_transition_to(State.FAILED)
			transition_failed.emit()
		else:
			print("[Bouncer] Scene mismatch: retrying fetch (", retries, "/", max_retries, ") expected=", expected_scene_id, " got=", scene_id)
			retry_requested.emit()
		return false

	# 3. Stage regression / invalid state progression checks
	if not _is_valid_transition(current_state, next_state):
		print("[Bouncer] Stage regression / invalid progression: cannot transition from State ", current_state, " to State ", next_state, ". Transition FAILED.")
		_transition_to(State.FAILED)
		transition_failed.emit()
		return false

	_transition_to(next_state)
	return true

func _is_valid_transition(from_state: State, to_state: State) -> bool:
	if to_state == State.SCENE_REQUESTED or to_state == State.FAILED:
		return true
	
	match to_state:
		State.SERVER_COMMITTED:
			return from_state == State.SCENE_REQUESTED
		State.TERRAIN_LAYOUT_READY:
			return from_state == State.SERVER_COMMITTED or from_state == State.SCENE_REQUESTED
		State.TERRAIN_LOCKED_VISIBLE:
			return from_state == State.TERRAIN_LAYOUT_READY
		State.SNAPSHOT_SYNCED:
			return from_state == State.TERRAIN_LOCKED_VISIBLE
		State.ENTITY_PASS_ATTEMPTED:
			return from_state == State.SNAPSHOT_SYNCED
		State.SCENE_READY:
			return from_state == State.ENTITY_PASS_ATTEMPTED or from_state == State.SNAPSHOT_SYNCED
	return false

func _transition_to(next_state: State) -> void:
	print("[Bouncer] State change: ", current_state, " → ", next_state)
	current_state = next_state
