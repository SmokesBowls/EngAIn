# EngAIn Narrative Pipeline GUI

**AI Logic Built for AI, Not Humans**

## Quick Start

### Linux/macOS
```bash
./launch_gui.sh
```

### Windows
```
launch_gui.bat
```

### Direct Python
```bash
python3 narrative_pipeline_gui.py
```

## Prerequisites

- Python 3.7+
- tkinter (usually included with Python)
- All pipeline scripts must be in the same directory:
  - `pass1_explicit.py`
  - `pass2_core.py` or `pass2_enhanced.py`
  - `pass3_merge.py`
  - `pass4_zon_bridge.py`
  - `lore_to_zon.py`

### Installing tkinter

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk
```

**Fedora:**
```bash
sudo dnf install python3-tkinter
```

**macOS:**
Usually included with Python

**Windows:**
Usually included with Python from python.org

## Features

### Narrative Processing Tab
1. **Select narrative file** (.txt)
2. **Set metadata:**
   - Era (e.g., "FirstAge")
   - Location (e.g., "Beach")
   - Scope (narrative/canon/lore/event)
3. **Click "▶ Process Narrative"**
4. **View progress** in real-time
5. **Check results** summary

### Lore Conversion Tab
1. **Add lore files** (.zw files)
2. **Click "▶ Convert to ZON"**
3. **View conversion** output

### Settings Tab
- Change output directory
- View current configuration

## Output Files

The GUI creates outputs in `./narrative_work/`:

```
narrative_work/
├── out_pass1_*.txt          # Semantic structure
├── out_pass2_*.metta        # Inference atoms
├── zonj_*.json              # Merged scene data
└── zon/
    ├── *.zon                # Human-readable ZON
    └── *.zonj.json          # Canonical JSON
```

## Workflow

### Processing a Narrative

1. **Prepare your narrative:**
   ```
   # Part 1: The Awakening
   
   Senareth stood at the edge. *Why are they afraid?* she wondered.
   
   "We should establish shelter," Vairis said.
   ```

2. **Save as .txt file**

3. **Launch GUI and select file**

4. **Set metadata:**
   - Era: `FirstAge`
   - Location: `Beach`
   - Scope: `narrative`

5. **Process** and wait for completion

6. **Check outputs** in `./narrative_work/zon/`

### Converting Lore Files

1. **Prepare ZW lore file:**
   ```
   ZW_EVENT_SEED:
     id: genesis
     era: First Age
     tags: [cosmic, origin]
   ```

2. **Add to GUI** (can add multiple)

3. **Convert** and check outputs

## Troubleshooting

### GUI won't start
- Check Python 3 is installed: `python3 --version`
- Check tkinter: `python3 -c "import tkinter"`
- Try direct: `python3 narrative_pipeline_gui.py`

### Pipeline scripts not found
- Ensure all `.py` scripts are in the same directory as GUI
- Check permissions: scripts should be readable

### Output directory errors
- Check write permissions
- Try changing output directory in Settings tab

### Processing fails
1. Check pipeline progress log for errors
2. Verify input file format
3. Test with small sample first (5-10 lines)
4. Check individual scripts work:
   ```bash
   python3 pass1_explicit.py test.txt
   ```

## Architecture

```
┌─────────────────┐
│  Select File    │
└────────┬────────┘
         │
    ┌────▼────┐
    │  Pass 1 │ Semantic Structure
    └────┬────┘
         │
    ┌────▼────┐
    │  Pass 2 │ Inference Extraction
    └────┬────┘
         │
    ┌────▼────┐
    │  Pass 3 │ ZONJ Merging
    └────┬────┘
         │
    ┌────▼────┐
    │  Pass 4 │ ZON Bridge
    └────┬────┘
         │
    ┌────▼────────┐
    │  ZON Memory │
    │   Fabric    │
    └─────────────┘
```

## Pipeline Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| pass1_explicit.py | Semantic structure | *.txt | out_pass1_*.txt |
| pass2_core.py | Inference (fast) | out_pass1_*.txt | out_pass2_*.metta |
| pass2_enhanced.py | Inference (advanced) | out_pass1_*.txt | out_pass2_*.metta |
| pass3_merge.py | ZONJ merging | pass1 + pass2 | zonj_*.json |
| pass4_zon_bridge.py | ZON conversion | zonj_*.json | *.zon + *.zonj.json |
| lore_to_zon.py | Lore conversion | *.zw | *.zon + *.zonj.json |

## Tips

- **Start small:** Test with 5-10 line narratives first
- **Check outputs:** Inspect each stage's output before continuing
- **Use enhanced Pass 2:** For complex narratives with multiple characters
- **Set proper metadata:** Era/Location affect ZON anchoring
- **View outputs:** Click "View ZON Output" to open output directory

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Run test pipeline: `python3 test_full_pipeline.py`
3. Verify individual scripts work standalone
4. Check project documentation

---

**EngAIn Pipeline** • World Model as Truth • ZW → ZON4D Memory Fabric
