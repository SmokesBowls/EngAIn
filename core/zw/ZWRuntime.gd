# res://autoload/ZWRuntime.gd
@tool
extends Node
#class_name ZWRuntime

# narrow-cast helpers
static func _ms() -> int: return int(Time.get_ticks_msec())
static func _us() -> int: return int(Time.get_ticks_usec())
static func _i(x: float) -> int: return int(x)

@export var zw_entry_file: String = "res://data/test_validation.zw"
@export var state_persistence_enabled: bool = true

var flags := {}
var inventory := {}
var reputation := {}
var player_stats := {}
var current_time := 0
var current_location := ""

var _file_mtime: int = 0


func _ready() -> void:
	print("[ZWRuntime] Bring the heat GPT")
	_emit_state()

# public API you can call from anywhere for the Step 5 test
func set_flag(name: String, v: bool = true) -> void:
	flags[name] = v
	_emit_state()

func _emit_state() -> void:
	var bus := get_node_or_null("/root/ZWEvents")
	if bus:
		bus.emit_signal("zw_state_changed")
	else:
		push_warning("ZWEvents not found")
