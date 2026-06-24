#!/usr/bin/env python3
"""
Trixel Composer - AI Pixel Artist for EngAIn
Generates pixel art sprites from text descriptions
Integrates with ZON memory system
Outputs Godot-ready assets
"""

import os
import json
import time
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from PIL import Image, ImageDraw, ImageFont
import random

@dataclass
class TrixelStyle:
    """Pixel art style configuration"""
    palette: List[Tuple[int, int, int]]  # RGB colors
    tile_size: int = 16  # 16x16 default
    outline: bool = True
    dithering: bool = False
    antialias: bool = False
    
    
@dataclass
class TrixelAsset:
    """Generated asset metadata"""
    id: str
    prompt: str
    style_name: str
    filepath: str
    width: int
    height: int
    created_at: float
    palette_hash: str
    tags: List[str]
    
    def to_zon(self) -> str:
        """Convert to ZON block format"""
        zon = f"""#ZON art/0.1
@id: {self.id}
@scope: trixel
@when: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(self.created_at))}
@where: Assets/Trixel/{self.style_name}
@summary: {self.prompt}
@tags: {"|".join(self.tags)}
=bullets
- filepath: {self.filepath}
- width: {self.width}
- height: {self.height}
- palette_hash: {self.palette_hash}
- style: {self.style_name}
- type: sprite
=end
"""
        return zon


class TrixelComposer:
    """
    AI Pixel Artist - Generates game assets
    
    Methods:
    - generate_sprite() - Create sprite from text prompt
    - generate_tile() - Create tileset from description  
    - generate_character() - Create character sprite sheet
    - get_palette() - Get color palette for style
    """
    
    def __init__(self, output_dir: str = "./trixel_output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Built-in palettes
        self.palettes = {
            "fantasy": [
                (15, 15, 27),    # Dark background
                (139, 72, 82),   # Deep red
                (213, 125, 95),  # Warm mid
                (255, 199, 119), # Light gold
                (250, 251, 234), # White/highlight
            ],
            "scifi": [
                (20, 12, 28),    # Dark purple
                (68, 36, 52),    # Mid purple
                (48, 52, 109),   # Blue
                (78, 74, 78),    # Gray
                (133, 149, 161), # Light blue-gray
            ],
            "forest": [
                (34, 32, 52),    # Dark
                (69, 40, 60),    # Brown
                (102, 57, 49),   # Deeper brown
                (143, 86, 59),   # Mid brown
                (223, 113, 38),  # Orange
            ],
            "ocean": [
                (15, 15, 27),    # Deep water
                (28, 74, 95),    # Dark blue
                (41, 119, 135),  # Mid blue
                (88, 170, 175),  # Light blue
                (189, 224, 228), # Foam/white
            ],
            "monochrome": [
                (0, 0, 0),       # Black
                (64, 64, 64),    # Dark gray
                (128, 128, 128), # Mid gray
                (192, 192, 192), # Light gray
                (255, 255, 255), # White
            ]
        }
        
        print(f"Trixel Composer initialized")
        print(f"Output directory: {output_dir}")
        print(f"Available palettes: {list(self.palettes.keys())}")
        
    def generate_sprite(self, 
                       prompt: str,
                       style: str = "fantasy",
                       size: int = 16,
                       tags: List[str] = None) -> TrixelAsset:
        """
        Generate pixel art sprite from text prompt
        
        Args:
            prompt: Text description (e.g. "stone wall tile", "fire elemental")
            style: Palette name
            size: Sprite dimensions (size x size)
            tags: Metadata tags
            
        Returns:
            TrixelAsset with filepath and metadata
        """
        
        if tags is None:
            tags = []
            
        print(f"\n🎨 Generating sprite: '{prompt}'")
        print(f"   Style: {style}")
        print(f"   Size: {size}x{size}")
        
        # Get palette
        palette = self.palettes.get(style, self.palettes["fantasy"])
        
        # Generate sprite data (procedural for now, can integrate SD later)
        sprite_data = self._generate_procedural_sprite(prompt, palette, size)
        
        # Create PIL Image
        img = Image.new('RGB', (size, size))
        pixels = img.load()
        
        for y in range(size):
            for x in range(size):
                pixels[x, y] = sprite_data[y][x]
        
        # Save file
        asset_id = self._generate_asset_id(prompt, style)
        filename = f"{asset_id}.png"
        filepath = os.path.join(self.output_dir, filename)
        
        # Scale up for visibility (4x)
        display_img = img.resize((size * 4, size * 4), Image.NEAREST)
        display_img.save(filepath)
        
        print(f"   ✓ Saved to: {filepath}")
        
        # Create asset metadata
        palette_hash = hashlib.md5(str(palette).encode()).hexdigest()[:8]
        
        asset = TrixelAsset(
            id=asset_id,
            prompt=prompt,
            style_name=style,
            filepath=filepath,
            width=size * 4,  # Scaled size
            height=size * 4,
            created_at=time.time(),
            palette_hash=palette_hash,
            tags=tags + [style, "sprite"]
        )
        
        # Save ZON metadata
        zon_path = filepath.replace('.png', '.zon')
        with open(zon_path, 'w') as f:
            f.write(asset.to_zon())
        
        print(f"   ✓ Metadata: {zon_path}")
        
        return asset
        
    def _generate_procedural_sprite(self, 
                                   prompt: str,
                                   palette: List[Tuple[int, int, int]],
                                   size: int) -> List[List[Tuple[int, int, int]]]:
        """
        Generate procedural pixel art based on prompt keywords
        
        This is a placeholder for real AI generation.
        You can replace this with:
        - Stable Diffusion API calls
        - Local SD model
        - DALL-E API
        - Custom trained pixel art model
        """
        
        # Parse prompt for keywords
        prompt_lower = prompt.lower()
        
        # Initialize grid
        grid = [[palette[0] for _ in range(size)] for _ in range(size)]
        
        # Procedural generation based on keywords
        if any(word in prompt_lower for word in ["wall", "brick", "stone"]):
            grid = self._generate_wall_pattern(palette, size)
            
        elif any(word in prompt_lower for word in ["fire", "flame", "torch"]):
            grid = self._generate_fire_pattern(palette, size)
            
        elif any(word in prompt_lower for word in ["water", "ocean", "wave"]):
            grid = self._generate_water_pattern(palette, size)
            
        elif any(word in prompt_lower for word in ["tree", "forest", "plant"]):
            grid = self._generate_tree_pattern(palette, size)
            
        elif any(word in prompt_lower for word in ["character", "person", "npc"]):
            grid = self._generate_character_pattern(palette, size)
            
        else:
            # Default: random dithered pattern
            grid = self._generate_abstract_pattern(palette, size)
            
        return grid
        
    def _generate_wall_pattern(self, palette, size):
        """Generate brick/stone wall pattern"""
        grid = [[palette[0] for _ in range(size)] for _ in range(size)]
        
        # Draw bricks
        brick_height = size // 4
        brick_width = size // 3
        
        for y in range(0, size, brick_height):
            offset = (y // brick_height) % 2
            for x in range(0, size, brick_width):
                x_pos = x + (brick_width // 2 if offset else 0)
                if x_pos < size:
                    # Fill brick
                    for by in range(min(brick_height - 1, size - y)):
                        for bx in range(min(brick_width - 1, size - x_pos)):
                            if y + by < size and x_pos + bx < size:
                                # Vary color slightly
                                color_idx = 2 + random.randint(0, 1)
                                grid[y + by][x_pos + bx] = palette[color_idx]
                    
                    # Mortar lines (dark)
                    for bx in range(min(brick_width, size - x_pos)):
                        if x_pos + bx < size and y < size:
                            grid[y][x_pos + bx] = palette[1]
                            
        return grid
        
    def _generate_fire_pattern(self, palette, size):
        """Generate animated fire effect"""
        grid = [[palette[0] for _ in range(size)] for _ in range(size)]
        
        # Fire starts at bottom
        for y in range(size // 2, size):
            for x in range(size):
                # Probability decreases as we go up
                heat = (y - size // 2) / (size // 2)
                if random.random() < heat:
                    # Hot colors at bottom
                    if y > size * 0.75:
                        grid[y][x] = palette[4]  # Bright
                    elif y > size * 0.6:
                        grid[y][x] = palette[3]  # Mid
                    else:
                        grid[y][x] = palette[2]  # Dark
                        
        return grid
        
    def _generate_water_pattern(self, palette, size):
        """Generate water wave pattern"""
        grid = [[palette[1] for _ in range(size)] for _ in range(size)]
        
        # Horizontal wave lines
        for y in range(0, size, 3):
            wave_offset = random.randint(-1, 1)
            for x in range(size):
                if (x + wave_offset) % 4 < 2:
                    grid[y][x] = palette[2]
                else:
                    grid[y][x] = palette[3]
                    
        # Add foam highlights
        for _ in range(size // 4):
            x = random.randint(0, size - 1)
            y = random.randint(0, size - 1)
            grid[y][x] = palette[4]
            
        return grid
        
    def _generate_tree_pattern(self, palette, size):
        """Generate simple tree sprite"""
        grid = [[palette[0] for _ in range(size)] for _ in range(size)]
        
        # Trunk
        trunk_x = size // 2
        trunk_width = max(2, size // 6)
        for y in range(size // 2, size):
            for x in range(trunk_x - trunk_width // 2, trunk_x + trunk_width // 2):
                if 0 <= x < size:
                    grid[y][x] = palette[2]
        
        # Foliage (circular-ish)
        center_y = size // 3
        center_x = size // 2
        radius = size // 3
        
        for y in range(max(0, center_y - radius), min(size, center_y + radius)):
            for x in range(max(0, center_x - radius), min(size, center_x + radius)):
                dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                if dist < radius:
                    grid[y][x] = palette[3]
                    
        return grid
        
    def _generate_character_pattern(self, palette, size):
        """Generate simple character sprite"""
        grid = [[palette[0] for _ in range(size)] for _ in range(size)]
        
        center_x = size // 2
        
        # Head
        head_y = size // 4
        head_size = max(2, size // 4)
        for y in range(head_y - head_size, head_y + head_size):
            for x in range(center_x - head_size, center_x + head_size):
                if 0 <= y < size and 0 <= x < size:
                    grid[y][x] = palette[3]
        
        # Body
        for y in range(size // 3, size * 2 // 3):
            for x in range(center_x - 1, center_x + 2):
                if 0 <= x < size and 0 <= y < size:
                    grid[y][x] = palette[2]
        
        # Legs
        for y in range(size * 2 // 3, size):
            grid[y][center_x - 1] = palette[1]
            grid[y][center_x + 1] = palette[1]
            
        return grid
        
    def _generate_abstract_pattern(self, palette, size):
        """Generate abstract dithered pattern"""
        grid = [[palette[0] for _ in range(size)] for _ in range(size)]
        
        for y in range(size):
            for x in range(size):
                # Perlin-like noise (simplified)
                val = (x * 7 + y * 13) % len(palette)
                grid[y][x] = palette[val]
                
        return grid
        
    def _generate_asset_id(self, prompt: str, style: str) -> str:
        """Generate unique asset ID"""
        timestamp = int(time.time() * 1000)
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        return f"trixel_{style}_{prompt_hash}_{timestamp}"
        
    def get_palette(self, style: str) -> List[Tuple[int, int, int]]:
        """Get color palette for style"""
        return self.palettes.get(style, self.palettes["fantasy"])
        
    def list_styles(self) -> List[str]:
        """List available palettes/styles"""
        return list(self.palettes.keys())


# Example usage and test
if __name__ == "__main__":
    composer = TrixelComposer()
    
    print("\n" + "="*60)
    print("🎨 TRIXEL COMPOSER - TEST SUITE")
    print("="*60)
    
    # Test 1: Wall tile
    print("\nTest 1: Stone wall tile")
    wall = composer.generate_sprite(
        "stone wall brick tile",
        style="fantasy",
        size=16,
        tags=["tile", "wall"]
    )
    
    # Test 2: Fire sprite
    print("\nTest 2: Fire elemental")
    fire = composer.generate_sprite(
        "fire flame torch",
        style="fantasy",
        size=16,
        tags=["effect", "fire"]
    )
    
    # Test 3: Water
    print("\nTest 3: Ocean water")
    water = composer.generate_sprite(
        "ocean water wave",
        style="ocean",
        size=16,
        tags=["tile", "water"]
    )
    
    # Test 4: Character
    print("\nTest 4: NPC character")
    character = composer.generate_sprite(
        "character person npc",
        style="scifi",
        size=16,
        tags=["character", "npc"]
    )
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETE")
    print("="*60)
    print(f"\nGenerated {4} sprites in: {composer.output_dir}")
    print("\nCheck the output directory for:")
    print("  - PNG files (scaled 4x for visibility)")
    print("  - ZON metadata files")
    print("\n💡 To use in Godot:")
    print("  1. Copy PNG files to res://assets/sprites/")
    print("  2. Import as sprites with Filter=Nearest")
    print("  3. Use in your scenes")
