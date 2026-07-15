#!/usr/bin/env python3
"""
Pose Editor - Interactive character posing with per-part controls.
Integrates with existing Mechanimation code.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import math
from pathlib import Path
from PIL import Image, ImageTk

# Import existing modules
import primeanim_v4a  # for load_rig, render_with_layers, interpolate_pose
from biomechanical_constraints_fixed import BiomechanicalConstraintsFixed, get_preset

class PoseEditor:
    def __init__(self, root, rig_path, anim_path=None, preset="human_balanced"):
        self.root = root
        self.root.title("Mechanimation Pose Editor")
        self.root.geometry("1200x800")
        
        # Load rig
        self.rig = primeanim_v4a.load_rig(rig_path)
        self.all_parts = self._get_all_part_names(self.rig)
        
        # Load animation if provided
        self.anim = None
        self.duration = 1.0
        self.keyframes = []
        if anim_path:
            with open(anim_path) as f:
                self.anim = json.load(f)
            self.duration = self.anim['duration']
            self.keyframes = self.anim['keyframes']
        
        # Constraints
        self.config = get_preset(preset)
        self.constraints = BiomechanicalConstraintsFixed(self.config, rig_data=self._load_rig_data(rig_path))
        
        # Pose state
        self.base_pose = {}
        self.override_pose = {}
        self.saved_pose = {}   # part_name -> {attr: value}
        
        # Settings
        self.live_update = tk.BooleanVar(value=True)
        self.apply_constraints = tk.BooleanVar(value=True)
        
        # Current time
        self.current_time = 0.0
        
        # Build GUI
        self._build_gui()
        
        # Initial pose
        self._update_base_pose()
        self._sync_gui_from_pose()
        self.update_canvas()
    
    def _get_all_part_names(self, part):
        """Recursively collect all part names."""
        names = [part['name']]
        for child in part['children'].values():
            names.extend(self._get_all_part_names(child))
        return names
    
    def _load_rig_data(self, rig_path):
        """Helper to load the raw rig JSON for bone length calculation."""
        with open(rig_path) as f:
            return json.load(f)
    
    def _build_gui(self):
        # Main layout: canvas left, control panel right
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas area
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg='gray', width=512, height=512)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right panel: scrollable controls
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        # Top of right panel: global settings
        settings_frame = ttk.LabelFrame(right_frame, text="Settings")
        settings_frame.pack(fill=tk.X, pady=5)
        
        ttk.Checkbutton(settings_frame, text="Live Update", variable=self.live_update).pack(anchor=tk.W)
        ttk.Checkbutton(settings_frame, text="Apply Biomechanical Constraints", variable=self.apply_constraints,
                        command=self._on_constraints_toggle).pack(anchor=tk.W)
        
        # Control panel (scrollable)
        control_container = ttk.Frame(right_frame)
        control_container.pack(fill=tk.BOTH, expand=True)
        
        control_canvas = tk.Canvas(control_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(control_container, orient=tk.VERTICAL, command=control_canvas.yview)
        self.controls_frame = ttk.Frame(control_canvas)
        
        control_canvas.create_window((0, 0), window=self.controls_frame, anchor='nw')
        control_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.controls_frame.bind('<Configure>', lambda e: control_canvas.configure(scrollregion=control_canvas.bbox('all')))
        
        control_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Build per-part controls
        self.part_controls = {}
        self._build_part_controls()
        
        # Bottom bar: timeline and global buttons
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # Time slider (if animation exists)
        if self.anim:
            self.time_var = tk.DoubleVar()
            self.time_slider = ttk.Scale(bottom_frame, from_=0, to=self.duration,
                                         orient=tk.HORIZONTAL, variable=self.time_var,
                                         command=self._on_time_slider)
            self.time_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            ttk.Button(bottom_frame, text="◀◀", command=lambda: self._step_frame(-0.1)).pack(side=tk.LEFT)
            ttk.Button(bottom_frame, text="▶", command=self._play).pack(side=tk.LEFT)
            ttk.Button(bottom_frame, text="◀", command=lambda: self._step_frame(-1/30)).pack(side=tk.LEFT)
            ttk.Button(bottom_frame, text="▶▶", command=lambda: self._step_frame(0.1)).pack(side=tk.LEFT)
        
        # Global buttons
        ttk.Button(bottom_frame, text="Reset All", command=self.reset_all).pack(side=tk.RIGHT, padx=5)
        ttk.Button(bottom_frame, text="Save All", command=self.save_all).pack(side=tk.RIGHT, padx=5)
        ttk.Button(bottom_frame, text="Load Pose", command=self.load_pose).pack(side=tk.RIGHT, padx=5)
        ttk.Button(bottom_frame, text="Save Pose", command=self.save_pose).pack(side=tk.RIGHT, padx=5)
        
        # Apply button (if live update is off)
        self.apply_btn = ttk.Button(bottom_frame, text="Apply Changes", command=self.update_canvas)
        self.apply_btn.pack(side=tk.RIGHT, padx=5)
        
        # Update apply button visibility based on live_update
        self.live_update.trace_add('write', self._toggle_apply_btn)
        self._toggle_apply_btn()
    
    def _build_part_controls(self):
        """Create a frame for each part with spinboxes and save/reset buttons."""
        for part_name in self.all_parts:
            frame = ttk.LabelFrame(self.controls_frame, text=part_name)
            frame.pack(fill=tk.X, padx=5, pady=2)
            
            # Row 0: Rotation
            ttk.Label(frame, text="Rot:").grid(row=0, column=0, sticky=tk.W)
            rot_var = tk.DoubleVar()
            spin_rot = ttk.Spinbox(frame, from_=-180, to=180, textvariable=rot_var, width=6)
            spin_rot.grid(row=0, column=1, padx=2)
            ttk.Button(frame, text="+", width=2, command=lambda v=rot_var, step=1: self._adjust_value(v, step)).grid(row=0, column=2)
            ttk.Button(frame, text="-", width=2, command=lambda v=rot_var, step=-1: self._adjust_value(v, step)).grid(row=0, column=3)
            
            # Row 1: Translate X
            ttk.Label(frame, text="Tx:").grid(row=1, column=0, sticky=tk.W)
            tx_var = tk.DoubleVar()
            spin_tx = ttk.Spinbox(frame, from_=-100, to=100, textvariable=tx_var, width=6)
            spin_tx.grid(row=1, column=1, padx=2)
            ttk.Button(frame, text="+", width=2, command=lambda v=tx_var, step=1: self._adjust_value(v, step)).grid(row=1, column=2)
            ttk.Button(frame, text="-", width=2, command=lambda v=tx_var, step=-1: self._adjust_value(v, step)).grid(row=1, column=3)
            
            # Row 2: Translate Y
            ttk.Label(frame, text="Ty:").grid(row=2, column=0, sticky=tk.W)
            ty_var = tk.DoubleVar()
            spin_ty = ttk.Spinbox(frame, from_=-100, to=100, textvariable=ty_var, width=6)
            spin_ty.grid(row=2, column=1, padx=2)
            ttk.Button(frame, text="+", width=2, command=lambda v=ty_var, step=1: self._adjust_value(v, step)).grid(row=2, column=2)
            ttk.Button(frame, text="-", width=2, command=lambda v=ty_var, step=-1: self._adjust_value(v, step)).grid(row=2, column=3)
            
            # Row 3: Save/Reset buttons
            ttk.Button(frame, text="Save", command=lambda p=part_name: self.save_part(p)).grid(row=3, column=0, columnspan=2, sticky=tk.W+tk.E)
            ttk.Button(frame, text="Reset", command=lambda p=part_name: self.reset_part(p)).grid(row=3, column=2, columnspan=2, sticky=tk.W+tk.E)
            
            self.part_controls[part_name] = {
                'rot': rot_var,
                'tx': tx_var,
                'ty': ty_var
            }
            
            # Bind spinbox changes to update override pose
            rot_var.trace_add('write', lambda *args, p=part_name: self._on_part_change(p, 'rotation'))
            tx_var.trace_add('write', lambda *args, p=part_name: self._on_part_change(p, 'translate_x'))
            ty_var.trace_add('write', lambda *args, p=part_name: self._on_part_change(p, 'translate_y'))
    
    def _adjust_value(self, var, delta):
        """Increase or decrease a variable by delta."""
        var.set(var.get() + delta)
    
    def _on_part_change(self, part_name, attr):
        """Called when a spinbox value changes."""
        val = self.part_controls[part_name][attr].get()
        if part_name not in self.override_pose:
            self.override_pose[part_name] = {}
        self.override_pose[part_name][attr] = val
        if self.live_update.get():
            self.update_canvas()
    
    def _on_constraints_toggle(self):
        """Recompute base pose when constraints setting changes."""
        self._update_base_pose()
        self._sync_gui_from_pose()
        self.update_canvas()
    
    def _toggle_apply_btn(self, *args):
        """Hide apply button when live update is on, show when off."""
        if self.live_update.get():
            self.apply_btn.pack_forget()
        else:
            self.apply_btn.pack(side=tk.RIGHT, padx=5)
    
    def _update_base_pose(self):
        """Recompute base pose from keyframes and constraints."""
        if self.keyframes:
            self.base_pose = primeanim_v4a.interpolate_pose(self.keyframes, self.current_time)
        else:
            self.base_pose = {}
        
        if self.apply_constraints.get():
            # Apply biomechanical constraints to the base pose
            self.base_pose = self.constraints.apply_biomechanical_constraints(
                self.base_pose, self.current_time, self.duration, debug=False
            )
    
    def _sync_gui_from_pose(self):
        """Update GUI spinboxes to reflect the current combined pose."""
        combined = self._get_combined_pose()
        for part_name, attrs in combined.items():
            if part_name in self.part_controls:
                self.part_controls[part_name]['rot'].set(attrs.get('rotation', 0))
                self.part_controls[part_name]['tx'].set(attrs.get('translate_x', 0))
                self.part_controls[part_name]['ty'].set(attrs.get('translate_y', 0))
    
    def _get_combined_pose(self):
        """Merge base pose with overrides."""
        combined = {}
        # Start with base pose
        for part_name, attrs in self.base_pose.items():
            combined[part_name] = attrs.copy()
        # Override with user changes
        for part_name, attrs in self.override_pose.items():
            if part_name not in combined:
                combined[part_name] = {}
            combined[part_name].update(attrs)
        return combined
    
    def _on_time_slider(self, value):
        """Time slider moved."""
        self.current_time = float(value)
        self._update_base_pose()
        # After updating base pose, we keep overrides but need to refresh GUI values
        # because some parts may have been changed by constraints.
        # We'll merge and update spinboxes.
        combined = self._get_combined_pose()
        for part_name, attrs in combined.items():
            if part_name in self.part_controls:
                self.part_controls[part_name]['rot'].set(attrs.get('rotation', 0))
                self.part_controls[part_name]['tx'].set(attrs.get('translate_x', 0))
                self.part_controls[part_name]['ty'].set(attrs.get('translate_y', 0))
        self.update_canvas()
    
    def _step_frame(self, delta):
        """Move time by delta seconds."""
        new_time = self.current_time + delta
        new_time = max(0, min(self.duration, new_time))
        self.time_var.set(new_time)
        self._on_time_slider(new_time)
    
    def _play(self):
        """Simple playback (not very smooth, but functional)."""
        def step():
            if self.current_time < self.duration - 0.033:
                self._step_frame(0.033)
                self.root.after(33, step)
            else:
                self._step_frame(0)
        step()
    
    def save_part(self, part_name):
        """Save current values of a part into saved_pose."""
        combined = self._get_combined_pose()
        if part_name in combined:
            self.saved_pose[part_name] = combined[part_name].copy()
        else:
            self.saved_pose[part_name] = {}
        # Optional: feedback
        print(f"Saved pose for {part_name}")
    
    def reset_part(self, part_name):
        """Reset a part to its saved pose (or base if none saved)."""
        if part_name in self.saved_pose and self.saved_pose[part_name]:
            # Restore from saved_pose
            if part_name not in self.override_pose:
                self.override_pose[part_name] = {}
            self.override_pose[part_name].update(self.saved_pose[part_name])
        else:
            # Remove overrides for this part, fall back to base
            if part_name in self.override_pose:
                del self.override_pose[part_name]
        # Update GUI controls
        combined = self._get_combined_pose()
        if part_name in combined:
            self.part_controls[part_name]['rot'].set(combined[part_name].get('rotation', 0))
            self.part_controls[part_name]['tx'].set(combined[part_name].get('translate_x', 0))
            self.part_controls[part_name]['ty'].set(combined[part_name].get('translate_y', 0))
        self.update_canvas()
    
    def reset_all(self):
        """Reset all parts: clear overrides and saved poses."""
        self.override_pose.clear()
        self.saved_pose.clear()
        self._sync_gui_from_pose()  # reload from base
        self.update_canvas()
    
    def save_all(self):
        """Save current combined pose for all parts."""
        combined = self._get_combined_pose()
        for part_name in self.all_parts:
            if part_name in combined:
                self.saved_pose[part_name] = combined[part_name].copy()
            else:
                self.saved_pose[part_name] = {}
        print("Saved all parts")
    
    def save_pose(self):
        """Save current combined pose to a JSON file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".json",
                                                 filetypes=[("JSON files", "*.json")])
        if file_path:
            combined = self._get_combined_pose()
            # Filter out zero values for brevity
            to_save = {}
            for part_name, attrs in combined.items():
                filtered = {k:v for k,v in attrs.items() if v != 0}
                if filtered:
                    to_save[part_name] = filtered
            with open(file_path, 'w') as f:
                json.dump(to_save, f, indent=2)
            messagebox.showinfo("Saved", f"Pose saved to {file_path}")
    
    def load_pose(self):
        """Load a pose JSON file and apply as overrides."""
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path) as f:
                loaded = json.load(f)
            # Merge into override_pose
            for part_name, attrs in loaded.items():
                if part_name not in self.override_pose:
                    self.override_pose[part_name] = {}
                self.override_pose[part_name].update(attrs)
            self._sync_gui_from_pose()
            self.update_canvas()
            messagebox.showinfo("Loaded", f"Pose loaded from {file_path}")
    
    def update_canvas(self):
        """Render the character on the canvas using the current combined pose."""
        # Clear canvas
        self.canvas.delete("all")
        # Create PIL image
        img = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
        combined = self._get_combined_pose()
        # Use render_with_layers (needs rig, pose, image, center x, center y)
        primeanim_v4a.render_with_layers(self.rig, combined, img, 256, 256, render_order=self.rig.get('render_order'))
        # Convert to PhotoImage and display
        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, image=self.tk_img, anchor='nw')
        self.canvas.update_idletasks()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Interactive Pose Editor")
    parser.add_argument('--rig', required=True, help="Path to rig JSON")
    parser.add_argument('--anim', help="Path to animation JSON (optional)")
    parser.add_argument('--preset', default="human_balanced", help="Locomotion preset")
    args = parser.parse_args()
    
    root = tk.Tk()
    app = PoseEditor(root, args.rig, args.anim, args.preset)
    root.mainloop()

if __name__ == "__main__":
    main()
