# ap_test_simple.gd
# Attach this to TestBridge node
# Press SPACEBAR to query AP and change cube color

extends Node

const RUNTIME_URL = "http://127.0.0.1:8765"

var http: HTTPRequest
var cube: MeshInstance3D

func _ready():
	# Find the cube in the scene
	cube = get_node_or_null("../MeshInstance3D")
	if not cube:
		print("[AP Test] ERROR: Can't find MeshInstance3D!")
		return
	
	# Setup HTTP
	http = HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(_on_request_completed)
	
	print("\n========================================")
	print("AP SIMPLE TEST READY")
	print("========================================")
	print("Press SPACEBAR to query AP engine")
	print("Cube will change color based on result:")
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
		set_cube_color(Color.MAGENTA)
		return
	
	var json = JSON.new()
	var parse_result = json.parse(body.get_string_from_utf8())
	
	if parse_result != OK:
		print("[AP Test] ERROR: Invalid JSON")
		set_cube_color(Color.MAGENTA)
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
		print("Color: GREEN")
		set_cube_color(Color.GREEN)
	else:
		print("Status: ✗ RULE BLOCKED")
		print("Color: RED")
		
		var blocked = data.get("blocked_by", [])
		if blocked.size() > 0:
			print("Reason: ", blocked[0])
		
		set_cube_color(Color.RED)
	
	print("========================================\n")

func set_cube_color(color: Color):
	if not cube:
		return
	
	# Force material update on main thread
	call_deferred("_update_cube_material", color)

func _update_cube_material(color: Color):
	var material = StandardMaterial3D.new()
	material.albedo_color = color
	material.emission_enabled = true
	material.emission = color * 0.5
	material.emission_energy = 2.0
	
	cube.set_surface_override_material(0, material)
	
	print("Cube color ACTUALLY changed to: ", color)
	print("Material applied: ", cube.get_surface_override_material(0) != null)
