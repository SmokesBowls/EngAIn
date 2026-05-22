extends SceneTree

func _init():
    var manifest_path := "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/manifests/engain_manifest.json"
    var mfile := FileAccess.open(manifest_path, FileAccess.READ)
    var mjson := JSON.new()
    mjson.parse(mfile.get_as_text())
    var manifest = mjson.data
    
    var active_lib = manifest.get("active", {}).get("scene_library", "")
    var index_path = manifest.get("scene_libraries", {}).get(active_lib, {}).get("index", "")
    print("INDEX PATH: ", index_path)
    
    var file := FileAccess.open(index_path, FileAccess.READ)
    if not file:
        print("FAILED TO OPEN FILE")
        quit()
        return

    var json := JSON.new()
    json.parse(file.get_as_text())
    var data = json.data
    print("DATA HAS ACTIVE SCENES: ", typeof(data) == TYPE_DICTIONARY and data.has("active_scenes"))
    print("SCENE COUNT: ", data.get("active_scenes", []).size())
    
    var loaded = 0
    for entry in data.get("active_scenes", []):
        var sid = str(entry.get("scene_id", ""))
        var path = str(entry.get("cache_file", ""))
        if sid.is_empty() or path.is_empty():
            print("SKIPPING: sid='", sid, "' path='", path, "'")
            continue
        loaded += 1
    print("LOADED: ", loaded)
    
    quit()
