# ZWInspector.gd
extends Control

# Get references to your UI elements using @onready
@onready var blocks_tree: Tree = $VBoxContainer/Panel/Panel2/TabContainer/Control/VBoxContainer/HSplitContainer/Tree
@onready var events_list: ItemList = $VBoxContainer/Panel/Panel2/TabContainer/Control2/VBoxContainer/ItemList

func _ready():
	# Print the entire node tree to see what's actually in your scene
	print_tree()
	
	# Let's also search for any Tree or ItemList nodes in your scene
	var tree_nodes = find_children("*", "Tree", true, false)
	var itemlist_nodes = find_children("*", "ItemList", true, false)
	
	print("Found Tree nodes: ", tree_nodes)
	print("Found ItemList nodes: ", itemlist_nodes)
	
