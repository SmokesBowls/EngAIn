extends Node3D

const SNAPSHOT_FILE := "/tmp/engain_snapshot.json"

var entities := {}

func _ready():
    print("============================================================")
    print("ENGAIN FILE-BASED TEST CLIENT (Godot 4)")
    print("============================================================")
    print("Make sure Python runtime is running:")
    print("  python3 sim_runtime_file_test.py")
    print("\nControls:")
    print("  SPACE  - Enemy attacks Guard (25 dmg)")
    print("  ENTER  - Guard attacks Enemy (15 dmg)")
    print("  1      - Enemy heavy attack (80 dmg)")
    print("  2      - Guard heavy attack (50 dmg)")
    print("  Q      - Quit")
    print("============================================================")

func _process(delta):
    var snapshot = load_snapshot()
    if snapshot == null:
        return

    if not snapshot.has("entities"):
        return

    for entity_id in snapshot["entities"].keys():
        var data = snapshot["entities"][entity_id]

        if not entities.has(entity_id):
            var cube = MeshInstance3D.new()
            cube.mesh = BoxMesh.new()       # <-- FIXED FOR GODOT 4
            cube.scale = Vector3(data["radius"], data["radius"], data["radius"])
            add_child(cube)
            entities[entity_id] = cube

        var node = entities[entity_id]
        var pos = data["pos"]
        node.position = Vector3(pos[0], pos[1], pos[2])

        var health = data["health"]
        var max_health = data["max_health"]
        var alive = data["alive"]

        if not alive:
            node.modulate = Color.BLACK
        elif health < max_health * 0.3:
            node.modulate = Color.RED
        elif health < max_health * 0.6:
            node.modulate = Color.YELLOW
        else:
            node.modulate = Color.GREEN


func load_snapshot():
    if not FileAccess.file_exists(SNAPSHOT_FILE):
        return null

    var f := FileAccess.open(SNAPSHOT_FILE, FileAccess.READ)
    if f == null:
        return null

    var text := f.get_as_text()
    f.close()

    if text.length() < 10:
        return null

    var parsed = JSON.parse_string(text)
    if typeof(parsed) != TYPE_DICTIONARY:
        return null

    return parsed
