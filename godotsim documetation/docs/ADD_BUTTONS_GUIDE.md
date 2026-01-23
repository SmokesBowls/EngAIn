# Add Clickable Buttons to Your Test Scene

## Why Keyboard Isn't Working

The game window needs **focus** (be the active window) for keyboard input to work. Easier solution: **add actual buttons you can click!**

## Quick Fix - Add Buttons

### Replace Your TestZWScene.gd

1. In Godot, double-click `TestZWScene.gd` in FileSystem
2. Select All (Ctrl+A), Delete
3. Copy **all the code** from `TestZWScene_with_buttons.gd`
4. Paste into the empty editor
5. Save (Ctrl+S)
6. Run (F5)

Now you'll see **5 clickable buttons** in the game window:
```
┌─────────────────────────┐
│ 1 - Greeter (Low Rep)   │
│ 2 - Greeter (High Rep)  │
│ 3 - Merchant            │
│                         │
│ R - Reload Blocks       │
│ D - Dump State          │
└─────────────────────────┘
```

## What Each Button Does

| Button | Action | What Happens |
|--------|--------|--------------|
| **1 - Greeter (Low Rep)** | Test dialogue with low reputation | Sends interaction command to Python |
| **2 - Greeter (High Rep)** | Test dialogue with high reputation | Sends interaction command to Python |
| **3 - Merchant** | Test merchant interaction | Sends trade command to Python |
| **R - Reload Blocks** | Reload ZW/ZON blocks | Python reloads game logic |
| **D - Dump State** | Print full state | Python dumps everything to terminal |

## Try It Now

1. **Click "R - Reload Blocks"**
2. Watch **both consoles**:
   - Godot Output: "→ Reload command sent!"
   - Python terminal: "Reloading blocks..."

3. **Click "D - Dump State"**
4. Check Python terminal for full state dump

5. **Click "1 - Greeter (Low Rep)"**
6. Watch Godot Output: "[TEST] Greeter with low reputation"

## Keyboard Still Works Too

If you click on the game window first (to give it focus), you can also press:
- **1**, **2**, **3** for tests
- **R** for reload
- **D** for dump

But now you don't need to - just click the buttons!

## Bonus: Quieter Output

The new version also only prints snapshot updates when something interesting happens (entities or events present), so less spam!

---

**TL;DR**: Replace TestZWScene.gd with the button version, run F5, click the buttons!
