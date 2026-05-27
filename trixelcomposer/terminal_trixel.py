#!/usr/bin/env python3
"""Terminal-Based Trixel Composer: Autonomous AI Artist.

Runs with the Python 3 standard library. Optional dependencies:
- Pillow for PNG export
- ollama for LLM-guided planning
- lmdb for experience storage
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import os
import random
import sys
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import entity_layer as _entity_layer

CANVAS_WIDTH = 16
CANVAS_HEIGHT = 16
DEFAULT_SNAPSHOT_PATH = Path(".zw/snapshots.json")
DEFAULT_MEMORY_PATH = Path(".zw/memory.json")
DEFAULT_SESSION_DIR = Path(".zw/sessions")
DEFAULT_ARTWORK_DIR = Path(".zw/artwork")
DEFAULT_ZW_DIR = Path(".zw")

# Optional dependencies -------------------------------------------------------
OLLAMA_AVAILABLE = importlib.util.find_spec("ollama") is not None
LMDB_AVAILABLE = importlib.util.find_spec("lmdb") is not None
PILLOW_AVAILABLE = importlib.util.find_spec("PIL") is not None

ollama = None
lmdb = None
Image = None

if OLLAMA_AVAILABLE:
    import ollama  # type: ignore[assignment]
if LMDB_AVAILABLE:
    import lmdb  # type: ignore[assignment]
if PILLOW_AVAILABLE:
    from PIL import Image  # type: ignore[assignment]


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
    artistic_success: float = 0.5


class ZWArtIntentManager:
    """Loads simple ZW art intent data and converts it into runtime guidance."""

    def __init__(self, intent_path: Path = Path(".zw/art.intent")) -> None:
        self.intent_path = Path(intent_path)
        self.intent: Dict[str, str] = {}
        self.ollama_prompt: str = ""
        self.palette_colors: Optional[List[Tuple[int, int, int]]] = None
        self._load_intent()

    def _load_intent(self) -> None:
        raw_block: Optional[str] = None
        if self.intent_path.exists():
            raw_block = self.intent_path.read_text(encoding="utf-8")
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

        print("🧱 Loaded ZW art intent:")
        print(f"   theme: {parsed.get('theme', 'unspecified')}")
        if parsed.get("palette"):
            print(f"   palette: {parsed['palette']}")

    def parse_block(self, block: str) -> Dict[str, str]:
        if "!zw/art.intent" in block:
            block = block.split("!zw/art.intent", 1)[-1]

        intent: Dict[str, str] = {}
        for raw_line in block.splitlines():
            line = raw_line.strip().strip("{}")
            if not line or line.startswith("!") or ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip().strip('"\'')
            value = value.strip().strip(",").strip().strip('"\'')
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

    def _resolve_palette(
        self, palette_name: Optional[str]
    ) -> Optional[List[Tuple[int, int, int]]]:
        if not palette_name:
            return None

        palette_library = {
            "obsidian_fire": [(255, 69, 0), (255, 140, 0), (139, 0, 0)],
            "aurora_glow": [(72, 209, 204), (123, 104, 238), (255, 250, 205)],
            "fractaline": [(199, 21, 133), (65, 105, 225), (32, 178, 170)],
            "verdant_realm": [(46, 139, 87), (107, 142, 35), (189, 183, 107)],
        }
        return palette_library.get(palette_name.lower())


class TerminalCanvas:
    """2D pixel canvas with ASCII display and optional PNG export."""

    def __init__(self, width: int = CANVAS_WIDTH, height: int = CANVAS_HEIGHT) -> None:
        self.width = width
        self.height = height
        self.canvas: List[List[List[int]]] = [
            [[0, 0, 0] for _ in range(width)] for _ in range(height)
        ]

    def set_pixel(self, x: int, y: int, color: Sequence[int]) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.canvas[y][x] = [int(color[0]), int(color[1]), int(color[2])]

    @staticmethod
    def _pixel_sum(pixel: Sequence[int]) -> int:
        return int(sum(pixel))

    def display(self) -> None:
        print("\n" + "=" * 50)
        print("🎨 TRIXEL COMPOSER - AUTONOMOUS AI ARTIST")
        print("=" * 50)

        for y in range(self.height):
            row = "|"
            for x in range(self.width):
                pixel_sum = self._pixel_sum(self.canvas[y][x])
                if pixel_sum == 0:
                    row += "  "
                elif pixel_sum < 150:
                    row += "▓▓"
                elif pixel_sum < 400:
                    row += "▒▒"
                else:
                    row += "░░"
            row += "|"
            print(row)
        print("=" * 50)

    def get_stats(self) -> Dict[str, Any]:
        non_zero_pixels = sum(
            1
            for row in self.canvas
            for pixel in row
            if self._pixel_sum(pixel) != 0
        )
        total_pixels = self.width * self.height
        completion = non_zero_pixels / total_pixels if total_pixels else 0.0

        unique_colors = {tuple(pixel) for row in self.canvas for pixel in row}
        unique_colors.discard((0, 0, 0))

        return {
            "completion": completion,
            "colors_used": len(unique_colors),
            "pixels_painted": non_zero_pixels,
        }

    # ------------------------------------------------------------------
    # Transform ABI: rotate_90 / rotate_180 / rotate_270 / flip_x / flip_y
    # All operations produce exact pixel-aligned results with no interpolation.
    # ------------------------------------------------------------------

    def rotate_90(self) -> None:
        """Rotate canvas 90° clockwise. new[x][H-1-y] = old[y][x]."""
        new_w, new_h = self.height, self.width
        new = [[[0, 0, 0] for _ in range(new_w)] for _ in range(new_h)]
        for y in range(self.height):
            for x in range(self.width):
                new[x][self.height - 1 - y] = list(self.canvas[y][x])
        self.canvas = new
        self.width, self.height = new_w, new_h

    def rotate_180(self) -> None:
        """Rotate canvas 180°."""
        new = [[[0, 0, 0] for _ in range(self.width)] for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                new[self.height - 1 - y][self.width - 1 - x] = list(self.canvas[y][x])
        self.canvas = new

    def rotate_270(self) -> None:
        """Rotate canvas 270° clockwise (= 90° counter-clockwise). new[H-1-x][y] = old[y][x]."""
        new_w, new_h = self.height, self.width
        new = [[[0, 0, 0] for _ in range(new_w)] for _ in range(new_h)]
        for y in range(self.height):
            for x in range(self.width):
                new[self.height - 1 - x][y] = list(self.canvas[y][x])
        self.canvas = new
        self.width, self.height = new_w, new_h

    def flip_x(self) -> None:
        """Mirror horizontally (left ↔ right)."""
        for y in range(self.height):
            self.canvas[y] = self.canvas[y][::-1]

    def flip_y(self) -> None:
        """Mirror vertically (top ↔ bottom)."""
        self.canvas = self.canvas[::-1]

    def apply_transform(self, transform: Dict[str, Any]) -> None:
        """Apply a transform dict: {rotate: 0|90|180|270, flip_x: bool, flip_y: bool}.

        Rotation is applied before flips.
        """
        rotate = int(transform.get("rotate", 0))
        if rotate == 90:
            self.rotate_90()
        elif rotate == 180:
            self.rotate_180()
        elif rotate == 270:
            self.rotate_270()
        elif rotate != 0:
            raise ValueError(f"Invalid rotate value {rotate!r}. Must be 0, 90, 180, or 270.")
        if transform.get("flip_x"):
            self.flip_x()
        if transform.get("flip_y"):
            self.flip_y()

    def to_png(
        self,
        output_dir: str = ".",
        session_id: str = "",
        scale: int = 20,
    ) -> Optional[Path]:
        if not PILLOW_AVAILABLE or Image is None:
            print("⚠️ Pillow not available; skipping PNG export.")
            return None

        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            scaled_rows: List[Tuple[int, int, int]] = []
            for row in self.canvas:
                expanded_row: List[Tuple[int, int, int]] = []
                for pixel in row:
                    expanded_row.extend([tuple(pixel)] * scale)
                for _ in range(scale):
                    scaled_rows.extend(expanded_row)

            img = Image.new("RGB", (self.width * scale, self.height * scale))
            img.putdata(scaled_rows)

            filename = f"trixel_{session_id}_{int(time.time())}.png"
            png_file = output_path / filename
            img.save(png_file)
            print(f"🎨 Artwork exported: {png_file}")
            return png_file
        except Exception as exc:
            print(f"❌ PNG export failed: {exc}")
            return None


class AutonomousCreativeMemory:
    """Small learning memory for tool preference and recent experiences."""

    def __init__(self) -> None:
        self.short_term: List[Dict[str, Any]] = []
        self.tool_preferences: Dict[str, Dict[str, float]] = {}
        self.style_evolution: List[Any] = []
        self.session_learnings: List[Any] = []
        self.total_experiences = 0

    def add_experience(self, action: CreativeAction, quality: float) -> None:
        experience = {
            "action": asdict(action),
            "quality": quality,
            "timestamp": time.time(),
        }
        self.short_term.append(experience)
        if len(self.short_term) > 10:
            self.short_term.pop(0)

        tool = action.tool
        if tool not in self.tool_preferences:
            self.tool_preferences[tool] = {"usage": 0.0, "avg_quality": 0.5}

        prefs = self.tool_preferences[tool]
        prefs["usage"] += 1
        alpha = 0.2
        prefs["avg_quality"] = (1 - alpha) * prefs["avg_quality"] + alpha * quality
        self.total_experiences += 1

    def get_preferred_tool(self) -> str:
        if not self.tool_preferences:
            return "brush"
        return max(
            self.tool_preferences.keys(),
            key=lambda tool: self.tool_preferences[tool]["avg_quality"],
        )

    def get_memory_summary(self) -> Dict[str, Any]:
        return {
            "experiences": self.total_experiences,
            "tools_learned": len(self.tool_preferences),
            "preferred_tool": self.get_preferred_tool(),
            "tool_mastery": {
                tool: f"{data['avg_quality']:.2f}"
                for tool, data in self.tool_preferences.items()
            },
        }

    def serialize(self) -> Dict[str, Any]:
        return {
            "short_term": self.short_term,
            "tool_preferences": self.tool_preferences,
            "style_evolution": self.style_evolution,
            "session_learnings": self.session_learnings,
            "total_experiences": self.total_experiences,
        }

    def load(self, data: Dict[str, Any]) -> None:
        self.short_term = data.get("short_term", [])
        self.tool_preferences = data.get("tool_preferences", {})
        self.style_evolution = data.get("style_evolution", [])
        self.session_learnings = data.get("session_learnings", [])
        self.total_experiences = data.get(
            "total_experiences", len(self.short_term)
        )


class SnapshotManager:
    """Manages rolling canvas snapshots for session continuity."""

    def __init__(self, snapshot_file: Path, max_snapshots: int = 10) -> None:
        self.snapshot_file = snapshot_file
        self.max_snapshots = max_snapshots
        self.snapshots: List[List[List[List[int]]]] = []
        self._load_snapshots()

    def _load_snapshots(self) -> None:
        if not self.snapshot_file.exists():
            return
        try:
            with open(self.snapshot_file, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, list):
                self.snapshots = data[-self.max_snapshots :]
        except Exception as exc:
            print(f"⚠️ Could not load snapshots: {exc}")

    def record_snapshot(self, canvas_state: List[List[List[int]]]) -> None:
        safe_copy = json.loads(json.dumps(canvas_state))
        self.snapshots.append(safe_copy)
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots = self.snapshots[-self.max_snapshots :]
        self._persist()

    def latest_snapshot(self) -> Optional[List[List[List[int]]]]:
        return self.snapshots[-1] if self.snapshots else None

    def _persist(self) -> None:
        self.snapshot_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.snapshot_file, "w", encoding="utf-8") as handle:
                json.dump(self.snapshots[-self.max_snapshots :], handle, indent=2)
        except Exception as exc:
            print(f"⚠️ Could not save snapshots: {exc}")


class ExperienceStore:
    """Persists learning traces to LMDB or JSONL."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.backend = "lmdb" if LMDB_AVAILABLE else "jsonl"
        self.log_path = self.base_dir / "experience_log.jsonl"
        self.counter_path = self.base_dir / "experience_counter.txt"
        self.env = None

        if self.backend == "lmdb" and lmdb is not None:
            try:
                self.env = lmdb.open(
                    str(self.base_dir / "experience.lmdb"),
                    map_size=64 * 1024 * 1024,
                    subdir=False,
                    create=True,
                )
            except Exception as exc:
                print(
                    f"⚠️ LMDB unavailable at runtime ({exc}); falling back to JSONL."
                )
                self.backend = "jsonl"

    def _next_id(self) -> int:
        last = 0
        if self.counter_path.exists():
            try:
                last = int(self.counter_path.read_text(encoding="utf-8").strip() or "0")
            except Exception:
                last = 0
        current = last + 1
        self.counter_path.write_text(str(current), encoding="utf-8")
        return current

    @staticmethod
    def _serialize(event: Dict[str, Any]) -> bytes:
        return json.dumps(event, separators=(",", ":")).encode("utf-8")

    def record(
        self,
        session_id: str,
        iteration: int,
        phase: str,
        action: CreativeAction,
        quality: float,
        canvas_stats: Dict[str, Any],
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
                    txn.put(
                        f"event:{event_id:09d}".encode("utf-8"),
                        self._serialize(event),
                    )
                return
            except Exception as exc:
                print(f"⚠️ LMDB write failed ({exc}); writing JSONL fallback.")

        with open(self.log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(event) + "\n")


class RecipeRenderer:
    """Deterministic recipe renderer for art_recipe-style scene descriptions."""

    def __init__(self, canvas: TerminalCanvas) -> None:
        self.canvas = canvas

    def execute(
        self, recipe: Dict[str, Any]
    ) -> Optional["_entity_layer.EntityLayer"]:
        """Execute all terrain passes and return entity layer (not rendered).

        entity_marker passes are routed to the entity layer, not the canvas.
        Returns None when the recipe carries no entity positions.
        """
        passes = recipe.get("passes", recipe.get("actions", recipe.get("strokes", [])))
        terrain_passes = [p for p in passes if p.get("type") != "entity_marker"]
        entity_passes  = [p for p in passes if p.get("type") == "entity_marker"]

        print(f"📜 Executing {len(terrain_passes)} terrain passes"
              + (f" + {len(entity_passes)} entity pass(es) → sidecar"
                 if entity_passes else "") + "...")

        for index, step in enumerate(terrain_passes):
            pass_type = step.get("type", step.get("action", "unknown"))
            if pass_type == "gradient_fill":
                self._exec_gradient_fill(step)
            elif pass_type == "noise_scatter":
                self._exec_noise_scatter(step)
            elif pass_type == "h_band":
                self._exec_h_band(step)
            elif pass_type == "v_crack":
                self._exec_v_crack(step)
            elif pass_type == "ember_scatter":
                self._exec_ember_scatter(step)
            else:
                print(f"⚠️ Unknown pass type: {pass_type}")
            print(f"   [{index + 1}/{len(terrain_passes)}] ✓ {pass_type}")

        # Build entity layer from first entity_marker pass that carries positions
        scene_id    = recipe.get("scene_id", "unknown")
        recipe_name = f"{recipe.get('terrain', 'unknown')}.{recipe.get('label', 'unknown')}"
        for ep in entity_passes:
            layer = _entity_layer.from_recipe_pass(
                scene_id=scene_id,
                recipe_name=recipe_name,
                pass_data=ep,
                canvas_width=self.canvas.width,
                canvas_height=self.canvas.height,
            )
            if layer:
                return layer
        return None

    def _exec_gradient_fill(self, step: Dict[str, Any]) -> None:
        top = tuple(step.get("top", [30, 10, 0]))
        bottom = tuple(step.get("bottom", [80, 20, 0]))
        for y in range(self.canvas.height):
            t = y / max(1, self.canvas.height - 1)
            color = tuple(int(bottom[c] * t + top[c] * (1 - t)) for c in range(3))
            for x in range(self.canvas.width):
                self.canvas.set_pixel(x, y, color)

    def _exec_noise_scatter(self, step: Dict[str, Any]) -> None:
        density = float(step.get("density", 0.1))
        colors = [tuple(c) for c in step.get("colors", [[255, 255, 255]])]
        rng = random.Random(step.get("seed"))
        for y in range(self.canvas.height):
            for x in range(self.canvas.width):
                if rng.random() < density:
                    self.canvas.set_pixel(x, y, rng.choice(colors))

    def _exec_h_band(self, step: Dict[str, Any]) -> None:
        rng = random.Random(int(step.get("seed", 0)))
        y_value = float(step.get("y", 0.5))
        thickness_value = float(step.get("thickness", 1))
        color = tuple(int(c) for c in step.get("color", [255, 255, 255]))
        jitter = float(step.get("jitter", 0.0))
        waviness = float(step.get("waviness", 0.0))
        gap_chance = float(step.get("gap_chance", 0.0))

        base_y = (
            int(round(y_value * (self.canvas.height - 1)))
            if y_value <= 1.0
            else int(round(y_value))
        )
        thickness = (
            max(1, int(round(thickness_value * self.canvas.height)))
            if thickness_value <= 1.0
            else max(1, int(round(thickness_value)))
        )

        current_y = base_y
        for x in range(self.canvas.width):
            if rng.random() < waviness:
                current_y += rng.choice([-1, 0, 1])
            for dy in range(thickness):
                yy = current_y + dy
                if rng.random() < jitter:
                    yy += rng.choice([-1, 0, 1])
                if rng.random() < gap_chance:
                    continue
                if 0 <= yy < self.canvas.height:
                    self.canvas.set_pixel(x, yy, color)

    def _exec_v_crack(self, step: Dict[str, Any]) -> None:
        rng = random.Random(int(step.get("seed", 0)))
        x_value = float(step.get("x", 0.5))
        y_start_value = float(step.get("y_start", 0.0))
        y_end_value = float(step.get("y_end", 1.0))
        color = tuple(int(c) for c in step.get("color", [255, 100, 0]))
        glow = bool(step.get("glow", False))
        glow_color = tuple(int(c) for c in step.get("glow_color", [100, 20, 0]))
        jitter = float(step.get("jitter", 0.0))
        gap_chance = float(step.get("gap_chance", 0.0))
        branch_chance = float(step.get("branch_chance", 0.0))

        cx = (
            int(round(x_value * (self.canvas.width - 1)))
            if x_value <= 1.0
            else int(round(x_value))
        )
        y_start = (
            int(round(y_start_value * (self.canvas.height - 1)))
            if y_start_value <= 1.0
            else int(round(y_start_value))
        )
        y_end = (
            int(round(y_end_value * (self.canvas.height - 1)))
            if y_end_value <= 1.0
            else int(round(y_end_value))
        )
        if y_end < y_start:
            y_start, y_end = y_end, y_start

        for y in range(y_start, y_end + 1):
            if rng.random() < jitter:
                cx += rng.choice([-1, 0, 1])
            cx = max(0, min(self.canvas.width - 1, cx))
            if rng.random() < gap_chance:
                continue

            self.canvas.set_pixel(cx, y, color)

            if rng.random() < branch_chance:
                cx += rng.choice([-1, 1])
                cx = max(0, min(self.canvas.width - 1, cx))

            if glow:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    gx, gy = cx + dx, y + dy
                    if 0 <= gx < self.canvas.width and 0 <= gy < self.canvas.height:
                        if rng.random() < 0.4:
                            self.canvas.set_pixel(gx, gy, glow_color)

    def _exec_ember_scatter(self, step: Dict[str, Any]) -> None:
        count = int(step.get("count", 5))
        colors = [tuple(c) for c in step.get("colors", [[255, 140, 0], [255, 215, 0]])]
        rng = random.Random(step.get("seed"))
        for _ in range(count):
            x = rng.randint(0, self.canvas.width - 1)
            y = rng.randint(0, self.canvas.height - 1)
            self.canvas.set_pixel(x, y, rng.choice(colors))

class TerminalTrixelComposer:
    """Main controller for autonomous creation, replay, persistence, and recipes."""

    def __init__(self) -> None:
        self.canvas = TerminalCanvas()
        self.memory = AutonomousCreativeMemory()
        self.creative_phase = CreativePhase.PLANNING
        self.session_id = f"terminal_{int(time.time())}"
        self.intent_manager = ZWArtIntentManager()
        self.ollama_model: Optional[str] = None
        self.snapshot_manager = SnapshotManager(DEFAULT_SNAPSHOT_PATH)
        self.memory_path = DEFAULT_MEMORY_PATH
        self.experience_store = ExperienceStore(DEFAULT_ZW_DIR)
        self.keystroke_log_path = DEFAULT_ZW_DIR / "keystrokes.jsonl"

        self._load_memory()
        self._restore_latest_snapshot()

        self.phase_colors: Dict[str, List[Tuple[int, int, int]]] = {
            "planning": [(139, 69, 19), (160, 82, 45), (205, 133, 63)],
            "active": [(255, 140, 0), (255, 69, 0), (255, 215, 0)],
            "reflection": [(100, 149, 237), (123, 104, 238), (147, 112, 219)],
            "style": [(255, 20, 147), (255, 105, 180), (255, 182, 193)],
        }
        if self.intent_manager.palette_colors:
            for key in self.phase_colors:
                self.phase_colors[key] = self.intent_manager.palette_colors

        self._configure_ollama_model()

    def _restore_latest_snapshot(self) -> None:
        latest_canvas = self.snapshot_manager.latest_snapshot()
        if latest_canvas:
            self.canvas.canvas = latest_canvas
            print(
                f"📸 Loaded {len(self.snapshot_manager.snapshots)} canvas snapshots; resuming from latest state."
            )
            self.creative_phase = CreativePhase.ACTIVE_CREATION
        else:
            print("📸 No existing snapshots found; starting a fresh canvas.")

    def _record_keystroke(self, prompt: str, value: str) -> None:
        event = {
            "session_id": self.session_id,
            "prompt": prompt,
            "value": value,
            "length": len(value),
            "timestamp": time.time(),
        }
        self.keystroke_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.keystroke_log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(event) + "\n")

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

    def _configure_ollama_model(self) -> None:
        if not OLLAMA_AVAILABLE or ollama is None:
            print("⚠️ Ollama not installed; running without LLM guidance.")
            return

        available_models: List[str] = []
        try:
            response = ollama.list()
            available_models = [
                model.get("name")
                for model in response.get("models", [])
                if model.get("name")
            ]
        except Exception as exc:
            print(f"⚠️ Could not list Ollama models: {exc}")

        if not available_models:
            print("⚙️ Continuing without Ollama-driven planning.")
            return

        print("🤖 Available Ollama models detected on this machine:")
        for idx, name in enumerate(available_models, start=1):
            print(f"   {idx}. {name}")

        choice = self._safe_input(
            "Select an Ollama model (Enter for default 1, or 0 to skip): "
        ).strip()
        if choice == "0":
            print("🚫 Ollama guidance disabled by user choice.")
            return

        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(available_models):
                self.ollama_model = available_models[idx - 1]

        if not self.ollama_model:
            self.ollama_model = available_models[0]

        print(f"🧠 Ollama guidance enabled with model: {self.ollama_model}")

    def ollama_brain(self, prompt: str) -> Optional[str]:
        if not (self.ollama_model and OLLAMA_AVAILABLE and ollama is not None):
            return None
        try:
            response = ollama.chat(
                model=self.ollama_model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.get("message", {}).get("content")
        except Exception as exc:
            print(f"⚠️ Ollama error: {exc}")
            return None

    def perceive(self) -> Dict[str, Any]:
        return {
            "canvas_stats": self.canvas.get_stats(),
            "memory_state": self.memory.get_memory_summary(),
            "phase": self.creative_phase.value,
            "session_id": self.session_id,
        }

    def plan_action(self, perception: Dict[str, Any]) -> CreativeAction:
        stats = perception["canvas_stats"]
        memory_state = perception["memory_state"]

        if self.creative_phase == CreativePhase.PLANNING:
            x = CANVAS_WIDTH // 2 + random.randint(-2, 2)
            y = CANVAS_HEIGHT // 2 + random.randint(-2, 2)
            if random.random() < 0.25:
                x = random.randint(0, CANVAS_WIDTH - 1)
                y = random.randint(0, CANVAS_HEIGHT - 1)
        else:
            if stats["completion"] > 0.3:
                x = random.randint(
                    max(0, CANVAS_WIDTH // 2 - 4),
                    min(CANVAS_WIDTH - 1, CANVAS_WIDTH // 2 + 4),
                )
                y = random.randint(
                    max(0, CANVAS_HEIGHT // 2 - 4),
                    min(CANVAS_HEIGHT - 1, CANVAS_HEIGHT // 2 + 4),
                )
            else:
                x = random.randint(0, CANVAS_WIDTH - 1)
                y = random.randint(0, CANVAS_HEIGHT - 1)

        tool = memory_state.get("preferred_tool", "brush")
        phase_key = {
            CreativePhase.PLANNING: "planning",
            CreativePhase.ACTIVE_CREATION: "active",
            CreativePhase.REFLECTION: "reflection",
            CreativePhase.STYLE_DEVELOPMENT: "style",
        }.get(self.creative_phase, "active")
        colors = self.phase_colors[phase_key]
        color = colors[random.randint(0, len(colors) - 1)]

        ollama_notes = ""
        ollama_context = self.intent_manager.ollama_prompt if self.intent_manager else ""
        ollama_prompt = (
            f"Canvas stats: {stats}\n"
            f"Memory: {memory_state}\n"
            f"Phase: {self.creative_phase.value}\n"
            f"ZW intent: {ollama_context or 'none'}\n\n"
            "Respond ONLY as JSON with keys tool and color, e.g. "
            '{"tool": "brush", "color": [255, 128, 0]}'
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
        if self.intent_manager.intent:
            intent_theme = (
                self.intent_manager.intent.get("theme", "")
                .strip()
                .replace(" ", "_")
            )

        return CreativeAction(
            tool=tool,
            x=x,
            y=y,
            color=color,
            pressure=random.uniform(0.5, 1.0),
            reasoning=f"{self.creative_phase.value}_action"
            + (f"_{intent_theme}" if intent_theme else "")
            + (f"_{ollama_notes}" if ollama_notes else ""),
            timestamp=time.time(),
        )

    def execute_action(self, action: CreativeAction) -> float:
        self.canvas.set_pixel(action.x, action.y, action.color)
        stats = self.canvas.get_stats()

        base_quality = 0.5
        if stats["completion"] > 0.1:
            base_quality += 0.2
        if stats["colors_used"] > 3:
            base_quality += 0.1

        quality = base_quality + random.uniform(-0.2, 0.3)
        return max(0.0, min(1.0, quality))

    def update_phase(self, perception: Dict[str, Any]) -> None:
        completion = perception["canvas_stats"]["completion"]
        experiences = max(len(self.memory.short_term), self.memory.total_experiences)

        if self.creative_phase == CreativePhase.PLANNING and (
            completion > 0.08 or experiences >= 5
        ):
            self.creative_phase = CreativePhase.ACTIVE_CREATION
        elif (
            self.creative_phase == CreativePhase.ACTIVE_CREATION
            and completion >= 0.6
        ):
            self.creative_phase = CreativePhase.REFLECTION
        elif self.creative_phase == CreativePhase.REFLECTION and completion >= 0.8:
            self.creative_phase = CreativePhase.STYLE_DEVELOPMENT

    async def autonomous_create(self, iterations: int = 100) -> None:
        print("🚀 STARTING AUTONOMOUS AI ARTIST SESSION")
        print(f"Session ID: {self.session_id}")

        for index in range(iterations):
            print(f"\n--- Iteration {index + 1}/{iterations} ---")
            perception = self.perceive()
            self.update_phase(perception)
            action = self.plan_action(perception)
            quality = self.execute_action(action)

            self.memory.add_experience(action, quality)
            self.experience_store.record(
                session_id=self.session_id,
                iteration=index + 1,
                phase=self.creative_phase.value,
                action=action,
                quality=quality,
                canvas_stats=self.canvas.get_stats(),
            )

            print(f"🧠 Phase: {self.creative_phase.value}")
            print(f"🎨 Action: {action.tool} at ({action.x},{action.y}) - Quality: {quality:.2f}")
            print(
                f"📊 Canvas: {perception['canvas_stats']['completion']:.1%} complete, "
                f"{perception['canvas_stats']['colors_used']} colors"
            )
            print(
                f"🎯 Memory: {perception['memory_state']['experiences']} experiences, "
                f"preferred tool: {perception['memory_state']['preferred_tool']}"
            )

            self.snapshot_manager.record_snapshot(self.canvas.canvas)
            if (index + 1) % 5 == 0 or index == iterations - 1:
                self.canvas.display()
            await asyncio.sleep(0.3)

        await self.session_summary()

    async def replay_experience_jsonl(
        self,
        jsonl_path: Path,
        delay: float = 0.15,
        clear_canvas: bool = True,
        max_events: Optional[int] = None,
    ) -> None:
        path = Path(jsonl_path)
        if not path.exists():
            raise FileNotFoundError(f"Replay file not found: {path}")

        if clear_canvas:
            self.canvas = TerminalCanvas(width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
            print("🧼 Cleared canvas for replay.")

        print(f"🎬 Replaying strokes from: {path}")
        applied = 0
        skipped = 0

        with open(path, "r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
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
                quality_text = f"{float(quality):.2f}" if isinstance(
                    quality, (int, float)
                ) else "n/a"
                print(
                    f"🎞️ Replay {applied}: line {line_no} -> ({x},{y}) "
                    f"color={color_tuple} quality={quality_text}"
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

    async def session_summary(self) -> None:
        perception = self.perceive()
        print("\n" + "🌟" * 20)
        print("AUTONOMOUS CREATION SESSION COMPLETE")
        print("🌟" * 20)
        print("\n📈 Session Statistics:")
        print(f" Canvas Completion: {perception['canvas_stats']['completion']:.1%}")
        print(f" Pixels Painted: {perception['canvas_stats']['pixels_painted']}")
        print(f" Colors Used: {perception['canvas_stats']['colors_used']}")
        print(f" Creative Experiences: {perception['memory_state']['experiences']}")
        print("\n🧠 AI Learning Progress:")
        print(f" Tools Mastered: {perception['memory_state']['tools_learned']}")
        print(f" Preferred Tool: {perception['memory_state']['preferred_tool']}")
        print(" Tool Mastery Levels:")
        for tool, mastery in perception["memory_state"]["tool_mastery"].items():
            print(f"   {tool}: {mastery}")
        print(f"\n🎨 Final Artistic Phase: {self.creative_phase.value}")
        if self.ollama_model:
            print(f"🤖 Ollama model: {self.ollama_model}")
        if self.intent_manager.intent:
            print("\n🧱 ZW Art Intent ➜ Ollama prompt:")
            print(f" Theme: {self.intent_manager.intent.get('theme', 'unspecified')}")
            if self.intent_manager.ollama_prompt:
                print(f" Prompt: {self.intent_manager.ollama_prompt}")
        self.save_session()
        print(f"\n💾 Session saved to: {DEFAULT_SESSION_DIR / f'{self.session_id}.json'}")

    def save_session(self) -> None:
        session_data = {
            "session_id": self.session_id,
            "canvas": self.canvas.canvas,
            "final_stats": self.canvas.get_stats(),
            "memory_summary": self.memory.get_memory_summary(),
            "final_phase": self.creative_phase.value,
            "experiences": self.memory.short_term,
            "experience_store_backend": self.experience_store.backend,
            "experience_log_path": str(self.experience_store.log_path),
            "keystroke_log_path": str(self.keystroke_log_path),
        }

        DEFAULT_SESSION_DIR.mkdir(parents=True, exist_ok=True)
        session_file = DEFAULT_SESSION_DIR / f"{self.session_id}.json"
        with open(session_file, "w", encoding="utf-8") as handle:
            json.dump(session_data, handle, indent=2)
        print(f"💾 Session saved successfully to: {session_file}")

        self.snapshot_manager.record_snapshot(self.canvas.canvas)
        self._save_memory()

        DEFAULT_ARTWORK_DIR.mkdir(parents=True, exist_ok=True)
        png_file = self.canvas.to_png(
            output_dir=str(DEFAULT_ARTWORK_DIR), session_id=self.session_id
        )
        if png_file:
            print(f"🎨✨ Your AI's artwork is now visible: {png_file}")

    def _save_memory(self) -> None:
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.memory_path, "w", encoding="utf-8") as handle:
                json.dump(self.memory.serialize(), handle, indent=2)
        except Exception as exc:
            print(f"⚠️ Could not save memory: {exc}")

    def _load_memory(self) -> None:
        if not self.memory_path.exists():
            return
        try:
            with open(self.memory_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                self.memory.load(data)
                print("🧠 Loaded prior creative memory for continuity across sessions.")
        except Exception as exc:
            print(f"⚠️ Could not load memory: {exc}")

    def execute_recipe(self, recipe_path: str, out_dir: str) -> bool:
        recipe_file = Path(recipe_path)
        if not recipe_file.exists():
            print(f"❌ Recipe not found: {recipe_path}")
            return False

        try:
            data = json.loads(recipe_file.read_text(encoding="utf-8"))
            recipe = data.get("recipe", data)
        except json.JSONDecodeError as exc:
            print(f"❌ Invalid JSON in recipe: {exc}")
            return False

        width = int(recipe.get("canvas", {}).get("width", CANVAS_WIDTH))
        height = int(recipe.get("canvas", {}).get("height", CANVAS_HEIGHT))
        if width != self.canvas.width or height != self.canvas.height:
            self.canvas = TerminalCanvas(width=width, height=height)
            print(f"📐 Canvas resized to {width}x{height}")

        renderer = RecipeRenderer(self.canvas)
        entity_layer = renderer.execute(recipe)

        transform = recipe.get("transform", {})
        if transform:
            self.canvas.apply_transform(transform)
            r = transform.get("rotate", 0)
            fx = transform.get("flip_x", False)
            fy = transform.get("flip_y", False)
            desc = " ".join(filter(None, [
                f"rotate={r}" if r else "",
                "flip_x" if fx else "",
                "flip_y" if fy else "",
            ]))
            print(f"🔄 Transform applied: {desc}")

        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        png_file = self.canvas.to_png(
            output_dir=str(out_path),
            session_id=recipe.get("scene_id", "recipe"),
            scale=20,
        )

        entity_sidecar: Optional[Path] = None
        if entity_layer:
            entity_sidecar = out_path / f"entities_{recipe.get('scene_id', 'output')}.json"
            entity_layer.save(entity_sidecar)
            print(f"🧩 Entity layer: {len(entity_layer.markers)} marker(s) → {entity_sidecar}")

        session_data = {
            "recipe_source": str(recipe_file),
            "scene_id": recipe.get("scene_id"),
            "terrain_passes_executed": len(
                [p for p in recipe.get("passes", []) if p.get("type") != "entity_marker"]
            ),
            "canvas_stats": self.canvas.get_stats(),
            "output_png": str(png_file) if png_file else None,
            "entity_layer": str(entity_sidecar) if entity_sidecar else None,
        }
        session_file = out_path / f"recipe_{recipe.get('scene_id', 'output')}.json"
        session_file.write_text(json.dumps(session_data, indent=2), encoding="utf-8")

        print(f"✅ Render complete: {png_file}")
        print(f"📄 Session saved: {session_file}")
        return True


def enable_empire_mode() -> None:
    print("🏰 Empire mode is unavailable because optional dependencies are not installed.")
    print("Run `pip install aiohttp` and connect to an Empire broker to enable it.")


async def launch_empire_collaborative_session() -> None:
    raise RuntimeError("Empire collaborative mode requires optional aiohttp dependency")


async def main(
    replay_jsonl: Optional[str] = None,
    replay_delay: float = 0.15,
    replay_limit: Optional[int] = None,
    clear_replay_canvas: bool = True,
    recipe_path: Optional[str] = None,
    out_dir: Optional[str] = None,
    no_autonomous: bool = False,
) -> int:
    print("🎨 TRIXEL COMPOSER: AUTONOMOUS AI ARTIST")
    print("=" * 50)

    composer = TerminalTrixelComposer()

    if recipe_path and out_dir:
        print(f"📜 Recipe mode: {recipe_path} → {out_dir}")
        success = composer.execute_recipe(recipe_path, out_dir)
        return 0 if success else 1

    composer.canvas.display()

    if replay_jsonl:
        await composer.replay_experience_jsonl(
            jsonl_path=Path(replay_jsonl),
            delay=max(0.0, replay_delay),
            clear_canvas=clear_replay_canvas,
            max_events=replay_limit,
        )
        return 0

    if no_autonomous:
        print("⏭️ Autonomous loop skipped (--no-autonomous)")
        return 0

    print("\n⏳ Starting autonomous creation in 3 seconds...")
    await asyncio.sleep(3)
    await composer.autonomous_create(30)
    print("\n✨ Autonomous AI artist session complete!")
    print("🎯 Check .zw/sessions/ folder for saved session data")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Terminal Trixel Composer")
    parser.add_argument("--replay-jsonl", help="Replay strokes from a JSONL file")
    parser.add_argument(
        "--replay-delay",
        type=float,
        default=0.15,
        help="Delay between replayed strokes (seconds)",
    )
    parser.add_argument(
        "--replay-limit",
        type=int,
        default=None,
        help="Optional max number of replay events",
    )
    parser.add_argument(
        "--no-clear-replay-canvas",
        action="store_true",
        help="Do not clear the current canvas before replay",
    )
    parser.add_argument("--recipe", type=str, help="Path to art_recipe.json")
    parser.add_argument("--out", type=str, help="Output directory for PNG + session JSON")
    parser.add_argument(
        "--no-autonomous",
        action="store_true",
        help="Skip autonomous loop when using --recipe",
    )

    args = parser.parse_args()

    try:
        exit_code = asyncio.run(
            main(
                replay_jsonl=args.replay_jsonl,
                replay_delay=args.replay_delay,
                replay_limit=args.replay_limit,
                clear_replay_canvas=not args.no_clear_replay_canvas,
                recipe_path=args.recipe,
                out_dir=args.out,
                no_autonomous=args.no_autonomous,
            )
        )
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Session interrupted by user")
        sys.exit(130)
    except Exception as exc:
        print(f"\n❌ Error: {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
