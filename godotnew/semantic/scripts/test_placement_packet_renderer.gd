extends SceneTree

const PLACEMENT_RENDERER_SCRIPT := preload("res://scripts/PlacementPacketRenderer.gd")


func _initialize() -> void:
	var renderer := PLACEMENT_RENDERER_SCRIPT.new()
	if renderer == null:
		push_error("[PLACEMENT_RENDER_TEST] Failed to instantiate PlacementPacketRenderer")
		quit(1)
		return

	var root := Node3D.new()
	root.name = "PlacementPacketRenderTestRoot"
	root.add_child(renderer)
	get_root().add_child(root)

	var abs_repo_root := ProjectSettings.globalize_path("res://../../")
	var packet_path := abs_repo_root.path_join("tests/fixtures/placement_packets_sample.json")

	var loaded := renderer.load_packets_from_file(packet_path)
	if not loaded:
		push_error("[PLACEMENT_RENDER_TEST] load_packets_from_file failed: %s" % packet_path)
		quit(1)
		return

	var raw := FileAccess.get_file_as_string(packet_path)
	if raw.is_empty():
		push_error("[PLACEMENT_RENDER_TEST] Fixture file was empty or unreadable: %s" % packet_path)
		quit(1)
		return
	var parsed: Variant = JSON.parse_string(raw)
	if typeof(parsed) != TYPE_ARRAY:
		push_error("[PLACEMENT_RENDER_TEST] Fixture root JSON is not Array")
		quit(1)
		return

	var packets := parsed as Array
	if renderer.get_child_count() != packets.size():
		push_error("[PLACEMENT_RENDER_TEST] child_count mismatch: got %d expected %d" % [renderer.get_child_count(), packets.size()])
		quit(1)
		return

	var snap1 := renderer.snapshot_state()

	var loaded_again := renderer.load_packets_from_file(packet_path)
	if not loaded_again:
		push_error("[PLACEMENT_RENDER_TEST] second load failed")
		quit(1)
		return
	var snap2 := renderer.snapshot_state()

	if JSON.stringify(snap1, "") != JSON.stringify(snap2, ""):
		push_error("[PLACEMENT_RENDER_TEST] non-deterministic snapshot across identical reload")
		quit(1)
		return

	print("[PLACEMENT_RENDER_TEST] PASS")
	quit(0)
