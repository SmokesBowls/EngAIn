extends Node
## Test script for ZONBinary loader
##
## This script tests loading .zonb files in Godot
## Place this in your test scene and run it

func _ready():
	print("=== ZONBinary Test ===")
	
		# Test 1: Load door rule example
	test_door_rule()
	
	# Test 2: Load Zork data
	test_zork_data()
	
	# ONLY test our new GUI-created file
	test_gui_container()
	
	print("\n=== Tests Complete ===")


func test_door_rule():
	print("\n--- Test 1: Door Rule ---")

	var loader = ZONBinary.new()
	var data = loader.load_zonb("res://test.zonb")

	if data == null:
		print("❌ Failed to load test.zonb")
		return

	print("✓ Loaded successfully")
	print("  Type: ", data.get("type", "N/A"))
	print("  ID: ", data.get("id", "N/A"))
	print("  Condition: ", data.get("condition", "N/A"))

	if data.has("requires"):
		print("  Requires:")
		for req in data.requires:
			print("    - ", req)

	if data.has("effect"):
		print("  Effect:")
		for eff in data.effect:
			print("    - ", eff)

func test_zork_data():
	print("\n--- Test 2: Zork Data ---")

	# Check if Zork data exists
	if not FileAccess.file_exists("res://zork/compiled/3dungeon.zonb"):
		print("⚠ Zork data not found (skip)")
		return

	var loader = ZONBinary.new()
	var data = loader.load_zonb("res://zork/compiled/3dungeon.zonb")

	if data == null:
		print("❌ Failed to load Zork data")
		return

	print("✓ Loaded Zork data")

	# Check if it's an array
	if typeof(data) == TYPE_ARRAY:
		print("  Item count: ", data.size())
		if data.size() > 0:
			print("  First item type: ", data[0].get("type", "N/A"))
			print("  First item ID: ", data[0].get("id", "N/A"))
			if data[0].has("description"):
				print("  Description: ", data[0].description)
	else:
		print("  Type: ", typeof(data))
		print("  Keys: ", data.keys())

func test_gui_container():
	print("\n--- Test 3: GUI-Created Container ---")

	# Check if GUI container exists
	if not FileAccess.file_exists("res://test_container.zonb"):
		print("⚠ GUI container not found (skip)")
		return

	var loader = ZONBinary.new()
	var data = loader.load_zonb("res://test2_container.zonb")

	if data == null:
		print("❌ Failed to load GUI container")
		return

	print("✓ Loaded GUI container")
	print("  Data type: ", typeof(data))
	print("  Data keys: ", data.keys())

	# Navigate to container data
	var container = data.get("container", {})
	if container.is_empty():
		print("  No container key found")
		return

	print("  Container found with ", container.size(), " fields")
	print("  Container ID: ", container.get("id", "N/A"))
	print("  Type: ", container.get("type", "N/A"))
	print("  Description: ", container.get("description", "N/A"))
	print("  Flags: ", str(container.get("flags", [])))

	if container.has("contents"):
		var contents = container.contents
		if typeof(contents) == TYPE_ARRAY:
			print("  Contents: ", contents.size(), " items")
			for item_wrapper in contents:
				var item_data = item_wrapper.get("item", {})
				var item_id = item_data.get("id", "unknown")
				var qty = item_data.get("quantity", 1)
				print("    - ", item_id, " (qty: ", qty, ")")
