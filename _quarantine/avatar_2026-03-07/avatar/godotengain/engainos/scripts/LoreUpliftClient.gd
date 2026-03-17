extends Node
class_name LoreUpliftClient

# Pointing to our new Lore endpoint in engainos_server.py
# (Usually runs on port 8000 for FastAPI)
const SERVER_URL = "http://localhost:8000/api/lore/uplift"

signal uplift_started(chapter_id)
signal uplift_completed(data)
signal visual_op_received(action, params)

var http : HTTPRequest

func _ready():
    http = HTTPRequest.new()
    add_child(http)
    http.request_completed.connect(_on_uplift_response)
    print("📜 LoreUpliftClient: System Ready. Standing by for Narrative Input.")

func uplift_text(text: String, chapter_id: String = "unknown"):
    print("📜 LoreUpliftClient: Uplifting Chapter: ", chapter_id)
    emit_signal("uplift_started", chapter_id)
    
    var payload = {
        "text": text,
        "chapter_id": chapter_id,
        "apply_to_runtime": true
    }
    
    var json_payload = JSON.stringify(payload)
    var headers = ["Content-Type: application/json"]
    
    var err = http.request(SERVER_URL, headers, HTTPClient.METHOD_POST, json_payload)
    if err != OK:
        print("❌ LoreUpliftClient: Request failed to start.")

func _on_uplift_response(result, response_code, headers, body):
    if response_code == 200:
        var json = JSON.new()
        var parse_err = json.parse(body.get_string_from_utf8())
        if parse_err == OK:
            var data = json.get_data()
            print("✅ LoreUpliftClient: Uplift Successful. Processing Visual Ops...")
            _process_visual_ops(data.get("visual_ops", []))
            emit_signal("uplift_completed", data)
        else:
            print("⚠️ LoreUpliftClient: JSON Parse Error: ", json.get_error_message())
    else:
        print("❌ LoreUpliftClient: Server error code: ", response_code)

func _process_visual_ops(ops: Array):
    for op in ops:
        var action = op.get("action", "")
        var params = op.get("params", {})
        print("  🎥 Visual Op: ", action)
        emit_signal("visual_op_received", action, params)
        
        # Example: Automatic handling of known visual actions
        if action == "emit_vfx":
            _handle_vfx(params)
        elif action == "set_gravity_scale":
            _handle_gravity(op.get("value", 1.0))

func _handle_vfx(params: Dictionary):
    var vfx_id = params.get("id", "generic")
    print("     [VFX] Spawning effect: ", vfx_id)
    # This is where you'd instance a particle effect if you knew how, 
    # but for now, we just log it as a successful engine signal!

func _handle_gravity(value: float):
    print("     [GRAVITY] Setting world gravity to: ", value)
    # If the user has a PhysicsStack, it would update here
