# ap_test_direct.gd
# Attach this to TestBridge node
# Press SPACEBAR to query AP and change cube color
# This version modifies the material directly

extends Node

const RUNTIME_URL = "http://127.0.0.1:8765"

var http: HTTPRequest
var cube: MeshInstance3D
var original_material: Material

func _ready():
	# Find the cube in the scene
	cube = get_node_or_null("../MeshInstance3D")
	if not cube:
		print("[AP Test] ERROR: Can't find MeshInstance3D!")
		return
	
	# Store original material
	original_material = cube.get_active_material(0)
	
	# Setup HTTP
	http = HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(_on_request_completed)
	
	print("\n========================================")
	print("AP DIRECT TEST READY")
	print("========================================")
	print("Press SPACEBAR to query AP engine")
	print("Cube will change color:")
	print("  GREEN = Rule can fire")
	print("  RED = Rule blocked")
	print("========================================\n")

func _input(event):
	if event is InputEventKey and event.pressed and event.keycode == KEY_SPACE:
		print("\n[AP Test] Querying engine...")
		query_ap()

func query_ap():
	var msg = {
		"type": "ap_evaluate_rule",
		"rule_id": "unknown_pickup_key",
		"context": {"player": "player"}
	}
	
	var json_string = JSON.stringify(msg)
	var headers = ["Content-Type: application/json"]
	
	http.request(RUNTIME_URL, headers, HTTPClient.METHOD_POST, json_string)

func _on_request_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
	if response_code != 200:
		print("[AP Test] ERROR: Response code ", response_code)
		flash_cube(Color.MAGENTA)
		return
	
	var json = JSON.new()
	var parse_result = json.parse(body.get_string_from_utf8())
	
	if parse_result != OK:
		print("[AP Test] ERROR: Invalid JSON")
		flash_cube(Color.MAGENTA)
		return
	
	var data = json.data
	var eligible = data.get("eligible", false)
	
	print("\n========================================")
	print("AP ENGINE RESPONSE:")
	print("========================================")
	print("Rule: unknown_pickup_key")
	print("Eligible: ", eligible)
	
	if eligible:
		print("Status: ✓ RULE CAN FIRE")
		flash_cube(Color.GREEN)
	else:
		print("Status: ✗ RULE BLOCKED")
		var blocked = data.get("blocked_by", [])
		if blocked.size() > 0:
			print("Reason: ", blocked[0])
		flash_cube(Color.RED)
	
	print("========================================\n")

func flash_cube(color: Color):
	# Create a completely new material
	var mat = StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = color
	
	# Apply it
	cube.set_surface_override_material(0, mat)
	
	print(">>> CUBE COLOR SET TO: ", color)
	
	# Flash back after 2 seconds
	await get_tree().create_timer(2.0).timeout
	
	# Reset to original
	cube.set_surface_override_material(0, null)
	print(">>> Cube reset to original color")
