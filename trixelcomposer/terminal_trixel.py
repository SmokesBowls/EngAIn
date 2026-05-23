#!/usr/bin/env python3
# Terminal-Based Trixel Composer: Autonomous AI Artist (No GUI Dependencies)
# Runs immediately with just the Python 3 standard library (Pillow optional for PNG export)

import os
import sys
import asyncio
import argparse
import json
import time
import random
import importlib.util
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple
from enum import Enum
from typing import Dict, List, Optional, Tuple

# --- Configuration ---
CANVAS_WIDTH = 16
CANVAS_HEIGHT = 16
ZW_SESSION_PATH = ".zw/trixel.session"

OLLAMA_AVAILABLE = False
LMDB_AVAILABLE = False
ollama = None
lmdb = None

try:
    OLLAMA_AVAILABLE = importlib.util.find_spec("ollama") is not None
except Exception:
    OLLAMA_AVAILABLE = False
if OLLAMA_AVAILABLE:
    import ollama

try:
    LMDB_AVAILABLE = importlib.util.find_spec("lmdb") is not None
except Exception:
    LMDB_AVAILABLE = False
if LMDB_AVAILABLE:
    import lmdb

class CreativePhase(Enum):
    PLANNING = "planning"
    ACTIVE_CREATION = "active_creation"
    REFLECTION = "reflection"
    STYLE_DEVELOPMENT = "style_development"


class ZWArtIntentManager:
    """Lightweight ZW art intent loader → Ollama prompt → runtime influence."""

    def __init__(self, intent_path: Path = Path(".zw/art.intent")):
        self.intent_path = Path(intent_path)
        self.intent: Dict[str, str] = {}
        self.ollama_prompt: str = ""
        self.palette_colors: Optional[List[Tuple[int, int, int]]] = None
        self._load_intent()

    def _load_intent(self):
        raw_block = None

        if self.intent_path.exists():
            raw_block = self.intent_path.read_text()
        elif os.environ.get("ZW_ART_INTENT"):
            raw_block = os.environ["ZW_ART_INTENT"]

        if not raw_block:
            return

        parsed = self.parse_block(raw_block)
        if not parsed:
            print("⚠️ Could not parse ZW art intent; continuing autonomously.")
            return

        self.intent = parsed
        self.ollama_prompt = self._build_ollama_prompt(parsed)
        self.palette_colors = self._resolve_palette(parsed.get("palette"))

        print("🧱 Loaded ZW art intent → Ollama prompt ready:")
        print(f"    theme: {parsed.get('theme', 'unspecified')}")
        if parsed.get("palette"):
            print(f"    palette: {parsed['palette']}")

    def parse_block(self, block: str) -> Dict[str, str]:
        # Trim any leading protocol markers
        if "!zw/art.intent" in block:
            block = block.split("!zw/art.intent", 1)[-1]

        # Extract key: value pairs (very small YAML/JSON subset)
        intent: Dict[str, str] = {}
        for line in block.splitlines():
            line = line.strip().strip("{}")
            if not line or line.startswith("!"):
                continue
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip().strip("\"'")
            value = value.strip().strip(",")
            value = value.strip().strip("\"'")
            if key:
                intent[key] = value

        return intent

    def _build_ollama_prompt(self, intent: Dict[str, str]) -> str:
        theme = intent.get("theme", "unknown theme")
        palette = intent.get("palette", "custom")
        density = intent.get("density", "balanced")
        style = intent.get("style", "adaptive")
        return (
            "You are a pixel artist collaborating with a Trixel canvas. "
            f"Paint a scene matching the theme '{theme}' in the '{palette}' palette. "
            f"Keep stroke density {density} and push toward a {style} aesthetic."
        )

    def _resolve_palette(self, palette_name: Optional[str]) -> Optional[List[Tuple[int, int, int]]]:
        if not palette_name:
            return None

        palette_library = {
            "obsidian_fire": [(255, 69, 0), (255, 140, 0), (139, 0, 0)],
            "aurora_glow": [(72, 209, 204), (123, 104, 238), (255, 250, 205)],
            "fractaline": [(199, 21, 133), (65, 105, 225), (32, 178, 170)],
            "verdant_realm": [(46, 139, 87), (107, 142, 35), (189, 183, 107)],
        }
        return palette_library.get(palette_name.lower())

@dataclass
class CreativeAction:
    tool: str
    x: int
    y: int
    color: Tuple[int, int, int]
    pressure: float = 1.0
    reasoning: str = ""
    timestamp: float = 0.0
    artistic_success: float = 0.5

class TerminalCanvas:
    """ASCII art representation of canvas for terminal display"""

    def __init__(self, width=16, height=16):
        self.width = width
        self.height = height
        self.canvas = [[[0, 0, 0] for _ in range(width)] for _ in range(height)]

    def set_pixel(self, x, y, color):
        """Set pixel color"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.canvas[y][x] = list(color)

    def _pixel_sum(self, pixel):
        return sum(pixel)

    def display(self):
        """Display canvas as ASCII art with color indicators"""
        print("\n" + "="*50)
        print("🎨 TRIXEL COMPOSER - AUTONOMOUS AI ARTIST")
        print("="*50)

        # Create ASCII representation
        for y in range(self.height):
            row = ""
            for x in range(self.width):
                pixel_sum = self._pixel_sum(self.canvas[y][x])
                if pixel_sum == 0:  # Black/empty
                    row += "  "
                elif pixel_sum < 150:  # Dark colors
                    row += "▓▓"
                elif pixel_sum < 400:  # Medium colors
                    row += "▒▒"
                else:  # Light colors
                    row += "░░"
            print(f"|{row}|")

        print("="*50)

    def get_stats(self):
        """Get canvas statistics"""
        non_zero_pixels = sum(
            1 for row in self.canvas for pixel in row if self._pixel_sum(pixel) != 0
        )
        total_pixels = self.width * self.height
        completion = non_zero_pixels / total_pixels

        unique_colors = {tuple(pixel) for row in self.canvas for pixel in row}
        unique_colors.discard((0, 0, 0))

        return {
            'completion': completion,
            'colors_used': len(unique_colors),
            'pixels_painted': non_zero_pixels
        }

class AutonomousCreativeMemory:
    """Simplified memory system for autonomous learning"""

    def __init__(self):
        self.short_term = []
        self.tool_preferences = {}
        self.style_evolution = []
        self.session_learnings = []
        self.total_experiences = 0
        
    def add_experience(self, action: CreativeAction, quality: float):
        """Add creative experience to memory"""
        experience = {
            'action': asdict(action),
            'quality': quality,
            'timestamp': time.time()
        }
        
        self.short_term.append(experience)
        if len(self.short_term) > 10:
            self.short_term.pop(0)
            
        # Update tool preferences
        tool = action.tool
        if tool not in self.tool_preferences:
            self.tool_preferences[tool] = {'usage': 0, 'avg_quality': 0.5}
            
        prefs = self.tool_preferences[tool]
        prefs['usage'] += 1

        # Moving average for quality
        alpha = 0.2
        prefs['avg_quality'] = (1 - alpha) * prefs['avg_quality'] + alpha * quality

        self.total_experiences += 1

    def get_preferred_tool(self):
        """Get currently preferred tool based on success"""
        if not self.tool_preferences:
            return 'brush'
            
        best_tool = max(self.tool_preferences.keys(), 
                       key=lambda t: self.tool_preferences[t]['avg_quality'])
        return best_tool
        
    def get_memory_summary(self):
        """Get summary of current memory state"""
        return {
            'experiences': self.total_experiences,
            'tools_learned': len(self.tool_preferences),
            'preferred_tool': self.get_preferred_tool(),
            'tool_mastery': {tool: f"{data['avg_quality']:.2f}"
                           for tool, data in self.tool_preferences.items()}
        }

    def serialize(self):
        return {
            'short_term': self.short_term,
            'tool_preferences': self.tool_preferences,
            'style_evolution': self.style_evolution,
            'session_learnings': self.session_learnings,
            'total_experiences': self.total_experiences,
        }

    def load(self, data: Dict):
        self.short_term = data.get('short_term', [])
        self.tool_preferences = data.get('tool_preferences', {})
        self.style_evolution = data.get('style_evolution', [])
        self.session_learnings = data.get('session_learnings', [])
        self.total_experiences = data.get('total_experiences', len(self.short_term))


class SnapshotManager:
    """Manage rolling canvas snapshots for continuity across sessions."""

    def __init__(self, snapshot_file: Path, max_snapshots: int = 10):
        self.snapshot_file = snapshot_file
        self.max_snapshots = max_snapshots
        self.snapshots: List[List[List[List[int]]]] = []
        self._load_snapshots()

    def _load_snapshots(self):
        if self.snapshot_file.exists():
            try:
                with open(self.snapshot_file, "r") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self.snapshots = data[-self.max_snapshots:]
            except Exception as e:
                print(f"⚠️ Could not load snapshots: {e}")

    def record_snapshot(self, canvas_state: List[List[List[int]]]):
        # Deep copy via JSON to avoid reference issues
        safe_copy = json.loads(json.dumps(canvas_state))
        self.snapshots.append(safe_copy)
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots = self.snapshots[-self.max_snapshots:]
        self._persist()

    def latest_snapshot(self) -> Optional[List[List[List[int]]]]:
        return self.snapshots[-1] if self.snapshots else None

    def _persist(self):
        self.snapshot_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.snapshot_file, "w") as f:
                json.dump(self.snapshots[-self.max_snapshots:], f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save snapshots: {e}")

class ExperienceStore:
    """Persist action-level learning traces for replay and offline training."""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.backend = "lmdb" if LMDB_AVAILABLE else "jsonl"
        self.log_path = self.base_dir / "experience_log.jsonl"
        self.counter_path = self.base_dir / "experience_counter.txt"
        self.env = None

        if self.backend == "lmdb":
            try:
                self.env = lmdb.open(
                    str(self.base_dir / "experience.lmdb"),
                    map_size=64 * 1024 * 1024,
                    subdir=False,
                    create=True,
                )
            except Exception as e:
                print(f"⚠️ LMDB unavailable at runtime ({e}); falling back to JSONL event log.")
                self.backend = "jsonl"

    def _next_id(self) -> int:
        last = 0
        if self.counter_path.exists():
            try:
                last = int(self.counter_path.read_text().strip() or "0")
            except Exception:
                last = 0
        current = last + 1
        self.counter_path.write_text(str(current))
        return current

    def _serialize(self, event: Dict) -> bytes:
        return json.dumps(event, separators=(",", ":")).encode("utf-8")

    def record(
        self,
        session_id: str,
        iteration: int,
        phase: str,
        action: CreativeAction,
        quality: float,
        canvas_stats: Dict,
    ) -> None:
        event_id = self._next_id()
        event = {
            "id": event_id,
            "session_id": session_id,
            "iteration": iteration,
            "phase": phase,
            "quality": quality,
            "action": asdict(action),
            "canvas_stats": canvas_stats,
            "recorded_at": time.time(),
        }

        if self.backend == "lmdb" and self.env is not None:
            try:
                with self.env.begin(write=True) as txn:
                    txn.put(f"event:{event_id:09d}".encode("utf-8"), self._serialize(event))
            except Exception as e:
                print(f"⚠️ LMDB write failed ({e}); writing event to JSONL fallback.")
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event) + "\n")
            return

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")


class TerminalTrixelComposer:
    """Terminal-based autonomous AI artist"""

    def __init__(self):
        self.canvas = TerminalCanvas()
        self.memory = AutonomousCreativeMemory()
        self.creative_phase = CreativePhase.PLANNING
        self.session_id = f"terminal_{int(time.time())}"
        self.intent_manager = ZWArtIntentManager()
        self.ollama_model: Optional[str] = None
        self.snapshot_manager = SnapshotManager(Path(".zw/snapshots.json"))
        self.memory_path = Path(".zw/memory.json")
        self.experience_store = ExperienceStore(Path(".zw"))
        self.keystroke_log_path = Path(".zw/keystrokes.jsonl")

        self._load_memory()

        # Restore the latest snapshot if available
        latest_canvas = self.snapshot_manager.latest_snapshot()
        if latest_canvas:
            self.canvas.canvas = latest_canvas
            print(f"📸 Loaded {len(self.snapshot_manager.snapshots)} canvas snapshots; resuming from latest state.")
            self.creative_phase = CreativePhase.ACTIVE_CREATION
        else:
            print("📸 No existing snapshots found; starting a fresh canvas.")

        print(f"🗂️ Experience store backend: {self.experience_store.backend}")
        
        # Color palettes for different phases
        self.phase_colors = {
            'planning': [(139, 69, 19), (160, 82, 45), (205, 133, 63)],
            'active': [(255, 140, 0), (255, 69, 0), (255, 215, 0)],
            'reflection': [(100, 149, 237), (123, 104, 238), (147, 112, 219)],
            'style': [(255, 20, 147), (255, 105, 180), (255, 182, 193)]
        }

        if self.intent_manager.palette_colors:
            self.phase_colors['planning'] = self.intent_manager.palette_colors
            self.phase_colors['active'] = self.intent_manager.palette_colors
            self.phase_colors['reflection'] = self.intent_manager.palette_colors
            self.phase_colors['style'] = self.intent_manager.palette_colors

        self._configure_ollama_model()

    def _record_keystroke(self, prompt: str, value: str):
        event = {
            "session_id": self.session_id,
            "prompt": prompt,
            "value": value,
            "length": len(value),
            "timestamp": time.time(),
        }
        self.keystroke_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.keystroke_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def _safe_input(self, prompt: str) -> str:
        if not sys.stdin.isatty():
            print("⚠️ Non-interactive mode detected; using default Ollama selection.")
            return ""
        try:
            value = input(prompt)
            self._record_keystroke(prompt, value)
            return value
        except EOFError:
            return ""

    def _configure_ollama_model(self):
        if not OLLAMA_AVAILABLE:
            print("⚠️ Ollama not installed; running without LLM guidance.")
            return

        available_models: List[str] = []
        try:
            response = ollama.list()
            available_models = [m.get("name") for m in response.get("models", []) if m.get("name")]
        except Exception as e:
            print(f"⚠️ Could not list Ollama models: {e}")

        if available_models:
            print("🤖 Available Ollama models detected on this machine:")
            for idx, name in enumerate(available_models, start=1):
                print(f"   {idx}. {name}")

            choice = self._safe_input("Select an Ollama model (press Enter for default 1, or 0 to skip): ").strip()

            if choice == "0":
                print("🚫 Ollama guidance disabled by user choice.")
                return

            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(available_models):
                    self.ollama_model = available_models[idx - 1]
            if not self.ollama_model:
                self.ollama_model = available_models[0]
        else:
            manual = self._safe_input("Enter an Ollama model to use (leave blank to skip): ").strip()
            if manual:
                self.ollama_model = manual

        if self.ollama_model:
            print(f"🧠 Ollama guidance enabled with model: {self.ollama_model}")
        else:
            print("⚙️ Continuing without Ollama-driven planning.")

    def ollama_brain(self, prompt: str) -> Optional[str]:
        if not (self.ollama_model and OLLAMA_AVAILABLE):
            return None
        try:
            response = ollama.chat(
                model=self.ollama_model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.get("message", {}).get("content")
        except Exception as e:
            print(f"⚠️ Ollama error: {e}")
            return None
        
    def perceive(self):
        """Analyze current canvas state"""
        stats = self.canvas.get_stats()
        if hasattr(self.memory, "get_memory_summary"):
            memory_summary = self.memory.get_memory_summary()
        else:
            experiences = len(getattr(self.memory, "short_term", []))
            tools = getattr(self.memory, "tool_preferences", {})
            memory_summary = {
                'experiences': experiences,
                'tools_learned': len(tools),
                'preferred_tool': getattr(self.memory, "get_preferred_tool", lambda: "brush")(),
                'tool_mastery': {tool: "unknown" for tool in tools}
            }

        return {
            'canvas_stats': stats,
            'memory_state': memory_summary,
            'phase': self.creative_phase.value,
            'session_id': self.session_id
        }
        
    def plan_action(self, perception):
        """Plan next creative action based on phase and memory"""
        stats = perception['canvas_stats']
        memory = perception['memory_state']

        # Choose location
        if self.creative_phase == CreativePhase.PLANNING:
            # Start near center
            x = CANVAS_WIDTH // 2 + random.randint(-2, 2)
            y = CANVAS_HEIGHT // 2 + random.randint(-2, 2)
            if random.random() < 0.25:
                x = random.randint(0, CANVAS_WIDTH - 1)
                y = random.randint(0, CANVAS_HEIGHT - 1)
        else:
            # Random exploration with some bias toward existing work
            if stats['completion'] > 0.3:
                # Bias toward existing pixels
                x = random.randint(max(0, CANVAS_WIDTH//2 - 4),
                                 min(CANVAS_WIDTH-1, CANVAS_WIDTH//2 + 4))
                y = random.randint(max(0, CANVAS_HEIGHT//2 - 4), 
                                 min(CANVAS_HEIGHT-1, CANVAS_HEIGHT//2 + 4))
            else:
                x = random.randint(0, CANVAS_WIDTH - 1)
                y = random.randint(0, CANVAS_HEIGHT - 1)
        
        # Choose tool based on memory or default
        tool = memory.get('preferred_tool', 'brush')
        
        # Choose color based on phase
        phase_key = {
            CreativePhase.PLANNING: 'planning',
            CreativePhase.ACTIVE_CREATION: 'active',
            CreativePhase.REFLECTION: 'reflection',
            CreativePhase.STYLE_DEVELOPMENT: 'style'
        }.get(self.creative_phase, 'active')
        
        colors = self.phase_colors[phase_key]
        color = colors[random.randint(0, len(colors) - 1)]

        # Optional Ollama-driven guidance overlays tool/color choices
        ollama_notes = ""
        if self.intent_manager and self.intent_manager.ollama_prompt:
            ollama_context = self.intent_manager.ollama_prompt
        else:
            ollama_context = ""

        ollama_prompt = (
            f"Canvas stats: {stats}\n"
            f"Memory: {memory}\n"
            f"Phase: {self.creative_phase.value}\n"
            f"ZW intent: {ollama_context or 'none'}\n\n"
            "Respond ONLY as JSON with keys tool and color, e.g. "
            "{\"tool\": \"brush\", \"color\": [r,g,b]}"
        )

        brain = self.ollama_brain(ollama_prompt)
        if brain:
            try:
                data = json.loads(brain)
                tool = data.get("tool", tool)
                color_data = data.get("color", color)
                if isinstance(color_data, (list, tuple)) and len(color_data) == 3:
                    color = tuple(int(c) for c in color_data)
                ollama_notes = "ollama_guided"
            except Exception:
                ollama_notes = "ollama_parse_failed"

        intent_theme = ""
        if self.intent_manager and self.intent_manager.intent:
            intent_theme = self.intent_manager.intent.get("theme", "").strip().replace(" ", "_")

        return CreativeAction(
            tool=tool,
            x=x,
            y=y,
            color=color,
            pressure=random.uniform(0.5, 1.0),
            reasoning=f"{self.creative_phase.value}_action"
            + (f"_{intent_theme}" if intent_theme else "")
            + (f"_{ollama_notes}" if ollama_notes else ""),
            timestamp=time.time()
        )
        
    def execute_action(self, action: CreativeAction):
        """Execute creative action and assess quality"""
        self.canvas.set_pixel(action.x, action.y, action.color)
        
        # Simple quality assessment
        stats = self.canvas.get_stats()
        
        # Quality factors
        base_quality = 0.5
        
        # Reward progress
        if stats['completion'] > 0.1:
            base_quality += 0.2
            
        # Reward color diversity
        if stats['colors_used'] > 3:
            base_quality += 0.1
            
        # Add some randomness for experimentation
        quality = base_quality + random.uniform(-0.2, 0.3)
        quality = max(0.0, min(1.0, quality))
        
        return quality
        
    def update_phase(self, perception):
        """Update creative phase based on progress"""
        completion = perception['canvas_stats']['completion']
        experiences = max(len(self.memory.short_term), getattr(self.memory, 'total_experiences', 0))

        if self.creative_phase == CreativePhase.PLANNING and (
            completion > 0.08 or experiences >= 5
        ):
            self.creative_phase = CreativePhase.ACTIVE_CREATION
        elif self.creative_phase == CreativePhase.ACTIVE_CREATION and completion >= 0.6:
            self.creative_phase = CreativePhase.REFLECTION
        elif self.creative_phase == CreativePhase.REFLECTION and completion >= 0.8:
            self.creative_phase = CreativePhase.STYLE_DEVELOPMENT
            
    async def autonomous_create(self, iterations=100):
        """Main autonomous creation loop"""
        print("🚀 STARTING AUTONOMOUS AI ARTIST SESSION")
        print(f"Session ID: {self.session_id}")
        
        for i in range(iterations):
            print(f"\n--- Iteration {i+1}/{iterations} ---")
            
            # 1. Perceive
            perception = self.perceive()
            
            # 2. Update phase
            self.update_phase(perception)
            
            # 3. Plan action
            action = self.plan_action(perception)
            
            # 4. Execute and assess
            quality = self.execute_action(action)
            
            # 5. Learn from experience
            self.memory.add_experience(action, quality)
            self.experience_store.record(
                session_id=self.session_id,
                iteration=i + 1,
                phase=self.creative_phase.value,
                action=action,
                quality=quality,
                canvas_stats=self.canvas.get_stats(),
            )

            # 6. Display progress
            print(f"🧠 Phase: {self.creative_phase.value}")
            print(f"🎨 Action: {action.tool} at ({action.x},{action.y}) - Quality: {quality:.2f}")
            print(f"📊 Canvas: {perception['canvas_stats']['completion']:.1%} complete, {perception['canvas_stats']['colors_used']} colors")
            print(f"🎯 Memory: {perception['memory_state']['experiences']} experiences, preferred tool: {perception['memory_state']['preferred_tool']}")

            # Snapshot the canvas after each stroke for continuity
            self.snapshot_manager.record_snapshot(self.canvas.canvas)
            
            # Display canvas every few iterations
            if (i + 1) % 5 == 0 or i == iterations - 1:
                self.canvas.display()
                
            # Brief pause for readability
            await asyncio.sleep(0.3)
            
        # Final session summary
        await self.session_summary()
        
    async def replay_experience_jsonl(
        self,
        jsonl_path: Path,
        delay: float = 0.15,
        clear_canvas: bool = True,
        max_events: Optional[int] = None,
    ):
        """Replay stroke events from a JSONL log onto the canvas."""
        path = Path(jsonl_path)
        if not path.exists():
            raise FileNotFoundError(f"Replay file not found: {path}")

        if clear_canvas:
            self.canvas = TerminalCanvas(width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
            print("🧼 Cleared canvas for replay.")

        print(f"🎬 Replaying strokes from: {path}")
        applied = 0
        skipped = 0

        with open(path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                if not line.strip():
                    continue

                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    skipped += 1
                    continue

                action_data = payload.get("action", payload)
                x = action_data.get("x")
                y = action_data.get("y")
                color = action_data.get("color")

                if not (isinstance(x, int) and isinstance(y, int)):
                    skipped += 1
                    continue
                if not (isinstance(color, (list, tuple)) and len(color) == 3):
                    skipped += 1
                    continue

                color_tuple = tuple(int(c) for c in color)
                self.canvas.set_pixel(x, y, color_tuple)
                applied += 1

                quality = payload.get("quality")
                quality_text = f"{float(quality):.2f}" if isinstance(quality, (int, float)) else "n/a"
                print(
                    f"🎞️ Replay {applied}: line {line_no} -> ({x},{y}) color={color_tuple} quality={quality_text}"
                )
                self.canvas.display()

                if delay > 0:
                    await asyncio.sleep(delay)

                if max_events is not None and applied >= max_events:
                    break

        stats = self.canvas.get_stats()
        print(
            f"✅ Replay complete: applied={applied}, skipped={skipped}, "
            f"completion={stats['completion']:.1%}, colors={stats['colors_used']}"
        )

    async def session_summary(self):
        """Display final session summary"""
        perception = self.perceive()
        
        print("\n" + "🌟"*20)
        print("AUTONOMOUS CREATION SESSION COMPLETE")
        print("🌟"*20)
        
        print(f"\n📈 Session Statistics:")
        print(f"   Canvas Completion: {perception['canvas_stats']['completion']:.1%}")
        print(f"   Pixels Painted: {perception['canvas_stats']['pixels_painted']}")
        print(f"   Colors Used: {perception['canvas_stats']['colors_used']}")
        print(f"   Creative Experiences: {perception['memory_state']['experiences']}")
        
        print(f"\n🧠 AI Learning Progress:")
        print(f"   Tools Mastered: {perception['memory_state']['tools_learned']}")
        print(f"   Preferred Tool: {perception['memory_state']['preferred_tool']}")
        print(f"   Tool Mastery Levels:")
        for tool, mastery in perception['memory_state']['tool_mastery'].items():
            print(f"      {tool}: {mastery}")
            
        print(f"\n🎨 Final Artistic Phase: {self.creative_phase.value}")
        if self.ollama_model:
            print(f"🤖 Ollama model: {self.ollama_model}")
        if self.intent_manager.intent:
            print("\n🧱 ZW Art Intent ➜ Ollama prompt:")
            print(f"   Theme: {self.intent_manager.intent.get('theme', 'unspecified')}")
            if self.intent_manager.ollama_prompt:
                print(f"   Prompt: {self.intent_manager.ollama_prompt}")

        # Save session
        self.save_session()
        print(f"\n💾 Session saved to: .zw/sessions/{self.session_id}.json")

    def save_session(self):
        """Save session data with proper type conversion"""

        def convert_types(obj):
            """Convert complex types to JSON-serializable Python types"""
            if isinstance(obj, dict):
                return {key: convert_types(value) for key, value in obj.items()}
            if isinstance(obj, list):
                return [convert_types(item) for item in obj]
            return obj

        session_data = {
            'session_id': self.session_id,
            'canvas': self.canvas.canvas,
            'final_stats': convert_types(self.canvas.get_stats()),
            'memory_summary': convert_types(self.memory.get_memory_summary()),
            'final_phase': self.creative_phase.value,
            'experiences': convert_types(self.memory.short_term),
            'experience_store_backend': self.experience_store.backend,
            'experience_log_path': str(self.experience_store.log_path),
            'keystroke_log_path': str(self.keystroke_log_path),
        }
        
        session_dir = Path(".zw/sessions")
        session_dir.mkdir(parents=True, exist_ok=True)
        
        session_file = session_dir / f"{self.session_id}.json"
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        print(f"💾 Session saved successfully to: {session_file}")

        # Save rolling snapshots to disk for continuity across runs
        self.snapshot_manager.record_snapshot(self.canvas.canvas)

        # Persist memory for cross-session learning
        self._save_memory()

    def _save_memory(self):
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.memory_path, "w") as f:
                json.dump(self.memory.serialize(), f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save memory: {e}")

    def _load_memory(self):
        if self.memory_path.exists():
            try:
                with open(self.memory_path, "r") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self.memory.load(data)
                    print("🧠 Loaded prior creative memory for continuity across sessions.")
            except Exception as e:
                print(f"⚠️ Could not load memory: {e}")

async def main(
    replay_jsonl: Optional[str] = None,
    replay_delay: float = 0.15,
    replay_limit: Optional[int] = None,
    clear_replay_canvas: bool = True,
):
    """Main entry point"""
    print("🎨 TRIXEL COMPOSER: AUTONOMOUS AI ARTIST")
    print("=" * 50)
    print("🚀 Initializing autonomous creative intelligence...")

    composer = TerminalTrixelComposer()

    # Show initial canvas
    composer.canvas.display()

    if replay_jsonl:
        await composer.replay_experience_jsonl(
            jsonl_path=Path(replay_jsonl),
            delay=max(0.0, replay_delay),
            clear_canvas=clear_replay_canvas,
            max_events=replay_limit,
        )
        return

    print("\n⏳ Starting autonomous creation in 3 seconds...")
    await asyncio.sleep(3)

    # Begin autonomous creation
    await composer.autonomous_create(30)

    print("\n✨ Autonomous AI artist session complete!")
    print("🎯 Check .zw/sessions/ folder for saved session data")

# PNG Export Patch - Add this before the main section
def apply_png_patch():
    """Apply PNG export capabilities to existing classes"""
    
    def to_png(self, output_dir=".", session_id="", scale=20):
        try:
            from PIL import Image
        except ImportError:
            print("⚠️ Pillow not available; skipping PNG export.")
            return None

        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            scaled_rows = []
            for row in self.canvas:
                expanded_row = []
                for pixel in row:
                    expanded_row.extend([tuple(pixel)] * scale)
                for _ in range(scale):
                    scaled_rows.extend(expanded_row)

            img = Image.new('RGB', (self.width * scale, self.height * scale))
            img.putdata(scaled_rows)

            filename = f"trixel_{session_id}_{int(time.time())}.png"
            png_file = output_path / filename

            img.save(png_file)
            print(f"🎨 Artwork exported: {png_file}")
            return png_file
        except Exception as e:
            print(f"❌ PNG export failed: {e}")
            return None
    
    # Add PNG export to TerminalCanvas
    TerminalCanvas.to_png = to_png
    
    # Enhanced save_session with PNG export
    original_save = TerminalTrixelComposer.save_session
    
    def enhanced_save_with_png(self):
        # Call original save method
        original_save(self)
        
        # Export PNG artwork
        artwork_dir = Path(".zw/artwork")
        artwork_dir.mkdir(parents=True, exist_ok=True)
        
        png_file = self.canvas.to_png(
            output_dir=str(artwork_dir),
            session_id=self.session_id
        )
        
        if png_file:
            print(f"🎨✨ Your AI's artwork is now visible: {png_file}")
    
    TerminalTrixelComposer.save_session = enhanced_save_with_png

# Apply the PNG patch
apply_png_patch()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Terminal Trixel Composer")
    parser.add_argument("--replay-jsonl", help="Replay strokes from a JSONL file")
    parser.add_argument("--replay-delay", type=float, default=0.15, help="Delay between replayed strokes (seconds)")
    parser.add_argument("--replay-limit", type=int, default=None, help="Optional max number of replay events")
    parser.add_argument("--no-clear-replay-canvas", action="store_true", help="Do not clear the current canvas before replay")
    args = parser.parse_args()

    try:
        asyncio.run(
            main(
                replay_jsonl=args.replay_jsonl,
                replay_delay=args.replay_delay,
                replay_limit=args.replay_limit,
                clear_replay_canvas=not args.no_clear_replay_canvas,
            )
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Session interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("💡 Make sure you have Python 3.7+ available; optional Pillow enables PNG export")


# Empire Art Bridge: AI-to-AI Artistic Collaboration System
# Optional Empire integration stubs for offline compatibility.
# Requires aiohttp and remote services; disabled by default.

def enable_empire_mode():
    print('🏰 Empire mode is unavailable because optional dependencies are not installed.')
    print('Run `pip install aiohttp` and connect to an Empire broker to enable it.')


async def launch_empire_collaborative_session():
    raise RuntimeError('Empire collaborative mode requires optional aiohttp dependency')
