# EventBus.gd - Global event system for ZW Protocol
extends Node

# Mandela Lock events
signal mandela_lock_triggered(anchor_id: String)
signal anchor_memory_selected(anchor_id: String)
signal temporal_collapse_started()

# Stellar Broadcast events  
signal stellar_broadcast_activated(signal_data: Dictionary)

# Reality Engine events
signal reality_shift(intensity: float, affected_nodes: Array)
signal paradox_detected(severity: String, options: Array)

# Dream State events
signal dream_corruption_detected(corruption_type: String)
signal reality_quarantine_activated(active: bool)

# General system events
signal zw_packet_processed(packet: Dictionary)
signal system_error_occurred(error_data: Dictionary)

func _ready():
    print("EventBus: ZW Protocol event system ready")
