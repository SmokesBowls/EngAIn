#!/usr/bin/env python3
"""
ZW Empire GUI - Visual editor and validator for ZW files
Place this in: ~/Downloads/EngAIn/gui/
Run from project root: cd ~/Downloads/EngAIn && python3 gui/zw_gui.py
"""

import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Now imports will work
from core.zw.zw_parser import parse_zw
from gui.official_zw_validator import ZWValidator, ZWValidationError
import json


class ZWEditorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ZW Empire Editor")
        self.root.geometry("1200x800")
        
        self.current_file = None
        self.zw_content = ""
        
        self._create_menu()
        self._create_ui()
    
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open .zw", command=self.open_file)
        file_menu.add_command(label="Save .zw", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Parse", command=self.parse_content)
        tools_menu.add_command(label="Validate", command=self.validate_content)
        tools_menu.add_command(label="Clear Output", command=self.clear_output)
    
    def _create_ui(self):
        """Create main UI layout"""
        
        # Top toolbar
        toolbar = tk.Frame(self.root, bg='#2b2b2b', height=50)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        tk.Button(toolbar, text="📂 Open", command=self.open_file, 
                 bg='#3c3f41', fg='white', padx=10).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="💾 Save", command=self.save_file,
                 bg='#3c3f41', fg='white', padx=10).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="🔍 Parse", command=self.parse_content,
                 bg='#3c3f41', fg='white', padx=10).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="✓ Validate", command=self.validate_content,
                 bg='#3c3f41', fg='white', padx=10).pack(side=tk.LEFT, padx=5, pady=5)
        
        # File path label
        self.file_label = tk.Label(toolbar, text="No file loaded", 
                                   bg='#2b2b2b', fg='white')
        self.file_label.pack(side=tk.LEFT, padx=20)
        
        # Main content area - split pane
        paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - ZW Editor
        left_frame = tk.Frame(paned)
        paned.add(left_frame, width=600)
        
        tk.Label(left_frame, text="ZW Content", font=('Arial', 12, 'bold')).pack(pady=5)
        
        self.zw_editor = scrolledtext.ScrolledText(
            left_frame, 
            wrap=tk.WORD, 
            font=('Courier', 10),
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='white'
        )
        self.zw_editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right panel - Output/Results
        right_frame = tk.Frame(paned)
        paned.add(right_frame, width=600)
        
        # Tabbed output
        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Parsed output tab
        parse_frame = tk.Frame(notebook)
        notebook.add(parse_frame, text="Parsed")
        
        self.parse_output = scrolledtext.ScrolledText(
            parse_frame,
            wrap=tk.WORD,
            font=('Courier', 9),
            bg='#1e1e1e',
            fg='#d4d4d4'
        )
        self.parse_output.pack(fill=tk.BOTH, expand=True)
        
        # Validation output tab
        valid_frame = tk.Frame(notebook)
        notebook.add(valid_frame, text="Validation")
        
        self.valid_output = scrolledtext.ScrolledText(
            valid_frame,
            wrap=tk.WORD,
            font=('Courier', 9),
            bg='#1e1e1e',
            fg='#d4d4d4'
        )
        self.valid_output.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_bar = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def open_file(self):
        """Open a ZW file"""
        filepath = filedialog.askopenfilename(
            title="Open ZW File",
            filetypes=[
                ("ZW Files", "*.zw"),
                ("All Files", "*.*")
            ]
        )
        
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                
                self.current_file = filepath
                self.zw_content = content
                self.zw_editor.delete(1.0, tk.END)
                self.zw_editor.insert(1.0, content)
                
                self.file_label.config(text=os.path.basename(filepath))
                self.status_bar.config(text=f"Loaded: {filepath}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file:\n{e}")
    
    def save_file(self):
        """Save ZW file"""
        if not self.current_file:
            filepath = filedialog.asksaveasfilename(
                title="Save ZW File",
                defaultextension=".zw",
                filetypes=[("ZW Files", "*.zw"), ("All Files", "*.*")]
            )
            if not filepath:
                return
            self.current_file = filepath
        
        try:
            content = self.zw_editor.get(1.0, tk.END)
            with open(self.current_file, 'w') as f:
                f.write(content)
            
            self.status_bar.config(text=f"Saved: {self.current_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")
    
    def parse_content(self):
        """Parse ZW content and display result"""
        content = self.zw_editor.get(1.0, tk.END).strip()
        
        if not content:
            self.parse_output.delete(1.0, tk.END)
            self.parse_output.insert(1.0, "No content to parse")
            return
        
        try:
            parsed = parse_zw(content)
            formatted = json.dumps(parsed, indent=2)
            
            self.parse_output.delete(1.0, tk.END)
            self.parse_output.insert(1.0, "✅ Parse successful!\n\n")
            self.parse_output.insert(tk.END, formatted)
            
            self.status_bar.config(text="Parse successful")
            
        except Exception as e:
            self.parse_output.delete(1.0, tk.END)
            self.parse_output.insert(1.0, f"❌ Parse failed:\n\n{e}")
            self.status_bar.config(text="Parse failed")
    
    def validate_content(self):
        """Validate ZW content"""
        content = self.zw_editor.get(1.0, tk.END).strip()
        
        if not content:
            self.valid_output.delete(1.0, tk.END)
            self.valid_output.insert(1.0, "No content to validate")
            return
        
        try:
            # Parse first
            parsed = parse_zw(content)
            
            # Validate
            validator = ZWValidator(strict=False)
            is_valid = validator.validate(parsed)
            
            # Display results
            self.valid_output.delete(1.0, tk.END)
            
            if is_valid:
                self.valid_output.insert(1.0, "✅ VALIDATION PASSED\n\n")
                self.valid_output.insert(tk.END, validator.get_report())
            else:
                self.valid_output.insert(1.0, "❌ VALIDATION FAILED\n\n")
                self.valid_output.insert(tk.END, validator.get_report())
            
            self.status_bar.config(text="Validation complete")
            
        except ZWValidationError as e:
            self.valid_output.delete(1.0, tk.END)
            self.valid_output.insert(1.0, f"❌ VALIDATION ERROR:\n\n{e}")
            self.status_bar.config(text="Validation error")
            
        except Exception as e:
            self.valid_output.delete(1.0, tk.END)
            self.valid_output.insert(1.0, f"❌ ERROR:\n\n{e}")
            self.status_bar.config(text="Error during validation")
    
    def clear_output(self):
        """Clear all output panels"""
        self.parse_output.delete(1.0, tk.END)
        self.valid_output.delete(1.0, tk.END)
        self.status_bar.config(text="Output cleared")


def main():
    root = tk.Tk()
    app = ZWEditorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
