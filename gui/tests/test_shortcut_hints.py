import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from gui.zw_gui import ZWEditorGUI

class TestShortcutHints(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.app = ZWEditorGUI(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_toolbar_button_text(self):
        buttons = []
        for child in self.app.root.winfo_children():
            if isinstance(child, tk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Button):
                        buttons.append(subchild.cget("text"))

        self.assertIn("📂 Open (Ctrl+O)", buttons)
        self.assertIn("💾 Save (Ctrl+S)", buttons)
        self.assertIn("🔍 Parse (F5)", buttons)
        self.assertIn("✓ Validate (F6)", buttons)

if __name__ == '__main__':
    unittest.main()
