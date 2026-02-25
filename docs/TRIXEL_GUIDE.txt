# TRIXEL COMPOSER GUIDE
## AI Pixel Artist for EngAIn

**Status:** Operational  
**Purpose:** Generate pixel art sprites from text descriptions

---

## 🎨 **What It Does**

Trixel Composer is your **onboard AI artist** that generates game assets:

- **Sprites** (characters, items, effects)
- **Tiles** (walls, floors, terrain)
- **UI elements** (buttons, icons)
- **Effects** (fire, water, magic)

**Outputs:**
- PNG files (Godot-ready)
- ZON metadata (style, palette, creation time)
- Organized by style/palette

---

## ⚡ **Quick Start**

```bash
cd ~/godotsim
python3 trixel_composer.py
```

Generates 4 test sprites with ZON metadata in `./trixel_output/`

---

## 🔧 **Basic Usage**

```python
from trixel_composer import TrixelComposer

# Initialize
composer = TrixelComposer(output_dir="./assets/sprites")

# Generate sprite
asset = composer.generate_sprite(
    prompt="fire elemental creature",
    style="fantasy",  # or: scifi, ocean, forest, monochrome
    size=16,          # 16x16 pixels
    tags=["enemy", "fire"]
)

print(f"Created: {asset.filepath}")
```

---

## 🎨 **Available Palettes**

| Style | Colors | Best For |
|-------|--------|----------|
| fantasy | Dark, red, warm, gold, white | Medieval, RPG, dungeon |
| scifi | Purple, blue, gray | Space, cyberpunk, tech |
| ocean | Deep blue to foam | Underwater, water |
| forest | Dark, browns, oranges | Nature, trees, wood |
| monochrome | Black to white | Retro, minimalist |

---

## 🎮 **Use in Godot**

1. Copy sprites: `cp trixel_output/*.png ~/godotsim/assets/sprites/`
2. In Godot: Import as texture with **Filter: Nearest**
3. Use in scene:
   ```gdscript
   var sprite = Sprite2D.new()
   sprite.texture = load("res://assets/sprites/trixel_fantasy_abc123.png")
   ```

---

## 📁 **Output Structure**

```
trixel_output/
├── trixel_fantasy_abc123_timestamp.png  # 64x64 (scaled 4x)
├── trixel_fantasy_abc123_timestamp.zon  # ZON metadata
```

**ZON Format:**
```
#ZON art/0.1
@id: trixel_fantasy_abc123_timestamp
@scope: trixel
@when: 2024-12-18T14:31:30Z
@where: Assets/Trixel/fantasy
@summary: stone wall brick tile
@tags: tile|wall|fantasy|sprite
=bullets
- filepath: ./trixel_output/trixel_fantasy_abc123.png
- style: fantasy
- type: sprite
=end
```

---

## 🚀 **Integration with EngAIn**

Add to your runtime:

```python
from trixel_composer import TrixelComposer

class EngAInRuntime:
    def __init__(self):
        self.trixel = TrixelComposer()
        
    def generate_asset(self, prompt, style="fantasy"):
        return self.trixel.generate_sprite(prompt, style)
```

---

## 🎯 **Keyword Recognition**

Procedural patterns for these keywords:

| Keywords | Pattern |
|----------|---------|
| wall, brick, stone | Brick wall |
| fire, flame, torch | Animated fire |
| water, ocean, wave | Water waves |
| tree, forest, plant | Simple tree |
| character, person, npc | Humanoid sprite |

**Extend:** Add patterns in `_generate_procedural_sprite()`

---

## 🔮 **Upgrade to Stable Diffusion** (Optional)

```bash
pip install diffusers torch --break-system-packages
```

Then modify Trixel to call SD API for real AI art.
*Note: Requires GPU, slower than procedural*

---

**You have an AI artist. Start generating.** 🎨
