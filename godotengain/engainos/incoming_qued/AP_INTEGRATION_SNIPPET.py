"""
MINIMAL AP INTEGRATION SNIPPET
Add this to your existing launch_engine.py or main runtime file

Location: /home/burdens/Downloads/EngAIn/godotengain/engainos/launch_engine.py
"""

# ============================================================================
# STEP 1: Add imports at top of file
# ============================================================================

# Add after your existing imports:
import sys
from pathlib import Path

# Make sure core is in path
sys.path.insert(0, str(Path(__file__).parent / "core"))

from core.ap_engine import ZWAPEngine, StateProvider
from core.ap_runtime import APRuntimeIntegration


# ============================================================================
# STEP 2: Add AP initialization in your main class
# ============================================================================

class YourMainRuntimeClass:  # Whatever your class is called
    def __init__(self):
        # ... your existing __init__ code ...
        
        # Initialize AP Runtime
        self.ap_runtime = None
        self._init_ap_runtime()
    
    def _init_ap_runtime(self):
        """Initialize AP engine with rules from scenes"""
        try:
            # Point to your scenes directory
            scenes_dir = Path(__file__).parent / "game_scenes"
            
            # Create AP runtime
            self.ap_runtime = APRuntimeIntegration(scenes_dir=str(scenes_dir))
            
            # Initialize with empty state (will load from ZON later)
            initial_state = {
                'flags': {},
                'stats': {},
                'locations': {},
                'inventory': {}
            }
            
            self.ap_runtime.initialize(initial_state)
            
            print(f"[AP] Initialized successfully")
            
        except Exception as e:
            print(f"[AP] Warning: Failed to initialize: {e}")
            print("[AP] AP queries will not be available")


# ============================================================================
# STEP 3: Add message handler for AP queries
# ============================================================================

    def handle_message(self, msg_dict):
        """Handle incoming messages from Godot"""
        # ... your existing message handling ...
        
        msg_type = msg_dict.get('type', '')
        
        # Route AP messages
        if msg_type.startswith('ap_'):
            if self.ap_runtime:
                try:
                    result = self.ap_runtime.handle_message(msg_dict)
                    return result
                except Exception as e:
                    return {'error': f'ap_error: {str(e)}'}
            else:
                return {'error': 'ap_not_initialized'}
        
        # ... rest of your message handling ...


# ============================================================================
# STEP 4: Optional - Sync state when it changes
# ============================================================================

    def on_state_change(self, state_delta):
        """Called when game state changes"""
        # ... your existing state handling ...
        
        # Sync to AP
        if self.ap_runtime:
            try:
                self.ap_runtime.update_state(state_delta)
            except Exception as e:
                print(f"[AP] State sync error: {e}")


# ============================================================================
# TESTING: Verify AP is loaded
# ============================================================================

    def test_ap(self):
        """Quick test to verify AP is working"""
        if not self.ap_runtime or not self.ap_runtime.engine:
            print("[AP] Not initialized")
            return
        
        # List loaded rules
        rules = self.ap_runtime.engine.list_rules()
        print(f"[AP] Loaded {len(rules)} rules:")
        for rule in rules[:5]:  # Show first 5
            print(f"  - {rule['id']}: priority={rule.get('priority', 0)}")


# ============================================================================
# USAGE IN YOUR MAIN
# ============================================================================

"""
if __name__ == '__main__':
    runtime = YourMainRuntimeClass()
    runtime.test_ap()  # Verify AP loaded
    # ... start your HTTP server ...
"""
