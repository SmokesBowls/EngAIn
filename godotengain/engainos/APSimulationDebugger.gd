extends Node

var http_request: HTTPRequest

func _ready():
    http_request = HTTPRequest.new()
    add_child(http_request)
    http_request.request_completed.connect(_on_request_completed)
    
    # Run simulation automatically every 2 seconds for the heatmap effect
    var timer = Timer.new()
    timer.wait_time = 2.0
    timer.autostart = true
    timer.timeout.connect(run_ap_simulation)
    add_child(timer)
    
    print("[AP Debugger] Ready. Polling simulation every 2s...")

func run_ap_simulation():
    var body = {
        "type": "ap_simulate_tick",
        "context": {
            "player": "player"
        }
    }

    var url = "http://127.0.0.1:8765/ap_simulate_tick"
    var headers = ["Content-Type: application/json"]
    
    http_request.request(url, headers, HTTPClient.METHOD_POST, JSON.stringify(body))

func _on_request_completed(_result, response_code, _headers, body):
    if response_code != 200:
        print("[AP Debugger] Error: Server returned ", response_code)
        return

    var json = JSON.new()
    var error = json.parse(body.get_string_from_utf8())
    if error != OK:
        print("[AP Debugger] Error parsing JSON")
        return
        
    var data = json.get_data()
    visualize_ap_result(data)

func visualize_ap_result(sim: Dictionary):
    var would_apply = sim.get("would_apply", [])
    var would_block = sim.get("would_block", [])
    var explanations = sim.get("explanations", {})

    for cube in get_tree().get_nodes_in_group("ap_cubes"):
        # Match by rule_id or fallback to entity_id if rule_id is empty
        var rid = cube.rule_id
        if rid == "":
            # Try to guess rule_id from entity_id (e.g. key -> unknown_pickup_key)
            # This is a temporary hack for the demo
            if cube.entity_id == "key": rid = "unknown_pickup_key"
            elif cube.entity_id == "door": rid = "unknown_unlock_door"

        if rid in would_apply:
            cube.set_color(Color.GREEN)
        elif rid in would_block:
            cube.set_color(Color.RED)
            var expl = explanations.get(rid, {})
            var blocked_by = expl.get("blocked_by", [])
            if blocked_by.size() > 0:
                cube.show_reason(blocked_by[0])
        else:
            cube.set_color(Color.GRAY)
