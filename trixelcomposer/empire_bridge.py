# Empire Bridge: Connect TrixelComposer to TraeAgent via ZW Protocol

import asyncio
import importlib.util
import json
from pathlib import Path
import time

AIOHTTP_AVAILABLE = importlib.util.find_spec("aiohttp") is not None
if AIOHTTP_AVAILABLE:
    import aiohttp

class EmpireBridge:
    def __init__(self, composer, zw_broker_url="http://localhost:5010"):
        self.composer = composer
        self.zw_broker_url = zw_broker_url
        self.session_id = f"trixel_{int(time.time())}"
        self.creative_memory = []
        
    async def send_to_empire(self, zw_message):
        """Send ZW protocol message to Empire via ZW Broker"""
        if not AIOHTTP_AVAILABLE:
            print("Empire communication unavailable: aiohttp is not installed.")
            return None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.zw_broker_url}/orchestrate",
                    json={
                        "session_id": self.session_id,
                        "domain": "trixel_creative",
                        "zw_content": zw_message
                    }
                ) as response:
                    return await response.json()
        except Exception as e:
            print(f"Empire communication error: {e}")
            return None

    async def request_ai_guidance(self, canvas_state):
        """Ask TraeAgent for creative guidance"""
        zw_request = {
            "!zw/trixel.guidance_request": {
                "canvas_snapshot": canvas_state,
                "current_tool": self.composer.tool,
                "memory_context": self.creative_memory[-3:],  # Last 3 decisions
                "request_type": "creative_suggestion"
            }
        }
        
        response = await self.send_to_empire(zw_request)
        if response and "ai_suggestion" in response:
            return self.parse_ai_suggestion(response["ai_suggestion"])
        return None

    def parse_ai_suggestion(self, suggestion):
        """Convert Empire AI response to actionable plan"""
        # Parse ZW response into Trixel action
        if "!zw/art.action" in suggestion:
            action_data = suggestion["!zw/art.action"]
            return {
                'action': action_data.get('tool', 'brush'),
                'x': action_data.get('x', 8),
                'y': action_data.get('y', 8), 
                'color': tuple(action_data.get('color', [255, 255, 255])),
                'reasoning': action_data.get('reasoning', 'AI suggestion')
            }
        return None

    async def collaborative_create(self):
        """Main collaborative creation loop with Empire"""
        print("🎨 Starting collaborative creation with AI Empire...")
        
        for iteration in range(10):  # 10 creative iterations
            # 1. Perceive current state
            canvas_state = self.composer.perceive()
            
            # 2. Request AI guidance from Empire
            ai_plan = await self.request_ai_guidance(canvas_state)
            
            if ai_plan:
                print(f"🧠 AI suggests: {ai_plan['reasoning']}")
                
                # 3. Execute AI suggestion
                self.composer.act(ai_plan)
                
                # 4. Log collaborative decision
                self.creative_memory.append({
                    'iteration': iteration,
                    'ai_suggestion': ai_plan,
                    'canvas_state_after': self.composer.perceive(),
                    'collaboration_success': True
                })
                
                # 5. Send learning feedback to Empire
                await self.send_learning_feedback(ai_plan, iteration)
                
            else:
                # Autonomous fallback
                local_plan = self.composer.plan()
                self.composer.act(local_plan)
                print(f"🎯 Autonomous action: {local_plan}")
            
            # Brief pause for observation
            await asyncio.sleep(0.5)
        
        # Save collaborative session
        self.save_collaborative_session()
        print("✅ Collaborative creation complete!")

    async def send_learning_feedback(self, executed_plan, iteration):
        """Send learning feedback to Empire for style development"""
        zw_feedback = {
            "!zw/trixel.learning": {
                "session_id": self.session_id,
                "iteration": iteration,
                "action_executed": executed_plan,
                "canvas_evolution": "positive",  # Could analyze canvas changes
                "style_notes": "developing_personal_aesthetic",
                "preference_learning": True
            }
        }
        await self.send_to_empire(zw_feedback)

    def save_collaborative_session(self):
        """Save the collaborative creative session"""
        session_data = {
            "session_id": self.session_id,
            "canvas_final": self.composer.canvas.tolist(),
            "creative_memory": self.creative_memory,
            "collaboration_stats": {
                "ai_suggestions": len([m for m in self.creative_memory if m.get('collaboration_success')]),
                "autonomous_actions": len(self.composer.memory) - len(self.creative_memory)
            }
        }
        
        session_file = Path(f".zw/sessions/collaborative_{self.session_id}.json")
        session_file.parent.mkdir(parents=True, exist_ok=True)
        session_file.write_text(json.dumps(session_data, indent=2))

# Integration helper for an external composer implementation.
def attach_empire_bridge(composer):
    """Attach Empire bridge to any composer object exposing perceive/act/plan/tool/canvas."""
    composer.empire_bridge = EmpireBridge(composer)
    return composer
