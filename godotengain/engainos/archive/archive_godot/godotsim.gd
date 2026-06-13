extends Node
class_name SimConnector

# Pointing to your running godotsim
const SIM_URL = "http://localhost:8080" 
var http_request : HTTPRequest

func _ready():
    # Create the nervous system node
    http_request = HTTPRequest.new()
    add_child(http_request)
    http_request.request_completed.connect(_on_request_completed)
    
    # Trigger the first signal!
    print("🔌 Attempting to handshake with EngAIn Sim...")
    fetch_inventory()

func fetch_inventory():
    # Assuming your sim has a basic GET endpoint for state or debug
    # If not, we might need to hit the root "/" or a specific "/inventory" endpoint
    # Based on your logs, it registered entities, so let's try to get the world state.
    var error = http_request.request(SIM_URL + "/state") # Or try "/" if uncertain
    if error != OK:
        print("❌ An error occurred in the HTTP request.")

func _on_request_completed(result, response_code, headers, body):
    if response_code == 200:
        var json = JSON.new()
        var parse_result = json.parse(body.get_string_from_utf8())
        
        if parse_result == OK:
            var data = json.get_data()
            print("✅ CONNECTION ESTABLISHED!")
            print("📦 SIM INVENTORY RECEIVED:")
            # Modify this path based on the actual JSON structure coming back
            if data.has("inventory"):
                print(data["inventory"])
            else:
                print(data) # Just dump whatever the brain is thinking
        else:
            print("⚠️ JSON Parse Error: ", json.get_error_message())
    else:
        print("❌ Server refused connection. Code: ", response_code)