# Make Your Test Buttons Actually DO Something!

## What's New in Enhanced Runtime

The new `sim_runtime_enhanced.py` makes your test buttons spawn actual entities with dialogue!

## Quick Setup

1. **Stop your current Python server** (Ctrl+C in terminal)
2. **Replace the file**:
   ```bash
   cp sim_runtime_enhanced.py sim_runtime.py
   ```
   Or just rename it to `sim_runtime.py`
3. **Restart**: `python3 sim_runtime.py`
4. **Click the buttons in Godot** and watch the magic!

## What Happens Now

### Button 1: Greeter (Low Rep)
**Before:** Just prints a test message  
**After:**
```python
✓ Spawned greeter with id greeter_main
  Greeter spawned: 'What do you want?' (mood: unfriendly)
```

**In snapshot:**
```json
"entities": {
  "greeter_main": {
    "type": "greeter",
    "position": {"x": 5, "y": 0, "z": 3},
    "dialogue": "What do you want?",
    "mood": "unfriendly",
    "reputation": 10
  }
}
```

### Button 2: Greeter (High Rep)
**After:**
```python
✓ Spawned greeter with id greeter_main
  Greeter spawned: 'Welcome back, friend!' (mood: friendly)
```

Same entity, but dialogue and mood change based on reputation!

### Button 3: Merchant
**After:**
```python
✓ Spawned merchant with id merchant_main
  Merchant spawned: 'What would you like to buy?'
  Inventory: ['sword', 'potion', 'shield']
```

**In snapshot:**
```json
"entities": {
  "merchant_main": {
    "type": "merchant",
    "dialogue": "What would you like to buy?",
    "willing_to_trade": true,
    "inventory": ["sword", "potion", "shield"]
  }
}
```

## How It Works

The enhanced runtime handles `"action": "interact"` commands:

```python
def _handle_interaction(self, cmd):
    entity = cmd.get("entity")  # "greeter" or "merchant"
    player_rep = cmd.get("player_rep", 50)
    
    if entity == "greeter":
        # Create greeter with reputation-based dialogue
        if player_rep < 30:
            dialogue = "What do you want?"
            mood = "unfriendly"
        elif player_rep < 70:
            dialogue = "Hello there."
            mood = "neutral"
        else:
            dialogue = "Welcome back, friend!"
            mood = "friendly"
        
        # Add to snapshot
        self.snapshot["entities"]["greeter_main"] = {
            "type": "greeter",
            "dialogue": dialogue,
            "mood": mood,
            ...
        }
```

## Watch It Live!

1. **In Python terminal** - See entity spawn messages
2. **In Godot Output** - See snapshot updates with entities
3. **Events also fire** - dialogue_started, trade_initiated

## Try This Sequence

1. Click **"D - Dump State"** → See empty entities
2. Click **"1 - Greeter (Low Rep)"** → Greeter spawns!
3. Click **"D - Dump State"** → See greeter in entities
4. Click **"3 - Merchant"** → Merchant spawns!
5. Click **"D - Dump State"** → See both entities

## Godot Will Show Entity Count

Your Godot console should now show:
```
[SNAPSHOT UPDATE]
  Entities: 1  ← Something spawned!
  Events: 1
```

## Customize the Responses

Edit `_handle_interaction()` in sim_runtime_enhanced.py:

```python
# Change greeter dialogue
if player_rep < 30:
    dialogue = "Get lost, stranger!"  # More aggressive
    
# Change merchant inventory
"inventory": ["magic_sword", "dragon_scale", "elixir"]

# Add more entity types
elif entity == "guard":
    self.snapshot["entities"]["guard_1"] = {
        "type": "guard",
        "dialogue": "Halt!",
        ...
    }
```

## Next Steps

Once you see entities spawning, you can:

1. **Add more test buttons** for different NPCs
2. **Wire up real dialogue trees** from ZON4D
3. **Connect to Perception3D** to have NPCs react to player
4. **Add Behavior3D** for AI-controlled NPCs
5. **Link to Combat3D** for guard encounters

---

**TL;DR**: Replace sim_runtime.py with enhanced version, restart, click buttons, watch entities spawn with dialogue! 🎉
