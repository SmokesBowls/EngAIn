# test_ap_connection.gd
# Minimal script to test AP connection from Godot
# 
# Add this as a new script to your TestBridge node or run standalone

extends Node

# Adjust to match your runtime server
const RUNTIME_URL = "http://127.0.0.1:8765"

func _ready():
	print("=== Testing AP Connection ===")
	test_ap_list_rules()

func test_ap_list_rules():
	"""Test basic AP connection by listing rules"""
	var http = HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(_on_list_rules_response)
	
	var msg = {
		"type": "ap_list_rules"
	}
	
	var json_string = JSON.stringify(msg)
	var headers = ["Content-Type: application/json"]
	
	print("[AP Test] Sending ap_list_rules request...")
	var error = http.request(RUNTIME_URL, headers, HTTPClient.METHOD_POST, json_string)
	
	if error != OK:
		print("[AP Test] ERROR: Failed to send request: ", error)

func _on_list_rules_response(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
	print("[AP Test] Response code: ", response_code)
	
	if response_code != 200:
		print("[AP Test] ERROR: Server returned ", response_code)
		return
	
	var json = JSON.new()
	var parse_result = json.parse(body.get_string_from_utf8())
	
	if parse_result != OK:
		print("[AP Test] ERROR: Failed to parse JSON")
		print("Raw response: ", body.get_string_from_utf8())
		return
	
	var data = json.data
	print("[AP Test] SUCCESS! Received response:")
	print("  Type: ", data.get("type", "unknown"))
	
	if data.has("rules"):
		var rules = data.get("rules", [])
		print("  Rules count: ", rules.size())
		print("  First 3 rules:")
		for i in min(3, rules.size()):
			var rule = rules[i]
			print("    - ", rule.get("id", "unknown"), " (priority: ", rule.get("priority", 0), ")")
	elif data.has("error"):
		print("  ERROR: ", data.get("error"))
	
	print("[AP Test] Connection test complete!")
	print("========================")


# ============================================================================
# HOW TO USE THIS TEST
# ============================================================================

"""
METHOD 1: Run from Godot Script tab
1. Open Godot
2. Create new script: test_ap_connection.gd
3. Copy this code
4. Attach to any node (or TestBridge)
5. Run scene - check output console

METHOD 2: Quick command line test
1. Make sure your runtime is running:
   cd /home/burdens/Downloads/EngAIn/godotengain/engainos
   python3 launch_engine.py
   
2. Test with curl:
   curl -X POST http://127.0.0.1:8765 \
     -H "Content-Type: application/json" \
     -d '{"type":"ap_list_rules"}'

Expected output:
{
  "type": "ap_rules_list",
  "rules": [
    {"id": "rule_1", "priority": 0, "tags": [], "write_set": []},
    ...
  ]
}

Or if AP not initialized:
{
  "error": "ap_not_initialized"
}

If you get this error, it means the runtime is working but AP needs to be integrated
per the AP_INTEGRATION_SNIPPET.py instructions.
"""
