extends Node
class_name ZONBinary

## ZON Binary Loader for Godot
## 
## Loads .zonb files and unpacks them into usable dictionaries or arrays.
## EXACTLY MATCHES Python zon_binary_pack.py implementation.

# Type markers (MUST MATCH Python)
const TYPE_NULL = 0x00
const TYPE_BOOL = 0x01
const TYPE_INT = 0x02
const TYPE_FLOAT = 0x03
const TYPE_STRING = 0x04
const TYPE_ARRAY = 0x05
const TYPE_DICT = 0x06
const TYPE_ROOT_ARRAY = 0x07

# Field IDs (MUST MATCH Python FIELD_IDS) - COMPLETE VERSION
const FIELD_NAMES = {
	0x01: "type",
	0x02: "id",
	0x03: "description",
	0x04: "flags",
	0x05: "name",
	0x06: "mood",
	0x07: "action",
	0x08: "environment",
	0x09: "lighting",
	0x0A: "ambience",
	0x0B: "overlays",
	0x0C: "npc_state",
	0x0D: "narrative_pulse",
	0x0E: "speaker",
	0x0F: "emotion",
	0x10: "line",
	0x11: "leads_to",
	0x12: "trigger",
	0x13: "op",
	0x14: "left",
	0x15: "right",
	# Container/Item fields
	0x16: "container",
	0x17: "contents",
	0x18: "item",
	0x19: "quantity",
	# Additional common fields
	0x1A: "npc",
	0x1B: "room",
	0x1C: "rule",
	0x1D: "exits",
	0x1E: "objects",
	0x1F: "level",
	0x20: "health",
	0x21: "hostile",
	0x22: "dialogue",
	0x23: "greeting",
	0x24: "damage",
	0x25: "weight",
}

# Magic header
const ZONB_MAGIC = "ZONB"


func load_zonb(path: String):
	"""Load and unpack a .zonb file.
	Returns Dictionary, Array, or null on failure."""
	var file = FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("Failed to open file: " + path)
		return null
	
	var data = file.get_buffer(file.get_length())
	file.close()
	
	return unpack_zonb(data)


func unpack_zonb(data: PackedByteArray):
	"""Unpack binary ZONB data to Dictionary or Array.
	Returns the unpacked data structure."""
	
	# Verify magic header
	if data.size() < 5:  # ZONB + version byte minimum
		push_error("ZONB data too short")
		return null
	
	var magic = data.slice(0, 4).get_string_from_ascii()
	if magic != ZONB_MAGIC:
		push_error("Invalid ZONB magic header: " + magic)
		return null
	
	var version = data[4]
	var ptr = 5  # Start after magic + version
	
	# Read the root value
	var result = read_value(data, ptr)
	return result[0]


func read_value(buffer: PackedByteArray, ptr: int) -> Array:
	"""Read a single value from buffer starting at ptr.
	Returns [decoded_value, new_ptr]"""
	
	if ptr >= buffer.size():
		push_error("Buffer overflow at position %d" % ptr)
		return [null, ptr]
	
	var type_marker = buffer[ptr]
	ptr += 1
	
	match type_marker:
		TYPE_NULL:
			return [null, ptr]
		
		TYPE_BOOL:
			var value = (buffer[ptr] == 1)
			return [value, ptr + 1]
		
		TYPE_INT:
			var result = read_varint(buffer, ptr)
			return [result[0], result[1]]
		
		TYPE_FLOAT:
			# Python uses little-endian float
			var bytes = buffer.slice(ptr, ptr + 4)
			var value = bytes.decode_float(0)
			return [value, ptr + 4]
		
		TYPE_STRING:
			var len_result = read_varint(buffer, ptr)
			var length = len_result[0]
			ptr = len_result[1]
			var value = buffer.slice(ptr, ptr + length).get_string_from_utf8()
			return [value, ptr + length]
		
		TYPE_ARRAY:
			var count_result = read_varint(buffer, ptr)
			var count = count_result[0]
			ptr = count_result[1]
			var array = []
			for i in range(count):
				var item_result = read_value(buffer, ptr)
				array.append(item_result[0])
				ptr = item_result[1]
			return [array, ptr]
		
		TYPE_DICT:
			var count_result = read_varint(buffer, ptr)
			var count = count_result[0]
			ptr = count_result[1]
			var dict = {}
			
			for i in range(count):
				# Read field_id (varint encoded)
				var field_id_result = read_varint(buffer, ptr)
				var field_id = field_id_result[0]
				ptr = field_id_result[1]
				
				# Get field name
				var field_name = FIELD_NAMES.get(field_id, "field_%d" % field_id)
				
				# Read the value
				var value_result = read_value(buffer, ptr)
				dict[field_name] = value_result[0]
				ptr = value_result[1]
			
			return [dict, ptr]
		
		TYPE_ROOT_ARRAY:
			# Special handling for root-level arrays
			var count_result = read_varint(buffer, ptr)
			var count = count_result[0]
			ptr = count_result[1]
			var array = []
			for i in range(count):
				var item_result = read_value(buffer, ptr)
				array.append(item_result[0])
				ptr = item_result[1]
			return [array, ptr]
		
		_:
			push_error("Unknown type marker: 0x%02X at position %d" % [type_marker, ptr - 1])
			return [null, ptr]


func read_varint(data: PackedByteArray, ptr: int) -> Array:
	"""Read a variable-length integer.
	Returns [value, new_ptr]"""
	var value = 0
	var shift = 0
	
	while ptr < data.size():
		var byte = data[ptr]
		ptr += 1
		
		value |= (byte & 0x7F) << shift
		
		if (byte & 0x80) == 0:
			break
		
		shift += 7
	
	return [value, ptr]


# Helper function for debugging
func dump_buffer(buffer: PackedByteArray, start: int = 0, length: int = 32) -> String:
	"""Dump buffer contents as hex for debugging."""
	var result = ""
	var end = min(start + length, buffer.size())
	for i in range(start, end):
		result += "%02X " % buffer[i]
		if (i - start + 1) % 16 == 0:
			result += "\n"
		elif (i - start + 1) % 8 == 0:
			result += " "
	return result.strip_edges()
