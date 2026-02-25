# ap_clickable_cube.gd
# Attach this to MeshInstance3D node (the purple cube)
# Click the cube to query AP and see it change color

extends MeshInstance3D

const RUNTIME_URL = "http://127.0.0.1:8765"

# Which rule this cube represents
@export var rule_id: String = "unknown_pickup_key"

var http: HTTPRequest

func _ready():
	# Make it clickable
	var static_body = StaticBody3D.new()
	add_child(static_body)
	
	var collision = CollisionShape3D.new()
	var shape = BoxShape3D.new()
	shape.size = Vector3(1, 1, 1)
	collision.shape = shape
	static_body.add_child(collision)
	
	# Setup HTTP
	http = HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(_on_request_completed)
	
	print("[Cube] Ready - click me to test AP! (rule: ", rule_id, ")")

func _input_event(camera, event, position, normal, shape_idx):
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		print("\n[Cube] Clicked! Asking AP about rule: ", rule_id)
		query_ap()

func query_ap():
	var msg = {
		"type": "ap_evaluate_rule",
		"rule_id": rule_id,
		"context": {"player": "player"}
	}
	
	var json_string = JSON.stringify(msg)
	var headers = ["Content-Type: application/json"]
	
	http.request(RUNTIME_URL, headers, HTTPClient.METHOD_POST, json_string)

func _on_request_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
	if response_code != 200:
		print("[Cube] ERROR: Response code ", response_code)
		set_color(Color.MAGENTA)  # Error = magenta
		return
	
	var json = JSON.new()
	var parse_result = json.parse(body.get_string_from_utf8())
	
	if parse_result != OK:
		print("[Cube] ERROR: Invalid JSON")
		set_color(Color.MAGENTA)
		return
	
	var data = json.data
	var eligible = data.get("eligible", false)
	
	print("[Cube] AP Response:")
	print("  Eligible: ", eligible)
	print("  Blocked by: ", data.get("blocked_by", []))
	
	if eligible:
		set_color(Color.GREEN)
		print("  ✓ RULE CAN FIRE")
	else:
		set_color(Color.RED)
		print("  ✗ RULE BLOCKED")
		
		# Show why
		var blocked = data.get("blocked_by", [])
		if blocked.size() > 0:
			print("  Reason: ", blocked[0])

func set_color(color: Color):
	var material = StandardMaterial3D.new()
	material.albedo_color = color
	material.emission_enabled = true
	material.emission = color * 0.3  # Make it glow
	set_surface_override_material(0, material)
