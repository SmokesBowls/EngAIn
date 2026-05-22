extends SceneTree

func _init():
    var main = load("res://Main.gd").new()
    main._ready()
    quit()
