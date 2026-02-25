extends Node

var t := 0.0

func _process(delta: float) -> void:
	t += delta
	if int(t) % 2 == 0:
		print("heartbeat:", snapped(t, 0.1))
