extends SceneTree
func _init():
    var script = load("res://trixel/TrixelEnvironmentPlanner.gd")
    var runtime_scene_doc = {
        "file": {
            "path": {
                "source_path": "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/.engain_cache/parsed/scenes/002_molten_descent_with_semantics.zonj.json"
            }
        },
        "scene_id": "scene.002_molten_descent"
    }
    script.plan(runtime_scene_doc)
    quit()
