#!/usr/bin/env python3
"""
ZW Empire GUI - Enhanced with core logic
Architecture: Core Logic → Observer Pattern → Decorator Pattern

Place in: ~/Downloads/EngAIn/gui/
Run: cd ~/Downloads/EngAIn && python3 gui/zw_gui_enhanced.py
"""

import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import json

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Core imports
from core.zw.zw_parser import parse_zw
from core.zon.zon_binary_pack import pack_to_zonb, unpack_from_zonb
from gui.official_zw_validator import ZWValidator, ZWValidationError


class ZWEditorCore:
    """
    Core logic layer - business logic without UI concerns
    Ready for Observer pattern integration
    """
    
    def __init__(self):
        self.current_file = None
        self.zw_content = ""
        self.parsed_data = None
        self.validation_result = None
        self.stats = {}
    
    def load_file(self, filepath):
        """Load ZW or ZONB file"""
        with open(filepath, 'r') as f:
            content = f.read()
        
        self.current_file = filepath
        self.zw_content = content
        return content
    
    def save_file(self, filepath, content):
        """Save ZW file"""
        with open(filepath, 'w') as f:
            f.write(content)
        self.current_file = filepath
    
    def parse(self, content):
        """Parse ZW content"""
        self.parsed_data = parse_zw(content)
        return self.parsed_data
    
    def validate(self, content=None, zw_type=None):
        """Validate ZW content"""
        if content:
            parsed = parse_zw(content)
        else:
            parsed = self.parsed_data
        
        validator = ZWValidator(strict=False)
        is_valid = validator.validate(parsed, zw_type)
        
        self.validation_result = {
            'valid': is_valid,
            'report': validator.get_report(),
            'errors': validator.errors,
            'warnings': validator.warnings
        }
        
        return self.validation_result
    
    def pack_to_zonb(self, zw_content, output_path):
        """Pack ZW to ZONB binary format"""
        # Parse ZW to dict
        parsed = parse_zw(zw_content)
        
        # Convert to JSON bytes
        json_bytes = json.dumps(parsed).encode('utf-8')
        
        # Pack to ZONB
        zonb_data = pack_to_zonb(parsed)
        
        # Write binary
        with open(output_path, 'wb') as f:
            f.write(zonb_data)
        
        return len(zonb_data)
    
    def unpack_zonb(self, zonb_path):
        """Unpack ZONB to viewable format"""
        with open(zonb_path, 'rb') as f:
            zonb_data = f.read()
        
        unpacked = unpack_from_zonb(zonb_data)
        return unpacked
    
    def calculate_compression_stats(self, zw_content):
        """Calculate compression statistics"""
        # ZW metrics
        zw_tokens = len(zw_content.split())
        zw_chars = len(zw_content)
        
        # Parse to get equivalent JSON
        parsed = parse_zw(zw_content)
        json_content = json.dumps(parsed, indent=2)
        
        json_tokens = len(json_content.split())
        json_chars = len(json_content)
        
        # Calculate ratios
        token_ratio = json_tokens / zw_tokens if zw_tokens > 0 else 0
        char_ratio = json_chars / zw_chars if zw_chars > 0 else 0
        
        token_savings = ((json_tokens - zw_tokens) / json_tokens * 100) if json_tokens > 0 else 0
        char_savings = ((json_chars - zw_chars) / json_chars * 100) if json_chars > 0 else 0
        
        self.stats = {
            'zw_tokens': zw_tokens,
            'zw_chars': zw_chars,
            'json_tokens': json_tokens,
            'json_chars': json_chars,
            'token_ratio': token_ratio,
            'char_ratio': char_ratio,
            'token_savings': token_savings,
            'char_savings': char_savings
        }
        
        return self.stats
    
    @staticmethod
    def get_template(template_type):
        """Get ZW templates for common structures"""
        templates = {
            'container': '''{container
  {type object}
  {id CHEST}
  {description "a wooden chest"}
  {flags [OPENBIT TRANSBIT]}
  {contents [
    {item {id EXAMPLE} {quantity 1}}
  ]}
}''',
            'npc': '''{npc
  {type character}
  {id GUARD}
  {description "a stern guard"}
  {level 5}
  {health 100}
  {hostile false}
  {dialogue [
    {greeting "Halt! State your business."}
  ]}
}''',
            'room': '''{room
  {type scene}
  {id CHAMBER}
  {description "a dimly lit chamber"}
  {exits [
    {direction north} {leads_to CORRIDOR}
    {direction south} {leads_to ENTRANCE}
  ]}
  {objects []}
}''',
            'item': '''{item
  {type object}
  {id SWORD}
  {description "a sharp sword"}
  {flags [WEAPONBIT TAKEBIT]}
  {damage 15}
  {weight 5}
}''',
            'rule': '''{rule
  {type zon-memory}
  {id example_rule}
  {condition all_of}
  {requires [
    {flag "condition_met"}
  ]}
  {effect [
    {action "trigger_event"}
  ]}
}'''
        }
        
        return templates.get(template_type, "")


class ZWEditorGUI:
    """
    UI layer - ready for Observer and Decorator patterns
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("ZW Empire Editor - Enhanced")
        self.root.geometry("1400x900")
        
        # Core logic instance
        self.core = ZWEditorCore()
        
        self._create_menu()
        self._create_ui()
    
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open ZW File", command=self.open_zw_file)
        file_menu.add_command(label="Open ZONB File", command=self.open_zonb_file)
        file_menu.add_separator()
        file_menu.add_command(label="Save ZW", command=self.save_zw_file)
        file_menu.add_command(label="Pack to ZONB", command=self.pack_to_zonb)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Clear", command=self.clear_editor)
        
        # Templates menu
        template_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Templates", menu=template_menu)
        template_menu.add_command(label="Container", command=lambda: self.insert_template('container'))
        template_menu.add_command(label="NPC", command=lambda: self.insert_template('npc'))
        template_menu.add_command(label="Room", command=lambda: self.insert_template('room'))
        template_menu.add_command(label="Item", command=lambda: self.insert_template('item'))
        template_menu.add_command(label="Rule", command=lambda: self.insert_template('rule'))
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Parse", command=self.parse_content)
        tools_menu.add_command(label="Validate", command=self.validate_content)
        tools_menu.add_command(label="Compression Stats", command=self.show_compression_stats)
        tools_menu.add_separator()
        tools_menu.add_command(label="Clear Output", command=self.clear_output)
    
    def _create_ui(self):
        """Create main UI layout"""
        
        # Top toolbar
        toolbar = tk.Frame(self.root, bg='#2b2b2b', height=60)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # File operations
        tk.Button(toolbar, text="📂 Open ZW", command=self.open_zw_file, 
                 bg='#3c3f41', fg='white', padx=10, pady=5).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="💾 Save", command=self.save_zw_file,
                 bg='#3c3f41', fg='white', padx=10, pady=5).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Frame(toolbar, bg='#2b2b2b', width=20).pack(side=tk.LEFT)  # Separator
        
        # Analysis operations
        tk.Button(toolbar, text="🔍 Parse", command=self.parse_content,
                 bg='#3c3f41', fg='white', padx=10, pady=5).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="✓ Validate", command=self.validate_content,
                 bg='#3c3f41', fg='white', padx=10, pady=5).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="📊 Stats", command=self.show_compression_stats,
                 bg='#3c3f41', fg='white', padx=10, pady=5).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Frame(toolbar, bg='#2b2b2b', width=20).pack(side=tk.LEFT)  # Separator
        
        # Binary operations
        tk.Button(toolbar, text="📦 Pack ZONB", command=self.pack_to_zonb,
                 bg='#4a5f3a', fg='white', padx=10, pady=5).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="🔓 Open ZONB", command=self.open_zonb_file,
                 bg='#4a5f3a', fg='white', padx=10, pady=5).pack(side=tk.LEFT, padx=5, pady=5)
        
        # File path label
        self.file_label = tk.Label(toolbar, text="No file loaded", 
                                   bg='#2b2b2b', fg='white', font=('Arial', 10))
        self.file_label.pack(side=tk.LEFT, padx=20)
        
        # Main content area - split pane
        paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - ZW Editor
        left_frame = tk.Frame(paned)
        paned.add(left_frame, width=700)
        
        editor_label = tk.Frame(left_frame, bg='#2b2b2b')
        editor_label.pack(fill=tk.X)
        tk.Label(editor_label, text="ZW Content", font=('Arial', 12, 'bold'),
                bg='#2b2b2b', fg='white').pack(side=tk.LEFT, padx=10, pady=5)
        
        # Template quick-buttons
        template_frame = tk.Frame(editor_label, bg='#2b2b2b')
        template_frame.pack(side=tk.RIGHT, padx=10)
        
        for name in ['container', 'npc', 'room', 'item', 'rule']:
            tk.Button(template_frame, text=name.capitalize(), 
                     command=lambda n=name: self.insert_template(n),
                     bg='#3c3f41', fg='white', padx=5, pady=2, font=('Arial', 8)).pack(side=tk.LEFT, padx=2)
        
        self.zw_editor = scrolledtext.ScrolledText(
            left_frame, 
            wrap=tk.WORD, 
            font=('Courier', 11),
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='white',
            selectbackground='#264f78'
        )
        self.zw_editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right panel - Output/Results
        right_frame = tk.Frame(paned)
        paned.add(right_frame, width=700)
        
        # Tabbed output
        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Parsed output tab
        parse_frame = tk.Frame(notebook)
        notebook.add(parse_frame, text="📋 Parsed")
        
        self.parse_output = scrolledtext.ScrolledText(
            parse_frame,
            wrap=tk.WORD,
            font=('Courier', 10),
            bg='#1e1e1e',
            fg='#d4d4d4'
        )
        self.parse_output.pack(fill=tk.BOTH, expand=True)
        
        # Validation output tab
        valid_frame = tk.Frame(notebook)
        notebook.add(valid_frame, text="✓ Validation")
        
        self.valid_output = scrolledtext.ScrolledText(
            valid_frame,
            wrap=tk.WORD,
            font=('Courier', 10),
            bg='#1e1e1e',
            fg='#d4d4d4'
        )
        self.valid_output.pack(fill=tk.BOTH, expand=True)
        
        # Stats tab
        stats_frame = tk.Frame(notebook)
        notebook.add(stats_frame, text="📊 Stats")
        
        self.stats_output = scrolledtext.ScrolledText(
            stats_frame,
            wrap=tk.WORD,
            font=('Courier', 10),
            bg='#1e1e1e',
            fg='#d4d4d4'
        )
        self.stats_output.pack(fill=tk.BOTH, expand=True)
        
        # ZONB viewer tab
        zonb_frame = tk.Frame(notebook)
        notebook.add(zonb_frame, text="📦 ZONB")
        
        self.zonb_output = scrolledtext.ScrolledText(
            zonb_frame,
            wrap=tk.WORD,
            font=('Courier', 10),
            bg='#1e1e1e',
            fg='#d4d4d4'
        )
        self.zonb_output.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_bar = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, 
                                   anchor=tk.W, font=('Arial', 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    # ========== File Operations ==========
    
    def open_zw_file(self):
        """Open a ZW file"""
        filepath = filedialog.askopenfilename(
            title="Open ZW File",
            filetypes=[("ZW Files", "*.zw"), ("All Files", "*.*")]
        )
        
        if filepath:
            try:
                content = self.core.load_file(filepath)
                
                self.zw_editor.delete(1.0, tk.END)
                self.zw_editor.insert(1.0, content)
                
                self.file_label.config(text=os.path.basename(filepath))
                self.status_bar.config(text=f"Loaded: {filepath}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file:\n{e}")
    
    def save_zw_file(self):
        """Save ZW file"""
        if not self.core.current_file:
            filepath = filedialog.asksaveasfilename(
                title="Save ZW File",
                defaultextension=".zw",
                filetypes=[("ZW Files", "*.zw"), ("All Files", "*.*")]
            )
            if not filepath:
                return
        else:
            filepath = self.core.current_file
        
        try:
            content = self.zw_editor.get(1.0, tk.END).strip()
            self.core.save_file(filepath, content)
            
            self.file_label.config(text=os.path.basename(filepath))
            self.status_bar.config(text=f"Saved: {filepath}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")
    
    def open_zonb_file(self):
        """Open and display ZONB binary file"""
        filepath = filedialog.askopenfilename(
            title="Open ZONB File",
            filetypes=[("ZONB Files", "*.zonb"), ("All Files", "*.*")]
        )
        
        if filepath:
            try:
                unpacked = self.core.unpack_zonb(filepath)
                formatted = json.dumps(unpacked, indent=2)
                
                self.zonb_output.delete(1.0, tk.END)
                self.zonb_output.insert(1.0, f"📦 ZONB File: {os.path.basename(filepath)}\n\n")
                self.zonb_output.insert(tk.END, formatted)
                
                # Get file size
                file_size = os.path.getsize(filepath)
                self.zonb_output.insert(tk.END, f"\n\n📏 File Size: {file_size} bytes")
                
                self.status_bar.config(text=f"Opened ZONB: {filepath}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open ZONB:\n{e}")
    
    # ========== Core Operations ==========
    
    def parse_content(self):
        """Parse ZW content and display result"""
        content = self.zw_editor.get(1.0, tk.END).strip()
        
        if not content:
            self.parse_output.delete(1.0, tk.END)
            self.parse_output.insert(1.0, "No content to parse")
            return
        
        try:
            parsed = self.core.parse(content)
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
            result = self.core.validate(content)
            
            self.valid_output.delete(1.0, tk.END)
            
            if result['valid']:
                self.valid_output.insert(1.0, "✅ VALIDATION PASSED\n\n")
            else:
                self.valid_output.insert(1.0, "❌ VALIDATION FAILED\n\n")
            
            self.valid_output.insert(tk.END, result['report'])
            
            self.status_bar.config(text="Validation complete")
            
        except Exception as e:
            self.valid_output.delete(1.0, tk.END)
            self.valid_output.insert(1.0, f"❌ ERROR:\n\n{e}")
            self.status_bar.config(text="Validation error")
    
    def pack_to_zonb(self):
        """Pack current ZW to ZONB binary"""
        content = self.zw_editor.get(1.0, tk.END).strip()
        
        if not content:
            messagebox.showwarning("Warning", "No content to pack")
            return
        
        # Get output path
        filepath = filedialog.asksaveasfilename(
            title="Pack to ZONB",
            defaultextension=".zonb",
            filetypes=[("ZONB Files", "*.zonb"), ("All Files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            byte_size = self.core.pack_to_zonb(content, filepath)
            
            messagebox.showinfo("Success", 
                f"Packed to ZONB successfully!\n\nFile: {os.path.basename(filepath)}\nSize: {byte_size} bytes")
            
            self.status_bar.config(text=f"Packed to: {filepath} ({byte_size} bytes)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to pack ZONB:\n{e}")
    
    def show_compression_stats(self):
        """Calculate and display compression statistics"""
        content = self.zw_editor.get(1.0, tk.END).strip()
        
        if not content:
            self.stats_output.delete(1.0, tk.END)
            self.stats_output.insert(1.0, "No content to analyze")
            return
        
        try:
            stats = self.core.calculate_compression_stats(content)
            
            self.stats_output.delete(1.0, tk.END)
            self.stats_output.insert(1.0, "📊 COMPRESSION ANALYSIS\n")
            self.stats_output.insert(tk.END, "="*60 + "\n\n")
            
            self.stats_output.insert(tk.END, "TOKEN COMPARISON:\n")
            self.stats_output.insert(tk.END, f"  ZW tokens:     {stats['zw_tokens']:5d}\n")
            self.stats_output.insert(tk.END, f"  JSON tokens:   {stats['json_tokens']:5d}\n")
            self.stats_output.insert(tk.END, f"  Ratio:         {stats['token_ratio']:.2f}x\n")
            self.stats_output.insert(tk.END, f"  Savings:       {stats['token_savings']:.1f}%\n\n")
            
            self.stats_output.insert(tk.END, "CHARACTER COMPARISON:\n")
            self.stats_output.insert(tk.END, f"  ZW chars:      {stats['zw_chars']:5d}\n")
            self.stats_output.insert(tk.END, f"  JSON chars:    {stats['json_chars']:5d}\n")
            self.stats_output.insert(tk.END, f"  Ratio:         {stats['char_ratio']:.2f}x\n")
            self.stats_output.insert(tk.END, f"  Savings:       {stats['char_savings']:.1f}%\n\n")
            
            self.stats_output.insert(tk.END, "="*60 + "\n")
            self.stats_output.insert(tk.END, "💡 ZW achieves compression by eliminating:\n")
            self.stats_output.insert(tk.END, "   • Colons after keys\n")
            self.stats_output.insert(tk.END, "   • Quotes around keys\n")
            self.stats_output.insert(tk.END, "   • Commas between elements\n")
            self.stats_output.insert(tk.END, "   • Redundant punctuation\n")
            
            self.status_bar.config(text=f"Stats: {stats['char_savings']:.1f}% character savings")
            
        except Exception as e:
            self.stats_output.delete(1.0, tk.END)
            self.stats_output.insert(1.0, f"❌ Stats calculation failed:\n\n{e}")
    
    # ========== Template Operations ==========
    
    def insert_template(self, template_type):
        """Insert a template at cursor position"""
        template = self.core.get_template(template_type)
        
        if template:
            self.zw_editor.insert(tk.INSERT, template + "\n\n")
            self.status_bar.config(text=f"Inserted {template_type} template")
    
    # ========== Utility Operations ==========
    
    def clear_editor(self):
        """Clear the editor"""
        if messagebox.askyesno("Clear", "Clear all content?"):
            self.zw_editor.delete(1.0, tk.END)
            self.status_bar.config(text="Editor cleared")
    
    def clear_output(self):
        """Clear all output panels"""
        self.parse_output.delete(1.0, tk.END)
        self.valid_output.delete(1.0, tk.END)
        self.stats_output.delete(1.0, tk.END)
        self.zonb_output.delete(1.0, tk.END)
        self.status_bar.config(text="Output cleared")


def main():
    root = tk.Tk()
    app = ZWEditorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
