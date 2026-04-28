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
try:
    from core.zw_core import parse_zw
except ImportError:
    # Fallback for different project structures
    try:
        from godotengain.engainos.core.zw.zw_parser import parse_zw
    except ImportError:
        # Last resort - maybe running from godotengain root?
        from engainos.core.zw.zw_parser import parse_zw

from gui.official_zw_validator import ZWValidator, ZWValidationError
import json


class ZWEditorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ZW Empire Editor")
        self.root.geometry("1200x800")
        
        self.current_file = None
        self.original_content = ""
        self.zw_content = ""
        
        self._create_menu()
        self._create_ui()
        self._bind_shortcuts()

        # Intercept window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)
    
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open .zw", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save .zw", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit, accelerator="Ctrl+Q")
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Parse", command=self.parse_content)
        tools_menu.add_command(label="Validate", command=self.validate_content)
        tools_menu.add_command(label="Clear Output", command=self.clear_output)
    
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-q>', lambda e: self.on_exit())

        # Dirty checking on key release and cursor position
        self.zw_editor.bind('<KeyRelease>', self.on_key_release)
        self.zw_editor.bind('<ButtonRelease-1>', self.update_cursor_info)
        self.zw_editor.bind('<FocusIn>', self.update_cursor_info)
        self.zw_editor.bind('<<Modified>>', self.on_modified)

    def _create_ui(self):
        """Create main UI layout"""
        
        # Top toolbar
        toolbar = tk.Frame(self.root, bg='#2b2b2b', height=50)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        tk.Button(toolbar, text="📂 Open", command=self.open_file, 
                 bg='#3c3f41', fg='white', padx=10, cursor='hand2').pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="💾 Save", command=self.save_file,
                 bg='#3c3f41', fg='white', padx=10, cursor='hand2').pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="🔍 Parse", command=self.parse_content,
                 bg='#3c3f41', fg='white', padx=10, cursor='hand2').pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="✓ Validate", command=self.validate_content,
                 bg='#3c3f41', fg='white', padx=10, cursor='hand2').pack(side=tk.LEFT, padx=5, pady=5)
        
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
            insertbackground='white',
            undo=True,
            autoseparators=True
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
        self.parse_output.tag_config("success", foreground="#51cf66")
        self.parse_output.tag_config("error", foreground="#ff6b6b")
        self.parse_output.pack(fill=tk.BOTH, expand=True)
        self.parse_output.config(state=tk.DISABLED)

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
        self.valid_output.tag_config("success", foreground="#51cf66")
        self.valid_output.tag_config("error", foreground="#ff6b6b")
        self.valid_output.pack(fill=tk.BOTH, expand=True)
        self.valid_output.config(state=tk.DISABLED)

        # Status bar
        self.status_bar = tk.Frame(self.root, bd=1, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_label = tk.Label(self.status_bar, text="Ready", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.cursor_label = tk.Label(self.status_bar, text="Ln 1, Col 0", anchor=tk.E)
        self.cursor_label.pack(side=tk.RIGHT, padx=10)

        # Give initial focus to editor
        self.zw_editor.focus_set()

    def on_key_release(self, event=None):
        """Handle key release events"""
        self.check_changes()
        self.update_cursor_info()

    def on_modified(self, event=None):
        """Handle modified virtual event (e.g., undo, paste)"""
        if self.zw_editor.edit_modified():
            self.check_changes()
            self.update_cursor_info()
            # Reset modified flag so event can fire again
            self.zw_editor.edit_modified(False)

    def update_cursor_info(self, event=None):
        """Update cursor position in status bar"""
        try:
            # Get current position (line.col)
            index = self.zw_editor.index(tk.INSERT)
            line, col = index.split('.')
            self.cursor_label.config(text=f"Ln {line}, Col {col}")
        except Exception:
            pass

    def check_changes(self, event=None):
        """Check for unsaved changes and update title"""
        current = self.zw_editor.get(1.0, "end-1c")  # -1c to ignore trailing newline
        is_dirty = current != self.original_content

        title = "ZW Empire Editor"
        label_text = "No file loaded"

        if self.current_file:
            filename = os.path.basename(self.current_file)
            title += f" - {filename}"
            label_text = filename

        if is_dirty:
            title += " *"
            if self.current_file:
                label_text += " *"
            else:
                label_text = "Unsaved File *"

        self.root.title(title)
        if hasattr(self, 'file_label'):
            self.file_label.config(text=label_text)
        return is_dirty

    def confirm_discard(self):
        """
        Ask user to confirm discarding changes.
        Returns True if safe to proceed (discard or saved), False if cancelled.
        """
        if self.check_changes():
            response = messagebox.askyesno(
                "Unsaved Changes",
                "You have unsaved changes. Discard them?"
            )
            return response
        return True

    def on_exit(self):
        """Handle application exit"""
        if self.confirm_discard():
            self.root.quit()

    def open_file(self):
        """Open a ZW file"""
        if not self.confirm_discard():
            return

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
                
                # Normalize original content
                self.original_content = self.zw_editor.get(1.0, "end-1c")

                self.file_label.config(text=os.path.basename(filepath))
                self.status_label.config(text=f"Loaded: {filepath}", fg='black')
                self.check_changes()
                
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
            content = self.zw_editor.get(1.0, "end-1c")
            with open(self.current_file, 'w') as f:
                f.write(content)
            
            self.original_content = content
            self.status_label.config(text=f"Saved: {self.current_file}", fg='black')
            self.check_changes()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")
    
    def parse_content(self):
        """Parse ZW content and display result"""
        content = self.zw_editor.get(1.0, tk.END).strip()
        
        self.parse_output.config(state=tk.NORMAL)
        self.parse_output.delete(1.0, tk.END)

        if not content:
            self.parse_output.insert(1.0, "No content to parse")
            self.parse_output.config(state=tk.DISABLED)
            return
        
        try:
            parsed = parse_zw(content)
            formatted = json.dumps(parsed, indent=2)
            
            self.parse_output.insert(1.0, "✅ Parse successful!\n\n", "success")
            self.parse_output.insert(tk.END, formatted)
            
            self.status_label.config(text="Parse successful", fg="#51cf66")
            
        except Exception as e:
            self.parse_output.insert(1.0, f"❌ Parse failed:\n\n{e}", "error")
            self.status_label.config(text="Parse failed", fg="#ff6b6b")

        self.parse_output.config(state=tk.DISABLED)
    
    def validate_content(self):
        """Validate ZW content"""
        content = self.zw_editor.get(1.0, tk.END).strip()
        
        self.valid_output.config(state=tk.NORMAL)
        self.valid_output.delete(1.0, tk.END)

        if not content:
            self.valid_output.insert(1.0, "No content to validate")
            self.valid_output.config(state=tk.DISABLED)
            return
        
        try:
            # Parse first
            parsed = parse_zw(content)
            
            # Validate
            validator = ZWValidator(strict=False)
            is_valid = validator.validate(parsed)
            
            if is_valid:
                self.valid_output.insert(1.0, "✅ VALIDATION PASSED\n\n", "success")
                self.valid_output.insert(tk.END, validator.get_report())
                self.status_label.config(text="Validation complete", fg="#51cf66")
            else:
                self.valid_output.insert(1.0, "❌ VALIDATION FAILED\n\n", "error")
                self.valid_output.insert(tk.END, validator.get_report())
                self.status_label.config(text="Validation complete", fg="#ff6b6b")
            
        except ZWValidationError as e:
            self.valid_output.insert(1.0, f"❌ VALIDATION ERROR:\n\n{e}", "error")
            self.status_label.config(text="Validation error", fg="#ff6b6b")
            
        except Exception as e:
            self.valid_output.insert(1.0, f"❌ ERROR:\n\n{e}", "error")
            self.status_label.config(text="Error during validation", fg="#ff6b6b")

        self.valid_output.config(state=tk.DISABLED)
    
    def clear_output(self):
        """Clear all output panels"""
        self.parse_output.config(state=tk.NORMAL)
        self.parse_output.delete(1.0, tk.END)
        self.parse_output.config(state=tk.DISABLED)

        self.valid_output.config(state=tk.NORMAL)
        self.valid_output.delete(1.0, tk.END)
        self.valid_output.config(state=tk.DISABLED)

        self.status_label.config(text="Output cleared", fg='black')


def main():
    root = tk.Tk()
    app = ZWEditorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
