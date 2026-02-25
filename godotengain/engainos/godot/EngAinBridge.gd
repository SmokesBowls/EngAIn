extends Node

func _ready():
	var http = HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(_on_data_received)
	
	# 🎯 This is the specific endpoint we found in your code
	print("Connecting to EngAIn Brain...")
	http.request("http://localhost:8080/snapshot")

func _on_data_received(result, code, headers, body):
	if code == 200:
		var json = JSON.parse_string(body.get_string_from_utf8())
		# The inventory is hidden inside the "payload" envelope
		print("🎒 INVENTORY RECEIVED: ", json.payload.inventory)
	else:
		print("❌ Connection Failed: ", code)
