# EngAIn - The AI Co-Director
## *Real-Time Intelligent Game Direction with Local LLM Integration*

> **EngAIn** (Engine AI) is a revolutionary AI co-director system that uses local LLMs to make intelligent, real-time narrative and mechanical decisions in games. Built with Godot 4 and powered by Ollama/Dolphin-Mistral, EngAIn represents the future of adaptive, intelligent game experiences.

---

## 🧠 **What is EngAIn?**

EngAIn is **not** a chatbot or simple response system. It's a **Tier 3 AI Agent** that:

- **Analyzes player intent** and emotional state in real-time
- **Makes director-level decisions** about narrative pacing, tension, and character development
- **Modifies game state** based on design principles and player psychology
- **Manages cosmic entropy** as a meaningful gameplay mechanic
- **Learns from player interactions** through persistent memory
- **Provides visual context awareness** through screenshot analysis

### 🎯 **Core Philosophy**
*"Every player action should receive an intelligent response that serves the larger goal of creating an engaging, meaningful experience."*

---

## 🚀 **Features**

### 🎭 **Real AI Direction**
- **Dolphin-Mistral LLM** makes narrative decisions based on game design principles
- **Dynamic pacing analysis** - AI adjusts intensity based on recent player actions
- **Emotional resonance targeting** - Creates moments that genuinely matter
- **Emergent complexity** - Simple rules create complex, interesting situations

### 🌌 **Cosmic Entropy System**
- **Entropy as meaning** - Cosmic entropy represents narrative tension (0-100 scale)
- **Smart entropy management** - AI adjusts entropy based on story weight
- **Reality manipulation** - Entropy changes affect game world and mechanics
- **Timeline anchoring** - Prevent reality drift through Mandela Lock controls

### 🧠 **Persistent Memory**
- **SQLite decision database** - Remembers every choice and outcome
- **Pattern recognition** - Learns what works for different player types
- **Success/failure tracking** - Improves decision-making over time
- **Player preference modeling** - Adapts to individual play styles

### 📸 **Visual Context Awareness**
- **Screenshot analysis** - AI can "see" the current game state
- **Dynamic context replacement** - No more static location templates
- **Visual event tracking** - Responds to what's actually happening on screen
- **Real-time environment analysis** - Describes crowds, energy streams, interface elements

### 🎮 **Game State Management**
- **Complete state tracking** - Characters, world state, narrative threads
- **Real-time modifications** - AI can change relationships, unlock abilities, trigger events
- **Temporal stability monitoring** - Track reality anchors and dimensional integrity
- **Multi-layered decision making** - From narrative to mechanical changes

---

## 🛠 **Technical Architecture**

### **System Components**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│    Godot 4      │◄──►│   File Bridge    │◄──►│ Python EngAIn   │
│   Game Engine   │    │ (JSON Exchange)  │    │   AI Director   │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│ SnapshotManager │    │ DynamicContext   │    │ Ollama/Dolphin  │
│ (Visual Data)   │    │    Manager       │    │    Mistral      │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### **Data Flow**
1. **Player Input** → Godot captures command + visual snapshot
2. **Context Building** → Game state + visual analysis + player history
3. **AI Analysis** → Dolphin-Mistral evaluates situation using design principles
4. **Decision Execution** → AI modifies game state and generates narrative response
5. **Memory Storage** → Decision and outcome stored for future learning

---

## 📋 **Requirements**

### **Software Dependencies**
- **Godot 4.4.1+** - Game engine
- **Python 3.8+** - AI director runtime
- **Ollama** - Local LLM server
- **SQLite** - Persistent memory storage

### **Python Packages**
```bash
pip install requests sqlite3 dataclasses typing
```

### **Ollama Models**
```bash
# Recommended (tested and optimized)
ollama pull dolphin-mistral:latest

# Alternatives
ollama pull llama3.1:8b
ollama pull qwen2.5:14b
ollama pull deepseek-coder:6.7b
```

---

## 🔧 **Installation & Setup**

### **1. Install Ollama**
```bash
# Linux/Mac
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama server
ollama serve
```

### **2. Download Required Model**
```bash
ollama pull dolphin-mistral:latest
```

### **3. Clone/Setup Project**
```bash
cd your-game-directory
# Copy EngAIn files to your project:
# - engain_dolphin.py
# - EngAInBridge.gd  
# - EngAInDragon.gd
# - SnapshotManager.gd
# - DynamicContextManager.gd
```

### **4. Godot Scene Setup**
1. **Add EngAInBridge Node:**
   - Add `Node` as child of your scene root
   - Rename to `EngAInBridge`
   - Attach `EngAInBridge.gd` script

2. **Update Your Character Script:**
   - Replace or modify with `EngAInDragon.gd`
   - Ensure proper node references (`@onready` variables)

3. **Add Support Systems:**
   - Add `SnapshotManager` node with script
   - Add `DynamicContextManager` node with script

### **5. Start EngAIn**
```bash
# In your project directory
python engain_dolphin.py
```

**You should see:**
```
🐍 Python working directory: /your/project/path
🐬 Ollama client initialized with dolphin-mistral:latest
✅ Ollama connection successful
🧠 EngAIn AI Co-Director ready with Ollama
📁 Persistent memory initialized
🎮 Waiting for game input...
```

---

## 🎮 **Usage**

### **Basic Commands**
- Type anything in the game input box
- EngAIn analyzes intent and responds intelligently
- Watch entropy and tension levels change dynamically

### **Special Debug Keys**
- **F10** - Trigger manual AI event ("surprise me")
- **F11** - Show AI director stats and current state
- **F12** - Capture manual snapshot for visual analysis

### **Example Interactions**

```
Player: "hi"
EngAIn: Analyzes as greeting → WORLD_BUILDING response
Result: "The cosmic interface pulses with acknowledgment..."

Player: "how many people are here?"
EngAIn: Analyzes visual context → CHARACTER_DEVELOPMENT
Result: Describes the crowd based on actual screenshot analysis

Player: "where are we?"
EngAIn: Considers narrative pacing → MYSTERY_REVEAL
Result: Reveals location lore appropriate to current tension level
```

---

## 🧠 **AI Decision Framework**

### **Available Actions**
- **WORLD_BUILDING** - Reveal lore, expand environment
- **CHARACTER_DEVELOPMENT** - Develop relationships, growth moments  
- **NARRATIVE_BRANCH** - Create new story paths
- **TENSION_ESCALATION** - Increase stakes, add conflict
- **MYSTERY_REVEAL** - Answer questions, provide clarity
- **PLAYER_CHOICE** - Present meaningful decisions
- **STATE_MODIFICATION** - Change mechanics, unlock abilities
- **ENTROPY_SHIFT** - Major reality changes, timeline alterations
- **CONSEQUENCE_TRIGGER** - Results of past actions

### **Decision Factors**
1. **Player Intent Analysis** - What does the player actually want?
2. **Narrative Momentum** - What serves the story best?
3. **Pacing Considerations** - Recent intensity levels
4. **Character Development** - Relationship opportunities
5. **Entropy Management** - Cosmic significance of actions
6. **Player Psychology** - Emotional state and needs

---

## 📊 **Monitoring & Analytics**

### **Real-Time Metrics**
- **Entropy Level** (0-100) - Cosmic instability/narrative tension
- **Narrative Tension** - Calculated from pending decisions, threads, conflicts
- **Pacing Analysis** - Recent action intensity tracking
- **Decision History** - Success rates of different action types

### **Memory Analytics**
```python
# Access decision database
import sqlite3
db = sqlite3.connect('engain_memory.db')

# View recent decisions
cursor = db.execute("SELECT * FROM decisions ORDER BY timestamp DESC LIMIT 10")
```

### **Visual Context Tracking**
- Screenshot capture with event metadata
- Visual analysis results stored in JSON
- Priority-based retention (Critical events kept forever)
- Automatic cleanup based on storage limits

---

## 🔧 **Configuration**

### **EngAIn Settings** (`engain_dolphin.py`)
```python
# Ollama Model Selection
OLLAMA_MODEL = "dolphin-mistral:latest"

# AI Creativity Settings
TEMPERATURE = 0.8        # Higher = more creative
TOP_P = 0.9             # Nucleus sampling
NUM_PREDICT = 1500      # Max response tokens

# Memory Settings
DECISION_HISTORY_LIMIT = 10    # Decisions to consider
```

### **Snapshot Settings** (`SnapshotManager.gd`)
```gdscript
@export var max_snapshots: int = 1000
@export var max_storage_mb: float = 500.0
@export var purge_older_than_hours: int = 24
```

### **Entropy Settings** (`EngAInBridge.gd`)
```gdscript
# Initial entropy level (0-100)
"entropy_level": 45.0

# Entropy contribution factors
tension += entropy_level * 0.4
tension += pending_decisions.size() * 8.0
tension += narrative_threads.size() * 5.0
```

---

## 🐛 **Troubleshooting**

### **Common Issues**

#### **"AI timeout - used fallback response"**
- **Cause:** Python not receiving requests or Ollama not responding
- **Fix:** Check file paths, ensure Ollama is running, verify model is loaded

#### **"EngAInBridge not found"**
- **Cause:** Node path mismatch in scene tree
- **Fix:** Verify `EngAInBridge` node exists and script is attached

#### **"Ollama connection failed"**
- **Cause:** Ollama server not running or model not loaded
- **Fix:** Run `ollama serve` and `ollama pull dolphin-mistral:latest`

#### **"Parse Error: Expected expression after '['"**
- **Cause:** Python slice syntax used in GDScript
- **Fix:** Replace `array[:5]` with proper GDScript: `array.slice(0, 5)`

### **Debug Logging**
Enable verbose logging in Python:
```python
# Add to main() function
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 🚀 **Advanced Usage**

### **Custom Decision Logic**
Modify `build_director_prompt()` to add domain-specific decision criteria:

```python
def build_director_prompt(self, context, history):
    prompt = f"""
    CUSTOM_CONTEXT:
    - Game Genre: {context.get('game_genre', 'RPG')}
    - Player Skill Level: {context.get('skill_level', 'intermediate')}
    - Session Time: {context.get('session_minutes', 0)} minutes
    
    {base_prompt}
    """
    return prompt
```

### **Visual Analysis Enhancement**
Extend screenshot analysis with computer vision:

```python
# Add to VisionAgent.py
import cv2
import numpy as np

def analyze_screenshot_advanced(self, image_path):
    img = cv2.imread(image_path)
    # Add object detection, text recognition, etc.
    return enhanced_description
```

### **Multi-Character Support**
Extend character tracking for multiple AI agents:

```gdscript
# In EngAInBridge.gd
var character_ais = {
    "dragon": "dolphin-mistral:latest",
    "wizard": "llama3.1:8b", 
    "oracle": "qwen2.5:14b"
}
```

---

## 📚 **API Reference**

### **EngAInBridge Public Methods**

```gdscript
# Send input to AI director
send_to_engain(player_input: String, additional_context: Dictionary = {})

# Get current metrics
get_current_entropy() -> float
get_narrative_tension() -> float

# State management
add_pending_decision(description: String)
resolve_pending_decision(index: int)
update_character_relationship(char_name: String, property: String, value)
trigger_world_event(event_name: String, event_data: Dictionary = {})

# Debug functions
print_current_state()
```

### **Python EngAIn API**

```python
class EngAInDirector:
    def analyze_and_decide(player_input: str, game_state: GameState) -> Dict[str, Any]
    def build_context(player_input: str, state: GameState) -> Dict[str, Any]
    def analyze_player_intent(input_text: str) -> Dict[str, Any]
    def calculate_narrative_tension(state: GameState) -> float

class EngAInMemory:
    def record_decision(player_input, context, action, narrative, changes, rating=0.0)
    def get_decision_history(limit: int = 10) -> List[Dict]
    def update_pattern_success(pattern_type: str, success: bool)
```

---

## 🤝 **Contributing**

### **Design Principles**
1. **Player Agency First** - Every decision should enhance player choice
2. **Narrative Coherence** - Maintain consistent world logic
3. **Emotional Resonance** - Create moments that genuinely matter
4. **Emergent Complexity** - Simple systems producing rich interactions
5. **Transparency** - AI decisions should be understandable and debuggable

### **Code Standards**
- **GDScript:** Follow Godot conventions, use type hints
- **Python:** PEP 8 compliance, comprehensive docstrings
- **Comments:** Explain WHY, not just what
- **Testing:** Include test cases for decision logic

### **Extending EngAIn**
1. **New Action Types:** Add to `action_types` list and implement logic
2. **Custom Metrics:** Extend `calculate_narrative_tension()` 
3. **Memory Enhancements:** Add new tables to `EngAInMemory`
4. **Visual Analysis:** Improve `VisionAgent` with ML models

---

## 📄 **License**

MIT License - Feel free to use, modify, and distribute.

---

## 🙏 **Acknowledgments**

- **Anthropic** - For Claude AI assistance in development
- **Ollama Team** - For local LLM infrastructure
- **Dolphin-Mistral** - For the excellent uncensored model
- **Godot Foundation** - For the amazing game engine

---

## 📞 **Support**

**This is experimental technology.** EngAIn represents a new paradigm in game AI - expect occasional quirks as the field evolves.

**For technical support:**
- Check logs in both Godot console and Python terminal
- Verify Ollama connection: `ollama list` and `ollama ps`
- Ensure all node paths and scripts are correctly assigned
- Monitor `engain_memory.db` for decision patterns

**For advanced usage and customization, study the decision framework and memory system - EngAIn's true power lies in its ability to learn and adapt to your specific game design goals.**

---

*EngAIn: Where artificial intelligence meets genuine game direction.* 🎮🧠✨
