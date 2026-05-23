# Enhanced Trixel Composer: Autonomous AI Artist with Advanced Memory & Optimization
# Implementing research-backed performance and creative intelligence enhancements

import os
import asyncio
import importlib.util
import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Set, Tuple, Optional
from enum import Enum

AIOHTTP_AVAILABLE = importlib.util.find_spec("aiohttp") is not None
if AIOHTTP_AVAILABLE:
    import aiohttp

PYQT5_AVAILABLE = importlib.util.find_spec("PyQt5") is not None
if PYQT5_AVAILABLE:
    from PyQt5 import QtWidgets, QtGui, QtCore

PIL_AVAILABLE = importlib.util.find_spec("PIL") is not None
if PIL_AVAILABLE:
    from PIL import Image, ImageDraw

NUMPY_AVAILABLE = importlib.util.find_spec("numpy") is not None
if NUMPY_AVAILABLE:
    import numpy as np
else:
    np = None

# --- Enhanced Configuration ---
CANVAS_WIDTH = 16
CANVAS_HEIGHT = 16
PIXEL_SIZE = 24
ZW_SESSION_PATH = ".zw/trixel.session"

class CreativePhase(Enum):
    PLANNING = "planning"
    ACTIVE_CREATION = "active_creation"
    REFLECTION = "reflection"
    STYLE_DEVELOPMENT = "style_development"

@dataclass
class CreativeAction:
    tool: str
    x: int
    y: int
    color: Tuple[int, int, int]
    pressure: float = 1.0
    reasoning: str = ""
    timestamp: float = 0.0
    artistic_success: float = 0.5  # 0-1 rating
    
class AutonomousCreativeMemory:
    """Advanced memory system for creative development and style evolution"""
    
    def __init__(self):
        # Short-term: 5-9 items (current session immediate context)
        self.short_term = []
        self.short_term_limit = 7
        
        # Working memory: Session patterns, current artistic goals
        self.working_memory = {
            'current_style_focus': 'exploring',
            'session_theme': 'unknown',
            'tool_preferences': {},
            'color_harmony_patterns': [],
            'composition_strategies': []
        }
        
        # Long-term: Cross-session learning, artistic signature development
        self.long_term = {
            'style_evolution': [],
            'mastered_techniques': {},
            'artistic_preferences': {},
            'creative_breakthroughs': [],
            'failure_learnings': []
        }
        
    def add_creative_experience(self, action: CreativeAction, result_quality: float):
        """Add creative experience to memory with learning integration"""
        experience = {
            'action': asdict(action),
            'result_quality': result_quality,
            'timestamp': time.time(),
            'learning_value': self._calculate_learning_value(action, result_quality)
        }
        
        # Add to short-term
        self.short_term.append(experience)
        if len(self.short_term) > self.short_term_limit:
            # Move oldest to working memory if significant
            old_experience = self.short_term.pop(0)
            if old_experience['learning_value'] > 0.7:
                self._integrate_to_working_memory(old_experience)
        
        # Update tool preferences
        self._update_tool_preferences(action, result_quality)
        
    def _calculate_learning_value(self, action: CreativeAction, quality: float) -> float:
        """Calculate how valuable this experience is for learning"""
        base_value = quality
        
        # Boost value for new techniques or tools
        if action.tool not in self.working_memory['tool_preferences']:
            base_value += 0.2
            
        # Boost value for breakthrough moments (very high or very low quality)
        if quality > 0.9 or quality < 0.2:
            base_value += 0.3
            
        return min(base_value, 1.0)
    
    def _update_tool_preferences(self, action: CreativeAction, quality: float):
        """Update tool mastery and preferences"""
        tool = action.tool
        if tool not in self.working_memory['tool_preferences']:
            self.working_memory['tool_preferences'][tool] = {
                'usage_count': 0,
                'success_rate': 0.5,
                'mastery_level': 0.0
            }
        
        prefs = self.working_memory['tool_preferences'][tool]
        prefs['usage_count'] += 1
        
        # Update success rate with moving average
        alpha = 0.1  # Learning rate
        prefs['success_rate'] = (1 - alpha) * prefs['success_rate'] + alpha * quality
        
        # Update mastery level based on consistency
        if prefs['usage_count'] > 5:
            prefs['mastery_level'] = min(prefs['success_rate'] * (prefs['usage_count'] / 20), 1.0)

if PYQT5_AVAILABLE:
    class OptimizedTrixelCanvas(QtWidgets.QWidget):
        """Performance-optimized canvas with dirty region tracking"""

        def __init__(self, composer):
            super().__init__()
            self.composer = composer
            self.dirty_regions: Set[Tuple[int, int]] = set()
            self.background_buffer = None
            self.last_full_render = 0
            self.setFixedSize(CANVAS_WIDTH * PIXEL_SIZE, CANVAS_HEIGHT * PIXEL_SIZE)

        def mark_dirty(self, x: int, y: int):
            """Mark a pixel region as needing redraw"""
            self.dirty_regions.add((x, y))

        def paintEvent(self, event):
            """Optimized paint event with dirty region tracking"""
            qp = QtGui.QPainter(self)
            current_time = time.time()

            # Full redraw every few seconds or if too many dirty regions
            if (current_time - self.last_full_render > 5.0 or
                len(self.dirty_regions) > CANVAS_WIDTH * CANVAS_HEIGHT * 0.3):
                self._full_redraw(qp)
                self.last_full_render = current_time
                self.dirty_regions.clear()
            else:
                self._partial_redraw(qp)

        def _full_redraw(self, qp):
            """Complete canvas redraw"""
            for y in range(CANVAS_HEIGHT):
                for x in range(CANVAS_WIDTH):
                    color = QtGui.QColor(*self.composer.canvas[y, x])
                    qp.fillRect(x * PIXEL_SIZE, y * PIXEL_SIZE,
                              PIXEL_SIZE, PIXEL_SIZE, color)

        def _partial_redraw(self, qp):
            """Redraw only dirty regions"""
            for x, y in self.dirty_regions:
                if 0 <= x < CANVAS_WIDTH and 0 <= y < CANVAS_HEIGHT:
                    color = QtGui.QColor(*self.composer.canvas[y, x])
                    qp.fillRect(x * PIXEL_SIZE, y * PIXEL_SIZE,
                              PIXEL_SIZE, PIXEL_SIZE, color)
            self.dirty_regions.clear()

class RealTimeCreativeFeedback:
    """Real-time AI feedback system with adaptive response times"""
    
    def __init__(self, composer):
        self.composer = composer
        self.response_targets = {
            'brush_feedback': 100,    # 100ms for stroke analysis
            'style_suggestion': 300,  # 300ms for composition advice  
            'creative_critique': 1000 # 1s for artistic evaluation
        }
        self.feedback_queue = asyncio.Queue()
        
    async def adaptive_feedback(self, canvas_change):
        """Provide adaptive feedback based on creative intensity"""
        intensity = self._calculate_change_intensity(canvas_change)
        
        if intensity > 0.8:  # Heavy artistic work
            return await self.quick_stroke_feedback(canvas_change)
        elif intensity > 0.4:  # Moderate creative work
            return await self.style_suggestion_feedback(canvas_change)
        else:  # Contemplative phase
            return await self.deep_creative_analysis(canvas_change)
    
    def _calculate_change_intensity(self, change) -> float:
        """Calculate artistic intensity of a change"""
        # Simple heuristic based on action type and frequency
        base_intensity = 0.5
        
        if hasattr(change, 'tool') and change.tool == 'brush':
            base_intensity = 0.8
        elif hasattr(change, 'tool') and change.tool == 'fill':
            base_intensity = 0.6
            
        return base_intensity
    
    async def quick_stroke_feedback(self, change):
        """Quick feedback for active drawing"""
        await asyncio.sleep(0.1)  # Simulate 100ms AI processing
        return {
            'type': 'stroke_feedback',
            'message': 'Stroke confidence improving',
            'confidence': 0.8
        }
    
    async def style_suggestion_feedback(self, change):
        """Medium-depth style suggestions"""
        await asyncio.sleep(0.3)  # Simulate 300ms processing
        return {
            'type': 'style_suggestion', 
            'message': 'Consider warmer colors for this area',
            'suggested_color': (200, 150, 100)
        }
    
    async def deep_creative_analysis(self, change):
        """Deep artistic analysis and guidance"""
        await asyncio.sleep(1.0)  # Simulate 1s processing
        return {
            'type': 'creative_critique',
            'message': 'Composition developing strong focal point',
            'artistic_growth': 'style_maturing'
        }

class EnhancedTrixelComposer:
    """Advanced autonomous AI artist with memory, learning, and optimization"""
    
    def __init__(self):
        if not NUMPY_AVAILABLE:
            raise RuntimeError("EnhancedTrixelComposer requires numpy. Install numpy and retry.")

        self.canvas = np.zeros((CANVAS_HEIGHT, CANVAS_WIDTH, 3), dtype=np.uint8)
        self.tool = 'brush'
        self.color = (255, 255, 255)
        self.pressure = 1.0
        
        # Advanced systems
        self.memory = AutonomousCreativeMemory()
        self.creative_feedback = RealTimeCreativeFeedback(self)
        self.creative_phase = CreativePhase.PLANNING
        
        # Empire integration
        self.empire_bridge = None
        self.session_id = f"autonomous_{int(time.time())}"
        
        self.load_tutorials()
        
    def load_tutorials(self):
        """Load tool tutorials for autonomous learning"""
        self.tutorials = {}
        tutorials_dir = Path(".zw/tools")
        if tutorials_dir.exists():
            for file in tutorials_dir.glob("*.txt"):
                self.tutorials[file.stem] = file.read_text()
    
    def perceive(self) -> Dict:
        """Enhanced perception with memory integration"""
        canvas_analysis = self._analyze_canvas_state()
        
        return {
            'canvas': self.canvas.tolist(),
            'canvas_analysis': canvas_analysis,
            'tool': self.tool,
            'color': self.color,
            'creative_phase': self.creative_phase.value,
            'memory_context': {
                'recent_actions': self.memory.short_term[-3:],
                'style_focus': self.memory.working_memory['current_style_focus'],
                'tool_mastery': self.memory.working_memory['tool_preferences']
            }
        }
    
    def _analyze_canvas_state(self) -> Dict:
        """Analyze current canvas for artistic properties"""
        # Simple analysis - could be enhanced with computer vision
        non_zero_pixels = np.count_nonzero(self.canvas.sum(axis=2))
        total_pixels = CANVAS_WIDTH * CANVAS_HEIGHT
        completion = non_zero_pixels / total_pixels
        
        # Color diversity analysis
        unique_colors = len(np.unique(self.canvas.reshape(-1, 3), axis=0))
        
        return {
            'completion_ratio': completion,
            'color_diversity': unique_colors,
            'dominant_colors': self._get_dominant_colors(),
            'composition_balance': self._analyze_composition()
        }
    
    def _get_dominant_colors(self) -> List[Tuple[int, int, int]]:
        """Get dominant colors from canvas"""
        # Simple implementation - could use clustering
        colors = self.canvas.reshape(-1, 3)
        unique_colors = np.unique(colors, axis=0)
        return [tuple(color) for color in unique_colors[:5]]
    
    def _analyze_composition(self) -> Dict:
        """Basic composition analysis"""
        # Center of mass calculation
        y_coords, x_coords = np.mgrid[0:CANVAS_HEIGHT, 0:CANVAS_WIDTH]
        total_mass = np.sum(self.canvas.sum(axis=2))
        
        if total_mass > 0:
            center_x = np.sum(x_coords * self.canvas.sum(axis=2)) / total_mass
            center_y = np.sum(y_coords * self.canvas.sum(axis=2)) / total_mass
        else:
            center_x, center_y = CANVAS_WIDTH // 2, CANVAS_HEIGHT // 2
            
        return {
            'center_of_mass': (float(center_x), float(center_y)),
            'balance_score': self._calculate_balance_score(center_x, center_y)
        }
    
    def _calculate_balance_score(self, center_x: float, center_y: float) -> float:
        """Calculate composition balance (0-1, 1 = perfectly centered)"""
        canvas_center_x = CANVAS_WIDTH / 2
        canvas_center_y = CANVAS_HEIGHT / 2
        
        distance = np.sqrt((center_x - canvas_center_x)**2 + (center_y - canvas_center_y)**2)
        max_distance = np.sqrt((CANVAS_WIDTH/2)**2 + (CANVAS_HEIGHT/2)**2)
        
        return 1.0 - (distance / max_distance)
    
    async def autonomous_create(self, iterations: int = 20):
        """Main autonomous creation loop with memory and learning"""
        print(f"🎨 Starting autonomous creation session: {self.session_id}")
        
        for iteration in range(iterations):
            # 1. Perceive current state
            perception = self.perceive()
            
            # 2. Update creative phase based on progress
            self._update_creative_phase(perception, iteration, iterations)
            
            # 3. Plan next action with memory integration
            plan = await self._autonomous_plan(perception)
            
            # 4. Execute action
            action = CreativeAction(**plan)
            result_quality = self._execute_action(action)
            
            # 5. Learn from action
            self.memory.add_creative_experience(action, result_quality)
            
            # 6. Get real-time feedback
            feedback = await self.creative_feedback.adaptive_feedback(action)
            print(f"🧠 Iteration {iteration}: {feedback['message']}")
            
            # 7. Brief contemplation pause
            await asyncio.sleep(0.2)
        
        # Save autonomous session
        self._save_autonomous_session()
        print("✅ Autonomous creation session complete!")
    
    def _update_creative_phase(self, perception: Dict, iteration: int, total: int):
        """Update creative phase based on progress and state"""
        progress = iteration / total
        completion = perception['canvas_analysis']['completion_ratio']
        
        if progress < 0.2:
            self.creative_phase = CreativePhase.PLANNING
        elif progress < 0.8 and completion < 0.7:
            self.creative_phase = CreativePhase.ACTIVE_CREATION
        elif completion > 0.7:
            self.creative_phase = CreativePhase.REFLECTION
        else:
            self.creative_phase = CreativePhase.STYLE_DEVELOPMENT
    
    async def _autonomous_plan(self, perception: Dict) -> Dict:
        """Enhanced planning with memory and phase awareness"""
        memory_context = perception['memory_context']
        canvas_analysis = perception['canvas_analysis']
        
        # Choose action based on creative phase and memory
        if self.creative_phase == CreativePhase.PLANNING:
            return self._plan_composition_action(canvas_analysis)
        elif self.creative_phase == CreativePhase.ACTIVE_CREATION:
            return self._plan_creative_action(memory_context, canvas_analysis)
        elif self.creative_phase == CreativePhase.REFLECTION:
            return self._plan_refinement_action(memory_context, canvas_analysis)
        else:  # STYLE_DEVELOPMENT
            return self._plan_style_action(memory_context, canvas_analysis)
    
    def _plan_composition_action(self, canvas_analysis: Dict) -> Dict:
        """Plan initial composition actions"""
        # Start with establishing basic structure
        x = CANVAS_WIDTH // 2 + np.random.randint(-2, 3)
        y = CANVAS_HEIGHT // 2 + np.random.randint(-2, 3)
        
        return {
            'tool': 'brush',
            'x': x,
            'y': y,
            'color': self._choose_color_for_phase('foundation'),
            'pressure': 0.8,
            'reasoning': 'establishing_composition_foundation'
        }
    
    def _plan_creative_action(self, memory_context: Dict, canvas_analysis: Dict) -> Dict:
        """Plan main creative actions"""
        # Use tool preferences from memory
        tool_prefs = memory_context.get('tool_mastery', {})
        preferred_tool = max(tool_prefs.keys(), key=lambda t: tool_prefs[t].get('mastery_level', 0)) if tool_prefs else 'brush'
        
        # Choose location based on composition analysis
        center_x, center_y = canvas_analysis['composition_balance']['center_of_mass']
        
        # Add some creative variation around center of mass
        x = int(center_x + np.random.randint(-3, 4))
        y = int(center_y + np.random.randint(-3, 4))
        
        # Clamp to canvas bounds
        x = max(0, min(CANVAS_WIDTH - 1, x))
        y = max(0, min(CANVAS_HEIGHT - 1, y))
        
        return {
            'tool': preferred_tool,
            'x': x,
            'y': y,
            'color': self._choose_color_for_phase('creative'),
            'pressure': np.random.uniform(0.6, 1.0),
            'reasoning': f'creative_expression_with_{preferred_tool}'
        }
    
    def _plan_refinement_action(self, memory_context: Dict, canvas_analysis: Dict) -> Dict:
        """Plan refinement and detail actions"""
        # Focus on empty areas or add details
        x = np.random.randint(0, CANVAS_WIDTH)
        y = np.random.randint(0, CANVAS_HEIGHT)
        
        return {
            'tool': 'brush',
            'x': x,
            'y': y,
            'color': self._choose_color_for_phase('refinement'),
            'pressure': 0.7,
            'reasoning': 'adding_details_and_refinement'
        }
    
    def _plan_style_action(self, memory_context: Dict, canvas_analysis: Dict) -> Dict:
        """Plan style development actions"""
        # Experiment with new techniques or enhance existing style
        x = np.random.randint(0, CANVAS_WIDTH)
        y = np.random.randint(0, CANVAS_HEIGHT)
        
        return {
            'tool': 'brush',
            'x': x,
            'y': y,
            'color': self._choose_color_for_phase('style'),
            'pressure': np.random.uniform(0.3, 0.9),
            'reasoning': 'style_signature_development'
        }
    
    def _choose_color_for_phase(self, phase: str) -> Tuple[int, int, int]:
        """Choose appropriate color based on creative phase"""
        phase_palettes = {
            'foundation': [(139, 69, 19), (160, 82, 45), (210, 180, 140)],  # Earth tones
            'creative': [(255, 140, 0), (255, 69, 0), (255, 215, 0)],      # Warm creative
            'refinement': [(100, 149, 237), (123, 104, 238), (147, 112, 219)], # Cool refinement
            'style': [(255, 20, 147), (255, 105, 180), (255, 182, 193)]    # Expressive style
        }
        
        palette = phase_palettes.get(phase, [(255, 255, 255)])
        return palette[np.random.randint(0, len(palette))]
    
    def _execute_action(self, action: CreativeAction) -> float:
        """Execute action and return quality assessment"""
        # Apply action to canvas
        if 0 <= action.x < CANVAS_WIDTH and 0 <= action.y < CANVAS_HEIGHT:
            self.canvas[action.y, action.x] = action.color
            
        # Simple quality assessment based on composition improvement
        return np.random.uniform(0.3, 0.9)  # Placeholder - could use actual analysis
    
    def _save_autonomous_session(self):
        """Save the autonomous creative session"""
        session_data = {
            'session_id': self.session_id,
            'canvas_final': self.canvas.tolist(),
            'memory_snapshot': {
                'short_term': self.memory.short_term,
                'working_memory': self.memory.working_memory,
                'tool_mastery': self.memory.working_memory['tool_preferences']
            },
            'creative_evolution': self._analyze_creative_growth()
        }
        
        session_file = Path(f".zw/sessions/autonomous_{self.session_id}.json")
        session_file.parent.mkdir(parents=True, exist_ok=True)
        session_file.write_text(json.dumps(session_data, indent=2))

    def _analyze_creative_growth(self) -> Dict:
        """Analyze creative growth during session"""
        tool_prefs = self.memory.working_memory['tool_preferences']
        
        return {
            'tools_explored': len(tool_prefs),
            'mastery_improvements': {tool: data['mastery_level'] 
                                   for tool, data in tool_prefs.items()},
            'style_development': self.memory.working_memory['current_style_focus'],
            'session_success': np.mean([exp.get('result_quality', 0.5) 
                                      for exp in self.memory.short_term])
        }

# Enhanced UI Integration
if PYQT5_AVAILABLE:
    class EnhancedComposerUI(QtWidgets.QWidget):
        def __init__(self, composer):
            super().__init__()
            self.setWindowTitle("Trixel Composer - Autonomous AI Artist")
            self.composer = composer
            self.canvas_widget = OptimizedTrixelCanvas(composer)

            # Layout
            layout = QtWidgets.QVBoxLayout()

            # Canvas
            layout.addWidget(self.canvas_widget)

            # Control panel
            controls = QtWidgets.QHBoxLayout()

            # Autonomous creation button
            auto_button = QtWidgets.QPushButton("Start Autonomous Creation")
            auto_button.clicked.connect(self.start_autonomous_creation)
            controls.addWidget(auto_button)

            # Phase indicator
            self.phase_label = QtWidgets.QLabel("Phase: Planning")
            controls.addWidget(self.phase_label)

            layout.addLayout(controls)
            self.setLayout(layout)

            # Timer for UI updates
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.update_ui)
            self.timer.start(100)  # Update every 100ms

        def start_autonomous_creation(self):
            """Start autonomous creation in separate thread"""
            import threading

            def run_creation():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.composer.autonomous_create(20))
                loop.close()

            thread = threading.Thread(target=run_creation)
            thread.daemon = True
            thread.start()

        def update_ui(self):
            """Update UI elements"""
            self.phase_label.setText(f"Phase: {self.composer.creative_phase.value}")
            self.canvas_widget.update()

# Launch Enhanced System
if __name__ == '__main__':
    import sys

    if not PYQT5_AVAILABLE:
        raise RuntimeError("PyQt5 is required to launch the enhanced GUI. Install PyQt5 and retry.")

    app = QtWidgets.QApplication(sys.argv)
    composer = EnhancedTrixelComposer()
    ui = EnhancedComposerUI(composer)
    ui.show()
    sys.exit(app.exec_())
