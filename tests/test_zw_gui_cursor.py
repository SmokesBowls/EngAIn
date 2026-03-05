import unittest
import tkinter as tk
from unittest.mock import MagicMock
import sys
import os

# Add project root to sys.path so we can import gui.zw_gui
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from gui.zw_gui import ZWEditorGUI

class TestZWEditorGUI(unittest.TestCase):
    def setUp(self):
        # Create a root window but hide it
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = ZWEditorGUI(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_cursor_update(self):
        """Test that the cursor label updates correctly when text is inserted."""
        # Simulate inserting text
        self.app.zw_editor.insert("1.0", "Hello\nWorld")

        # Move cursor to end of first line (Hello is 5 chars, so index 1.5)
        self.app.zw_editor.mark_set("insert", "1.5")

        # Trigger the update manually since we can't easily simulate key/mouse events in headless
        self.app.update_cursor_info()

        # Check label text
        # Note: tkinter text indices are 1-based for lines and 0-based for columns.
        # "1.5" means Line 1, Column 5.
        expected_text = "Ln 1, Col 5"
        self.assertEqual(self.app.cursor_label.cget("text"), expected_text)

    def test_cursor_update_multiline(self):
        """Test cursor position on a second line."""
        self.app.zw_editor.insert("1.0", "Line 1\nLine 2")
        self.app.zw_editor.mark_set("insert", "2.3") # Line 2, Column 3

        self.app.update_cursor_info()

        expected_text = "Ln 2, Col 3"
        self.assertEqual(self.app.cursor_label.cget("text"), expected_text)

if __name__ == '__main__':
    unittest.main()
