#!/usr/bin/env python3
"""
narrative_pipeline_gui.py - Complete GUI for EngAIn Narrative Pipeline

Combines Pass 1-4 + Lore conversion in a single interface
"""

import sys
import os
import subprocess
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext


class NarrativePipelineGUI:
    """GUI for the complete narrative processing pipeline"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("EngAIn Narrative Pipeline")
        self.root.geometry("1200x800")
        
        # State
        self.current_narrative = None
        self.current_lore_files = []
        self.output_dir = Path("./narrative_work")
        self.output_dir.mkdir(exist_ok=True)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the user interface"""
        
        # Main container with notebook
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: Narrative Processing
        narrative_frame = ttk.Frame(notebook)
        notebook.add(narrative_frame, text="Narrative Processing")
        self._create_narrative_tab(narrative_frame)
        
        # Tab 2: Lore Conversion
        lore_frame = ttk.Frame(notebook)
        notebook.add(lore_frame, text="Lore Conversion")
        self._create_lore_tab(lore_frame)
        
        # Tab 3: Settings
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Settings")
        self._create_settings_tab(settings_frame)
        
        # Status bar
        self.status_bar = tk.Label(
            self.root,
            text="Ready",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _create_narrative_tab(self, parent):
        """Create narrative processing tab"""
        
        # Top: File selection and metadata
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # File selection
        file_frame = ttk.LabelFrame(top_frame, text="Input File", padding=5)
        file_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.narrative_file_label = tk.Label(
            file_frame,
            text="No file selected",
            fg="gray"
        )
        self.narrative_file_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            file_frame,
            text="Select Narrative...",
            command=self.select_narrative_file
        ).pack(side=tk.RIGHT, padx=5)
        
        # Metadata
        meta_frame = ttk.LabelFrame(top_frame, text="Metadata", padding=5)
        meta_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(meta_frame, text="Era:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.era_entry = ttk.Entry(meta_frame, width=30)
        self.era_entry.insert(0, "FirstAge")
        self.era_entry.grid(row=0, column=1, padx=5, pady=2)
        
        tk.Label(meta_frame, text="Location:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.location_entry = ttk.Entry(meta_frame, width=30)
        self.location_entry.insert(0, "Beach")
        self.location_entry.grid(row=1, column=1, padx=5, pady=2)
        
        tk.Label(meta_frame, text="Scope:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.scope_var = tk.StringVar(value="narrative")
        scope_combo = ttk.Combobox(
            meta_frame,
            textvariable=self.scope_var,
            values=["narrative", "canon", "lore", "event"],
            width=27,
            state="readonly"
        )
        scope_combo.grid(row=2, column=1, padx=5, pady=2)
        
        # Process button
        process_frame = ttk.Frame(top_frame)
        process_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            process_frame,
            text="▶ Process Narrative",
            command=self.process_narrative,
            style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            process_frame,
            text="View ZON Output",
            command=self.view_zon_output
        ).pack(side=tk.LEFT, padx=5)
        
        # Middle: Pipeline progress
        progress_frame = ttk.LabelFrame(parent, text="Pipeline Progress", padding=5)
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.progress_text = scrolledtext.ScrolledText(
            progress_frame,
            height=20,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.progress_text.pack(fill=tk.BOTH, expand=True)
        
        # Bottom: Results summary
        results_frame = ttk.LabelFrame(parent, text="Results", padding=5)
        results_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.results_label = tk.Label(
            results_frame,
            text="No results yet",
            fg="gray",
            justify=tk.LEFT,
            anchor=tk.W
        )
        self.results_label.pack(fill=tk.X)
    
    def _create_lore_tab(self, parent):
        """Create lore conversion tab"""
        
        # Top: File selection
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        file_frame = ttk.LabelFrame(top_frame, text="Lore Files", padding=5)
        file_frame.pack(fill=tk.BOTH, expand=True)
        
        # Listbox for files
        list_frame = ttk.Frame(file_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.lore_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            height=10
        )
        self.lore_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.lore_listbox.yview)
        
        # Buttons
        button_frame = ttk.Frame(file_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            button_frame,
            text="Add Files...",
            command=self.add_lore_files
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame,
            text="Clear All",
            command=self.clear_lore_files
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame,
            text="▶ Convert to ZON",
            command=self.convert_lore,
            style="Accent.TButton"
        ).pack(side=tk.RIGHT, padx=2)
        
        # Output
        output_frame = ttk.LabelFrame(parent, text="Conversion Output", padding=5)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.lore_output_text = scrolledtext.ScrolledText(
            output_frame,
            height=15,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.lore_output_text.pack(fill=tk.BOTH, expand=True)
    
    def _create_settings_tab(self, parent):
        """Create settings tab"""
        
        settings_frame = ttk.LabelFrame(parent, text="Output Settings", padding=10)
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(settings_frame, text="Output Directory:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        self.output_dir_label = tk.Label(
            settings_frame,
            text=str(self.output_dir),
            fg="blue"
        )
        self.output_dir_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Button(
            settings_frame,
            text="Change...",
            command=self.change_output_dir
        ).grid(row=0, column=2, padx=5)
        
        # Info frame
        info_frame = ttk.LabelFrame(parent, text="About", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        info_text = """EngAIn Narrative Pipeline

This tool converts raw narrative text and lore files into ZON memory fabric format.

Pipeline Stages:
• Pass 1: Semantic structure extraction
• Pass 2: Inference extraction (speakers, emotions, actions)
• Pass 3: ZONJ merging
• Pass 4: ZON memory fabric conversion

Output Formats:
• .zon - Human-readable ZON format
• .zonj.json - Canonical ZON JSON for EngAIn runtime

For more information, see the documentation files."""
        
        info_label = tk.Label(
            info_frame,
            text=info_text,
            justify=tk.LEFT,
            anchor=tk.NW
        )
        info_label.pack(fill=tk.BOTH, expand=True)
    
    # Narrative Processing Methods
    
    def select_narrative_file(self):
        """Select a narrative file"""
        filepath = filedialog.askopenfilename(
            title="Select Narrative File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if filepath:
            self.current_narrative = Path(filepath)
            self.narrative_file_label.config(
                text=self.current_narrative.name,
                fg="black"
            )
            self.status_bar.config(text=f"Loaded: {self.current_narrative.name}")
    
    def process_narrative(self):
        """Run the complete 4-pass pipeline"""
        if not self.current_narrative or not self.current_narrative.exists():
            messagebox.showerror("Error", "Please select a narrative file first")
            return
        
        # Clear progress
        self.progress_text.delete(1.0, tk.END)
        self.results_label.config(text="Processing...", fg="blue")
        self.root.update()
        
        try:
            base_name = self.current_narrative.stem
            
            # Pass 1
            self.log_progress("="*70)
            self.log_progress("PASS 1: Semantic Structure Extraction")
            self.log_progress("="*70)
            
            result = subprocess.run(
                [sys.executable, "pass1_explicit.py", str(self.current_narrative)],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            
            if result.returncode != 0:
                error_msg = f"Pass 1 failed:\n{result.stderr}\n{result.stdout}"
                raise Exception(error_msg)
            
            pass1_out = Path(f"out_pass1_{base_name}.txt")
            self.log_progress(f"✓ Created: {pass1_out}")
            
            # Pass 2
            self.log_progress("\n" + "="*70)
            self.log_progress("PASS 2: Inference Extraction")
            self.log_progress("="*70)
            
            result = subprocess.run(
                [sys.executable, "pass2_core.py", str(pass1_out)],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            
            if result.returncode != 0:
                error_msg = f"Pass 2 failed:\n{result.stderr}\n{result.stdout}"
                raise Exception(error_msg)
            
            pass2_out = Path(f"out_pass2_{base_name}.metta")
            self.log_progress(f"✓ Created: {pass2_out}")
            
            # Pass 3
            self.log_progress("\n" + "="*70)
            self.log_progress("PASS 3: ZONJ Merging")
            self.log_progress("="*70)
            
            result = subprocess.run(
                [sys.executable, "pass3_merge.py", str(pass1_out), str(pass2_out)],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            
            if result.returncode != 0:
                error_msg = f"Pass 3 failed:\n{result.stderr}\n{result.stdout}"
                raise Exception(error_msg)
            
            # Pass 3 creates zonj_{base_name}.json
            base_name = pass1_out.stem  # Remove .txt extension
            pass3_out = Path(f"zonj_{base_name}.json")
            self.log_progress(f"✓ Created: {pass3_out}")
            
            # Pass 4
            self.log_progress("\n" + "="*70)
            self.log_progress("PASS 4: ZON Memory Fabric Conversion")
            self.log_progress("="*70)
            
            zon_output_dir = self.output_dir / "zon"
            zon_output_dir.mkdir(exist_ok=True)
            
            result = subprocess.run(
                [sys.executable, "pass4_zon_bridge.py", str(pass3_out),
                 "--era", self.era_entry.get(),
                 "--location", self.location_entry.get(),
                 "--scope", self.scope_var.get(),
                 "--output-dir", str(zon_output_dir)],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            
            if result.returncode != 0:
                error_msg = f"Pass 4 failed:\n{result.stderr}\n{result.stdout}"
                raise Exception(error_msg)
            
            zon_file = zon_output_dir / f"{pass1_out.stem}.zon"
            zonj_file = zon_output_dir / f"{pass1_out.stem}.zonj.json"
            
            self.log_progress(f"✓ Created: {zon_file}")
            self.log_progress(f"✓ Created: {zonj_file}")
            
            # Show results
            self.log_progress("\n" + "="*70)
            self.log_progress("SUCCESS!")
            self.log_progress("="*70)
            
            # Load and analyze results
            with zonj_file.open("r") as f:
                zon_data = json.load(f)
            
            entities = zon_data.get("@entities", [])
            segments = len(zon_data.get("=segments", []))
            inferred = zon_data.get("=inferred", {})
            
            emotions_count = len(inferred.get("emotions", []))
            actions_count = len(inferred.get("actions", []))
            thoughts_count = len(inferred.get("thoughts", []))
            
            results_text = f"""✓ Pipeline Complete!

Output Files:
  • {zon_file.name}
  • {zonj_file.name}

Metadata:
  • Era: {self.era_entry.get()}
  • Location: {self.location_entry.get()}
  • Scope: {self.scope_var.get()}

Analysis:
  • Segments: {segments}
  • Entities: {len(entities)} ({', '.join(entities) if entities else 'none detected'})
  • Emotions: {emotions_count}
  • Actions: {actions_count}
  • Thoughts: {thoughts_count}

Output Directory: {zon_output_dir}"""
            
            self.results_label.config(text=results_text, fg="darkgreen")
            self.status_bar.config(text="Processing complete!")
            
        except Exception as e:
            self.log_progress(f"\n❌ ERROR: {e}")
            self.results_label.config(text=f"Error: {e}", fg="red")
            messagebox.showerror("Processing Error", str(e))
    
    def view_zon_output(self):
        """Open ZON output in system viewer"""
        zon_dir = self.output_dir / "zon"
        if zon_dir.exists():
            if sys.platform == "win32":
                os.startfile(zon_dir)
            elif sys.platform == "darwin":
                subprocess.run(["open", str(zon_dir)])
            else:
                subprocess.run(["xdg-open", str(zon_dir)])
        else:
            messagebox.showinfo("Info", "No output directory yet. Process a narrative first.")
    
    # Lore Processing Methods
    
    def add_lore_files(self):
        """Add lore files to the list"""
        filepaths = filedialog.askopenfilenames(
            title="Select Lore Files",
            filetypes=[("ZW Files", "*.zw"), ("All Files", "*.*")]
        )
        
        for filepath in filepaths:
            if filepath not in self.current_lore_files:
                self.current_lore_files.append(filepath)
                self.lore_listbox.insert(tk.END, Path(filepath).name)
        
        self.status_bar.config(text=f"Added {len(filepaths)} lore file(s)")
    
    def clear_lore_files(self):
        """Clear the lore files list"""
        self.current_lore_files = []
        self.lore_listbox.delete(0, tk.END)
        self.status_bar.config(text="Lore files cleared")
    
    def convert_lore(self):
        """Convert lore files to ZON"""
        if not self.current_lore_files:
            messagebox.showerror("Error", "Please add lore files first")
            return
        
        self.lore_output_text.delete(1.0, tk.END)
        self.root.update()
        
        try:
            lore_output_dir = self.output_dir / "lore_zon"
            lore_output_dir.mkdir(exist_ok=True)
            
            self.log_lore_progress("="*70)
            self.log_lore_progress(f"Converting {len(self.current_lore_files)} lore file(s)")
            self.log_lore_progress("="*70 + "\n")
            
            result = subprocess.run(
                [sys.executable, "lore_to_zon.py"] + self.current_lore_files +
                ["--batch", "--output-dir", str(lore_output_dir)],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            
            if result.returncode != 0:
                error_msg = f"Lore conversion failed:\n{result.stderr}\n{result.stdout}"
                raise Exception(error_msg)
            
            self.log_lore_progress(result.stdout)
            self.log_lore_progress("\n" + "="*70)
            self.log_lore_progress("SUCCESS!")
            self.log_lore_progress("="*70)
            self.log_lore_progress(f"\nOutput directory: {lore_output_dir}")
            
            self.status_bar.config(text=f"Converted {len(self.current_lore_files)} lore files")
            
        except Exception as e:
            self.log_lore_progress(f"\n❌ ERROR: {e}")
            messagebox.showerror("Conversion Error", str(e))
    
    # Utility Methods
    
    def change_output_dir(self):
        """Change output directory"""
        dirpath = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.output_dir
        )
        
        if dirpath:
            self.output_dir = Path(dirpath)
            self.output_dir_label.config(text=str(self.output_dir))
            self.status_bar.config(text=f"Output directory: {self.output_dir}")
    
    def log_progress(self, message):
        """Log to narrative progress text"""
        self.progress_text.insert(tk.END, message + "\n")
        self.progress_text.see(tk.END)
        self.root.update()
    
    def log_lore_progress(self, message):
        """Log to lore output text"""
        self.lore_output_text.insert(tk.END, message + "\n")
        self.lore_output_text.see(tk.END)
        self.root.update()


def main():
    root = tk.Tk()
    
    # Set style
    style = ttk.Style()
    style.theme_use('clam')  # Use clam theme for better appearance
    
    app = NarrativePipelineGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
