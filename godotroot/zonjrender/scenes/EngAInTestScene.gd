extends Node3D
## EngAInTestScene.gd — Drop-in test scene
## Attach to root Node3D of your test scene.
## Creates camera, light, renderer, and keyboard controls.
##
## Keys:
##   1-5  = Load scene.01 through scene.05
##   L    = Load scene.04_the_convergence (29 entities)
##   C    = Clear all spawned entities
##   S    = Print status
##   V    = Link vault (edit path below)

@export var vault_root: String = "/home/burdens/obsidian/obsidianburdenNov25"
@export var manifest_path: String = "/home/burdens/obsidian/obsidianburdenNov25/vault.manifest.json"

var _renderer: Node3D
var _status_label: Label


func _ready() -> void:
	# Camera
	var cam := Camera3D.new()
	cam.position = Vector3(15, 12, 25)
	cam.look_at(Vector3(15, 0, 0))
	cam.fov = 60
	add_child(cam)

	# Light
	var light := DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-45, -30, 0)
	add_child(light)

	# Ambient
	var env := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.12, 0.12, 0.15)
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(0.3, 0.3, 0.35)
	env.environment = environment
	add_child(env)

	# Ground plane
	var ground := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(80, 40)
	ground.mesh = plane
	var ground_mat := StandardMaterial3D.new()
	ground_mat.albedo_color = Color(0.15, 0.18, 0.15)
	ground.material_override = ground_mat
	add_child(ground)

	# SemanticRenderer
	var renderer_script = load("res://SemanticRenderer.gd")
	if renderer_script:
		_renderer = Node3D.new()
		_renderer.set_script(renderer_script)
		_renderer.name = "SemanticRenderer"
		add_child(_renderer)
		print("[TestScene] SemanticRenderer attached")
	else:
		push_error("[TestScene] SemanticRenderer.gd not found at res://")

	# HUD
	var canvas := CanvasLayer.new()
	add_child(canvas)
	_status_label = Label.new()
	_status_label.position = Vector2(10, 10)
	_status_label.add_theme_font_size_override("font_size", 16)
	_status_label.add_theme_color_override("font_color", Color.WHITE)
	canvas.add_child(_status_label)

	var help := Label.new()
	help.position = Vector2(10, 40)
	help.add_theme_font_size_override("font_size", 14)
	help.add_theme_color_override("font_color", Color(0.6, 0.6, 0.6))
	help.text = "L=load ch4  1-5=load scene  V=vault  C=clear  S=status"
	canvas.add_child(help)


func _process(_delta: float) -> void:
	if _renderer and _renderer.has_method("get_status"):
		var s: Dictionary = _renderer.get_status()
		_status_label.text = "EngAIn | %s | %s | %d entities" % [
			"CONNECTED" if s.get("connected", false) else "DISCONNECTED",
			s.get("scene", "no scene"),
			s.get("managed", 0),
		]


func _unhandled_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed:
		return

	var client = _get_client()

	match event.keycode:
		KEY_L:
			if client: client.load_scene("scene.04_the_convergence")
		KEY_1:
			if client: client.load_scene("scene.01_the_awakening")
		KEY_2:
			if client: client.load_scene("scene.02_first_light")
		KEY_3:
			if client: client.load_scene("scene.03_the_crossing")
		KEY_4:
			if client: client.load_scene("scene.04_the_convergence")
		KEY_5:
			if client: client.load_scene("scene.05_the_gathering")
		KEY_V:
			if client: client.link_vault(vault_root, manifest_path)
		KEY_C:
			if _renderer and _renderer.has_method("clear_all"):
				_renderer.clear_all()
				print("[TestScene] Cleared all entities")
		KEY_S:
			_print_status()


func _get_client():
	if Engine.has_singleton("EngAInClient"):
		return Engine.get_singleton("EngAInClient")
	if has_node("/root/EngAInClient"):
		return get_node("/root/EngAInClient")
	# Fallback: create inline
	return null


func _print_status() -> void:
	if _renderer and _renderer.has_method("get_status"):
		var s = _renderer.get_status()
		print("=== EngAIn Status ===")
		print("  Connected: %s" % s.get("connected", false))
		print("  Scene: %s" % s.get("scene", "none"))
		print("  Entities: %d" % s.get("managed", 0))
		print("  Errors: %d" % s.get("errors", 0))
	if _renderer and _renderer.has_method("get_all_entities"):
		var ents = _renderer.get_all_entities()
		for eid in ents:
			var node: Node3D = ents[eid]
			print("    %s @ %s  type=%s" % [
				eid, node.position,
				node.get_meta("entity_type", "?")
			])
