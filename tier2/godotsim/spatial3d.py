# spatial3d.py - Base classes for spatial adapter
"""
Minimal stubs for Spatial3D adapter to work standalone
without full ENGINALITY framework
"""

class Spatial3DStateView:
    """Base state view for spatial subsystem"""
    
    def __init__(self, state_slice=None):
        self.state = state_slice or {"entities": {}}
    
    def get_entity(self, entity_id):
        return self.state.get("entities", {}).get(entity_id)
    
    def get_all_entities(self):
        return self.state.get("entities", {})
    
    def set_entity(self, entity_id, data):
        if "entities" not in self.state:
            self.state["entities"] = {}
        self.state["entities"][entity_id] = data


class Alert:
    """Alert/warning for subsystem violations"""
    
    def __init__(self, level, message, context=None):
        self.level = level
        self.message = message
        self.context = context or {}
    
    def __repr__(self):
        return f"Alert({self.level}: {self.message})"
