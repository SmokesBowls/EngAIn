extends SceneTree

func _init():
    var file := FileAccess.open("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/.engain_cache/parsed/scenes/scene_index.json", FileAccess.READ)
    var json := JSON.new()
    json.parse(file.get_as_text())
    var data = json.data
    var loaded = 0
    if typeof(data) == TYPE_DICTIONARY and data.has("active_scenes"):
        for entry in data["active_scenes"]:
            var sid = str(entry.get("scene_id", ""))
            var path = str(entry.get("cache_file", ""))
            if sid.is_empty() or path.is_empty():
                continue
            loaded += 1
    print("Loaded: ", loaded)
    quit()
