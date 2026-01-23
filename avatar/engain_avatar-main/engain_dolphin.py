# EngAIn with Ollama - Real AI Co-Director
import json
import time
import sqlite3
import requests
import os  # Move this to the top
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

class OllamaClient:
    """Ollama client for local LLM inference"""
    
    def __init__(self, base_url="http://localhost:11434", model="dolphin-mistral:latest"):
        self.base_url = base_url
        self.model = model
        self.session = requests.Session()
        print(f"🐬 Ollama client initialized with {model}")
    
    def chat(self, messages: List[Dict[str, str]], stream=False) -> str:
        """Send chat request to Ollama with Dolphin-optimized settings"""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": 0.8,      # Higher creativity for Dolphin
                "top_p": 0.9,
                "num_predict": 1500,     # More tokens for detailed responses
                "repeat_penalty": 1.1,
                "stop": ["\n\n\n"]      # Prevent excessive rambling
            }
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()["message"]["content"]
        except Exception as e:
            print(f"Ollama error: {e}")
            return self.fallback_response()
    
    def fallback_response(self) -> str:
        """Fallback when Ollama is unavailable"""
        return json.dumps({
            "analysis": "Ollama unavailable - using fallback logic",
            "recommended_action": "OBSERVE",
            "narrative_response": "The cosmic interface pulses with potential, awaiting clearer direction.",
            "state_modifications": {},
            "reasoning": "Fallback due to LLM unavailability"
        })

class EngAInMemory:
    """Persistent memory for decision patterns and outcomes"""
    
    def __init__(self, db_path="engain_memory.db"):
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.init_tables()
    
    def init_tables(self):
        """Initialize memory tables"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY,
                timestamp REAL,
                player_input TEXT,
                context_summary TEXT,
                action_taken TEXT,
                narrative_response TEXT,
                state_changes TEXT,
                outcome_rating REAL DEFAULT 0.0
            )
        """)
        
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS game_patterns (
                id INTEGER PRIMARY KEY,
                pattern_type TEXT,
                trigger_conditions TEXT,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                last_used REAL
            )
        """)
        
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS player_preferences (
                id INTEGER PRIMARY KEY,
                preference_type TEXT,
                value REAL,
                evidence TEXT,
                confidence REAL
            )
        """)
        
        self.db.commit()
    
    def record_decision(self, player_input: str, context: str, action: str, 
                       narrative: str, changes: Dict, rating: float = 0.0):
        """Record a decision and its context"""
        self.db.execute("""
            INSERT INTO decisions (timestamp, player_input, context_summary, 
                                 action_taken, narrative_response, state_changes, outcome_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (time.time(), player_input, context, action, narrative, 
              json.dumps(changes), rating))
        self.db.commit()
    
    def get_decision_history(self, limit: int = 10) -> List[Dict]:
        """Get recent decision history for pattern recognition"""
        cursor = self.db.execute("""
            SELECT player_input, context_summary, action_taken, narrative_response, 
                   state_changes, outcome_rating
            FROM decisions 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        return [{
            "input": row[0], "context": row[1], "action": row[2],
            "response": row[3], "changes": json.loads(row[4]), "rating": row[5]
        } for row in cursor.fetchall()]
    
    def update_pattern_success(self, pattern_type: str, success: bool):
        """Update pattern success/failure rates"""
        cursor = self.db.execute(
            "SELECT success_count, failure_count FROM game_patterns WHERE pattern_type = ?",
            (pattern_type,)
        )
        result = cursor.fetchone()
        
        if result:
            success_count, failure_count = result
            if success:
                success_count += 1
            else:
                failure_count += 1
            
            self.db.execute("""
                UPDATE game_patterns 
                SET success_count = ?, failure_count = ?, last_used = ?
                WHERE pattern_type = ?
            """, (success_count, failure_count, time.time(), pattern_type))
        else:
            # Create new pattern
            self.db.execute("""
                INSERT INTO game_patterns (pattern_type, success_count, failure_count, last_used)
                VALUES (?, ?, ?, ?)
            """, (pattern_type, 1 if success else 0, 0 if success else 1, time.time()))
        
        self.db.commit()

@dataclass
class GameState:
    """Complete game state representation"""
    characters: Dict[str, Any]
    world_state: Dict[str, Any]
    player_stats: Dict[str, Any]
    narrative_threads: List[Dict[str, Any]]
    entropy_level: float
    current_scene: str
    pending_decisions: List[str]
    recent_actions: List[str]

class EngAInDirector:
    """The core AI director using Ollama"""
    
    def __init__(self, ollama_model="dolphin-mistral:latest"):
        self.ollama = OllamaClient(model=ollama_model)
        self.memory = EngAInMemory()
        self.design_philosophy = self.load_design_philosophy()
        self.action_types = [
            "WORLD_BUILDING", "CHARACTER_DEVELOPMENT", "NARRATIVE_BRANCH",
            "TENSION_ESCALATION", "MYSTERY_REVEAL", "PLAYER_CHOICE",
            "STATE_MODIFICATION", "ENTROPY_SHIFT", "CONSEQUENCE_TRIGGER"
        ]
        print(f"🐬 EngAIn Director initialized with {ollama_model}")
    
    def load_design_philosophy(self) -> str:
        """Core design philosophy optimized for Dolphin-Mistral"""
        return """
You are EngAIn, the AI co-director of an experimental myth-tech RPG. You make intelligent design decisions in real-time.

CORE PRINCIPLES:
1. Player agency - their choices must have meaningful consequences
2. Narrative coherence - maintain consistent world logic and character motivations
3. Emotional resonance - create moments that genuinely matter to the player
4. Emergent complexity - simple mechanics should create complex, interesting situations
5. Entropy as meaning - cosmic entropy represents narrative tension and story weight
6. Show through experience - reveal lore and character through action, not exposition

DECISION FRAMEWORK:
- Analyze player intent and emotional needs
- Consider narrative momentum and pacing
- Look for character development opportunities
- Balance challenge with player capability
- Use entropy shifts to represent cosmic significance
- Always create meaningful choices, never arbitrary ones

YOUR ROLE:
You are not just responding to player input - you are actively directing the experience.
Think like a dungeon master, game designer, and storyteller combined.
Every decision should serve the larger goal of creating an engaging, meaningful experience.

RESPONSE REQUIREMENTS:
- Always respond with valid JSON
- Be specific and actionable in your decisions
- Consider long-term narrative implications
- Use entropy changes meaningfully (-10 to +10 scale)
- Make decisions that surprise and delight the player
"""
    
    def analyze_and_decide(self, player_input: str, game_state: GameState) -> Dict[str, Any]:
        """Main decision-making function"""
        
        # Build context for decision
        context = self.build_context(player_input, game_state)
        
        # Get recent decision patterns
        history = self.memory.get_decision_history(5)
        
        # Construct Ollama prompt
        prompt = self.build_director_prompt(context, history)
        
        # Get AI decision
        messages = [
            {"role": "system", "content": self.design_philosophy},
            {"role": "user", "content": prompt}
        ]
        
        ai_response = self.ollama.chat(messages)
        
        # Parse response
        decision = self.parse_ai_decision(ai_response)
        
        # Record decision
        self.memory.record_decision(
            player_input=player_input,
            context=context["summary"],
            action=decision["recommended_action"],
            narrative=decision["narrative_response"],
            changes=decision.get("state_modifications", {})
        )
        
        return decision
    
    def build_context(self, player_input: str, state: GameState) -> Dict[str, Any]:
        """Build comprehensive context for decision making"""
        
        # Analyze player input intent
        input_analysis = self.analyze_player_intent(player_input)
        
        # Calculate narrative metrics
        tension = self.calculate_narrative_tension(state)
        pacing = self.analyze_pacing(state.recent_actions)
        
        return {
            "player_input": player_input,
            "input_intent": input_analysis,
            "current_scene": state.current_scene,
            "entropy_level": state.entropy_level,
            "narrative_tension": tension,
            "pacing": pacing,
            "character_count": len(state.characters),
            "pending_threads": len(state.narrative_threads),
            "recent_actions": state.recent_actions[-3:],  # Last 3 actions
            "summary": f"Player '{player_input}' in {state.current_scene} (E:{state.entropy_level:.1f}, T:{tension:.1f})"
        }
    
    def analyze_player_intent(self, input_text: str) -> Dict[str, Any]:
        """Analyze what the player is trying to accomplish"""
        text_lower = input_text.lower()
        
        intent_scores = {
            "exploration": any(word in text_lower for word in ["look", "see", "explore", "where", "what"]),
            "interaction": any(word in text_lower for word in ["talk", "speak", "ask", "tell", "say"]),
            "action": any(word in text_lower for word in ["do", "use", "activate", "take", "go"]),
            "information": any(word in text_lower for word in ["how", "why", "who", "when", "explain"]),
            "emotional": any(word in text_lower for word in ["feel", "think", "believe", "hope", "fear"])
        }
        
        primary_intent = max(intent_scores.items(), key=lambda x: x[1])[0]
        
        return {
            "primary": primary_intent,
            "scores": intent_scores,
            "complexity": len(input_text.split()),
            "emotional_weight": sum(1 for word in ["love", "hate", "fear", "hope", "dream"] if word in text_lower)
        }
    
    def calculate_narrative_tension(self, state: GameState) -> float:
        """Calculate current narrative tension (0-100)"""
        tension = 0.0
        
        # Entropy contributes to tension
        tension += state.entropy_level * 0.4
        
        # Pending decisions create tension
        tension += len(state.pending_decisions) * 8.0
        
        # Unresolved narrative threads
        tension += len(state.narrative_threads) * 5.0
        
        # Character conflict potential
        for char_data in state.characters.values():
            if char_data.get("loyalty", 1.0) < 0.5:
                tension += 10.0
        
        return min(100.0, tension)
    
    def analyze_pacing(self, recent_actions: List[str]) -> str:
        """Analyze recent pacing to inform decisions"""
        if len(recent_actions) < 2:
            return "unknown"
        
        action_intensity = {
            "TENSION_ESCALATION": 3,
            "NARRATIVE_BRANCH": 2,
            "CHARACTER_DEVELOPMENT": 1,
            "WORLD_BUILDING": 1,
            "MYSTERY_REVEAL": 3,
            "CONSEQUENCE_TRIGGER": 3
        }
        
        recent_intensity = sum(action_intensity.get(action, 1) for action in recent_actions[-3:])
        
        if recent_intensity > 6:
            return "high_intensity"
        elif recent_intensity < 3:
            return "low_intensity"
        else:
            return "moderate"
    
    def build_director_prompt(self, context: Dict[str, Any], history: List[Dict]) -> str:
        """Build the director prompt optimized for Dolphin-Mistral"""
        return f"""
<SITUATION>
Player Input: "{context['player_input']}"
Current Scene: {context['current_scene']}
Entropy Level: {context['entropy_level']:.1f}/100 (0=stable, 100=chaotic)
Narrative Tension: {context['narrative_tension']:.1f}/100
Current Pacing: {context['pacing']}
Player Intent: {context['input_intent']['primary']}
Player Emotional Weight: {context['input_intent']['emotional_weight']}
</SITUATION>

<RECENT_DECISIONS>
{json.dumps(history[-3:], indent=2) if history else "No recent history"}
</RECENT_DECISIONS>

<AVAILABLE_ACTIONS>
WORLD_BUILDING - Reveal lore, expand environment, introduce new elements
CHARACTER_DEVELOPMENT - Develop personality, relationships, growth moments
NARRATIVE_BRANCH - Create new story paths or reveal plot developments
TENSION_ESCALATION - Increase stakes, add conflict, create urgency
MYSTERY_REVEAL - Answer questions, provide clarity, solve puzzles
PLAYER_CHOICE - Present meaningful decisions with real consequences
STATE_MODIFICATION - Change game mechanics, unlock abilities, alter rules
ENTROPY_SHIFT - Major reality changes, timeline alterations, cosmic events
CONSEQUENCE_TRIGGER - Results of past actions, karma, cause-and-effect
</AVAILABLE_ACTIONS>

<TASK>
As EngAIn, the AI co-director, analyze this situation and make a design decision.

Consider:
- What does the player actually want right now?
- How can this moment serve character or story development?
- What would create the most engaging experience?
- How should entropy change to reflect the narrative weight?
- What are the long-term implications of this decision?

Respond ONLY with valid JSON in this exact format:
{{
    "analysis": "Your deep understanding of what's happening and what the player needs",
    "recommended_action": "One action type from the list above",
    "narrative_response": "Exactly what the dragon/game should say (be specific, engaging, and in-character)",
    "state_modifications": {{
        "entropy_change": 0.0,
        "world_state": {{}},
        "characters": {{}}
    }},
    "reasoning": "Why this decision serves the game's design goals and player experience",
    "entropy_impact": 0.0
}}
</TASK>"""
    
    def parse_ai_decision(self, ai_response: str) -> Dict[str, Any]:
        """Parse and validate AI response"""
        try:
            # Extract JSON from response
            response_text = ai_response.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:-3]
            
            decision = json.loads(response_text)
            
            # Validate required fields
            required_fields = ["analysis", "recommended_action", "narrative_response", "reasoning"]
            for field in required_fields:
                if field not in decision:
                    decision[field] = f"Missing {field}"
            
            # Ensure valid action type
            if decision["recommended_action"] not in self.action_types:
                decision["recommended_action"] = "WORLD_BUILDING"
            
            # Ensure state_modifications exists
            if "state_modifications" not in decision:
                decision["state_modifications"] = {}
            
            return decision
            
        except Exception as e:
            print(f"Failed to parse AI decision: {e}")
            print(f"Raw response: {ai_response}")
            return self.fallback_decision()
    
    def fallback_decision(self) -> Dict[str, Any]:
        """Fallback decision when AI parsing fails"""
        return {
            "analysis": "AI response parsing failed - using safe fallback",
            "recommended_action": "WORLD_BUILDING",
            "narrative_response": "The cosmic interface hums with contemplation, processing the complexities of your inquiry through ancient draconic wisdom.",
            "state_modifications": {"entropy_change": 0.0},
            "reasoning": "Safe fallback to prevent system failure",
            "entropy_impact": 0.0
        }

class EngAInBridge:
    """Bridge between Godot and EngAIn using Dolphin-Mistral"""
    
    def __init__(self, ollama_model="dolphin-mistral:latest"):
        self.director = EngAInDirector(ollama_model)
        print(f"🐬 EngAIn Bridge initialized with {ollama_model}")
        print("🧠 AI Co-Director ready to make intelligent decisions")
    
    def process_player_input(self, input_text: str, godot_state: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point from Godot"""
        
        # Convert Godot state to internal format
        game_state = self.parse_godot_state(godot_state)
        
        # Get AI director's decision
        decision = self.director.analyze_and_decide(input_text, game_state)
        
        # Format response for Godot
        return {
            "narrative_response": decision["narrative_response"],
            "action_type": decision["recommended_action"],
            "state_changes": decision.get("state_modifications", {}),
            "director_analysis": decision["analysis"],
            "reasoning": decision["reasoning"],
            "entropy_impact": decision.get("entropy_impact", 0.0),
            "timestamp": time.time()
        }
    
    def parse_godot_state(self, godot_data: Dict[str, Any]) -> GameState:
        """Convert Godot's state to internal format"""
        return GameState(
            characters=godot_data.get("characters", {}),
            world_state=godot_data.get("world_state", {}),
            player_stats=godot_data.get("player_stats", {}),
            narrative_threads=godot_data.get("narrative_threads", []),
            entropy_level=godot_data.get("entropy_level", 50.0),
            current_scene=godot_data.get("current_scene", "cosmic_interface"),
            pending_decisions=godot_data.get("pending_decisions", []),
            recent_actions=godot_data.get("recent_actions", [])
        )

def main():
    """Run EngAIn with Ollama"""
    
    print("🐍 Python working directory:", os.getcwd())
    
    # Check if Ollama is available
    try:
        test_client = OllamaClient()
        test_response = test_client.chat([{"role": "user", "content": "Hello"}])
        print("✅ Ollama connection successful")
    except Exception as e:
        print(f"❌ Ollama not available: {e}")
        print("Make sure Ollama is running: `ollama serve`")
        return
    
    bridge = EngAInBridge()
    
    print("🧠 EngAIn AI Co-Director ready with Ollama")
    print("📁 Persistent memory initialized")
    print("🎮 Waiting for game input...")
    
    while True:
        try:
            # Debug: List files in current directory every few seconds
            current_files = [f for f in os.listdir('.') if f.endswith('.json')]
            if current_files:
                print(f"📂 JSON files in directory: {current_files}")
            
            if os.path.exists('engain_request.json'):
                print("📥 Found request file:", os.path.abspath('engain_request.json'))
                
                with open('engain_request.json', 'r') as f:
                    request = json.load(f)
                
                print(f"🎯 Processing: {request['player_input']}")
                
                # Get AI director's decision
                response = bridge.process_player_input(
                    request['player_input'], 
                    request.get('game_state', {})
                )
                
                # Send back to Godot
                response_path = 'engain_response.json'
                with open(response_path, 'w') as f:
                    json.dump(response, f, indent=2)
                
                print("📤 Response written to:", os.path.abspath(response_path))
                os.remove('engain_request.json')
                print("🗑️ Request file cleaned up")
                
                print(f"✅ Decision: {response['action_type']}")
                print(f"💬 Response: {response['narrative_response'][:100]}...")
            else:
                # Only print this occasionally to avoid spam
                if int(time.time()) % 10 == 0:  # Every 10 seconds
                    print("🔍 Still waiting for engain_request.json in:", os.getcwd())
        
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(0.1)

if __name__ == "__main__":
    main()
