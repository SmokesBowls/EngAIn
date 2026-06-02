# Enhanced zw_file_bridge.py with Improved Narrative Generation
import os
import time
import json
from VisionAgent import VisualZWBridge, VisionAgent

# Create one coordinator that persists across commands
coordinator = None
visual_bridge = None

class SymbolicAgent:
    def __init__(self):
        self.state = {
            "location": "Cosmic Command Center",
            "inventory": ["RealityManipulator"],
            "objects": {
                "EntropyDial": {"status": "active"},
                "TimelineAnchor": {"status": "locked"},
                "MandelaLock": {"status": "available"}
            }
        }
    
    def validate_and_update(self, zw_packet):
        action = zw_packet.get("ACTION", {})
        verb = action.get("verb", "").lower()
        target = action.get("target", "").lower()
        
        state_delta = {}
        
        if "look" in verb or "see" in verb or "where" in verb or "what" in verb:
            # Visual analysis action - no state change needed
            pass
        elif "activate" in verb:
            if "entropy" in target:
                self.state["objects"]["EntropyDial"]["status"] = "activated"
                state_delta["entropy_activated"] = True
        elif "lock" in verb:
            if "mandela" in target:
                self.state["objects"]["MandelaLock"]["status"] = "engaged"
                state_delta["mandela_lock"] = True
        
        return True, state_delta

class NarrativeAgent:
    def generate(self, zw_packet, state_delta, visual_context=""):
        action = zw_packet.get("ACTION", {})
        verb = action.get("verb", "").lower()
        target = action.get("target", "").lower()
        
        # Better narrative generation for different command types
        if "look" in verb or "see" in verb:
            return self._generate_look_response(visual_context)
        elif "where" in verb:
            return self._generate_location_response(visual_context)
        elif "what" in verb:
            return self._generate_what_response(target, visual_context)
        elif "hi" in verb or "hello" in verb:
            return self._generate_greeting_response()
        elif "activate" in verb and "entropy" in target:
            return "You reach toward the entropy dial. The cosmic energies respond to your touch, reality beginning to fluctuate around the control interface."
        elif "lock" in verb and "mandela" in target:
            return "The Mandela Lock mechanism engages with a deep resonance. Timeline anchors solidify, preventing further reality drift."
        else:
            return self._generate_generic_response(verb, target, visual_context)
    
    def _generate_look_response(self, visual_context):
        if visual_context and "VISUAL CONTEXT:" in visual_context:
            visual_part = visual_context.split("VISUAL CONTEXT:")[1].strip()
            return f"Looking at the interface before me, {visual_part.lower()}"
        else:
            return "I observe the cosmic command center - a sophisticated reality manipulation interface with multiple control systems and monitoring displays. The geometric patterns suggest dimensional mapping capabilities."
    
    def _generate_location_response(self, visual_context):
        return "You are within the Cosmic Command Center, standing before a sophisticated reality manipulation interface. The control panels around you monitor temporal stability and dimensional anchoring systems."
    
    def _generate_what_response(self, target, visual_context):
        if not target or "implicit" in target:
            return "You observe the cosmic interface around you - reality control panels, temporal anchoring systems, and dimensional monitoring displays all working in harmony to maintain the stability of this command center."
        else:
            return f"You focus your attention on {target} within the cosmic command interface."
    
    def _generate_greeting_response(self):
        return "The cosmic interface pulses with acknowledgment. Reality patterns shift subtly around you as the command center recognizes your presence. The dragon awaits your instructions for reality manipulation."
    
    def _generate_generic_response(self, verb, target, visual_context):
        if not target or "implicit" in target:
            return f"You {verb} within the cosmic command center. The reality manipulation interface responds to your intent, patterns of light shifting across the control panels."
        else:
            return f"You {verb} the {target} through the cosmic interface. The reality manipulation systems process your command."

class WatcherAgent:
    def log(self, message):
        print(f"WATCHER: {message}")

class CoordinatorAgent:
    def __init__(self):
        self.watcher = WatcherAgent()
        self.symbolic = SymbolicAgent()
        self.narrative = NarrativeAgent()
    
    def process_request(self, zw_packet, visual_context=""):
        self.watcher.log(f"Received ZW-PACKET with visual context: {len(visual_context)} chars")
        
        valid, state_delta = self.symbolic.validate_and_update(zw_packet)
        
        if not valid:
            self.watcher.log(f"Invalid action: {zw_packet}")
            return {
                "narrative": "The reality interface rejects that command.",
                "world_state": self.symbolic.state,
                "timestamp": time.time()
            }
        
        narrative_response = self.narrative.generate(zw_packet, state_delta, visual_context)
        self.watcher.log(f"Generated narrative with visual awareness")
        
        return {
            "narrative": narrative_response,
            "world_state": self.symbolic.state,
            "visual_analysis_used": "VISUAL CONTEXT:" in visual_context,
            "timestamp": time.time()
        }

def create_zw_packet(command_text):
    words = command_text.lower().split()
    verb = words[0] if words else "unknown"
    target = " ".join(words[1:]) if len(words) > 1 else "implicit"
    
    return {
        "type": "ZW-REQUEST",
        "SCOPE": "Player",
        "CONTEXT": {
            "Location": "Cosmic Command Center",
            "Inventory": ["RealityManipulator"]
        },
        "ACTION": {
            "verb": verb,
            "target": target
        }
    }

def process_command_with_vision(command_text):
    global coordinator, visual_bridge
    
    if coordinator is None:
        coordinator = CoordinatorAgent()
    
    if visual_bridge is None:
        visual_bridge = VisualZWBridge()
        visual_bridge.snapshots_dir = "snapshots/"
    
    # Create enhanced context with vision
    try:
        zw_packet, enhanced_context = visual_bridge.create_visual_zw_packet(
            command_text, 
            "Currently in Cosmic Command Center"
        )
        
        # Process with visual awareness
        result = coordinator.process_request(zw_packet, enhanced_context)
        
        print(f"VISION: Used visual context: {result.get('visual_analysis_used', False)}")
        return result
        
    except Exception as e:
        print(f"VISION ERROR: {e}")
        # Fallback to non-visual processing
        zw_packet = create_zw_packet(command_text)
        return coordinator.process_request(zw_packet)

def main():
    print("Enhanced ZW File Bridge with Vision started...")
    print("Waiting for commands from Godot in 'godot_command.txt'")
    print("Vision system will analyze screenshots from 'snapshots/' directory")
    
    while True:
        try:
            if os.path.exists('godot_command.txt'):
                try:
                    with open('godot_command.txt', 'r') as f:
                        command = f.read().strip()
                    
                    if command:
                        print(f"Processing command with vision: {command}")
                        
                        # Use enhanced vision-aware processing
                        response_dict = process_command_with_vision(command)
                        
                        with open('python_response.json', 'w') as f:
                            json.dump(response_dict, f, indent=2)
                        
                        print(f"Response written: {response_dict['narrative']}")
                        
                        os.remove('godot_command.txt')
                    else:
                        os.remove('godot_command.txt')
                        
                except IOError:
                    print("File access error, retrying...")
                    time.sleep(0.05)
                    continue
            
            time.sleep(0.1)
            
        except KeyboardInterrupt:
            print("\nVision-Enhanced Bridge stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
