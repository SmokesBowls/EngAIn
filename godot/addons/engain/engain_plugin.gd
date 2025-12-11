@tool
extends EditorPlugin

# EngAIn Plugin
# Integrates ZW/ZON/AP runtime into Godot

func _enter_tree():
	print("EngAIn: Initializing AI Game Engine")
	# Add custom types, autoloads, etc.
	pass


func _exit_tree():
	print("EngAIn: Shutting down")
	# Clean up
	pass
