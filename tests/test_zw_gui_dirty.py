import unittest
import tkinter as tk
from unittest.mock import MagicMock
import sys
import os

# Add project root to sys.path so we can import gui.zw_gui
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from gui.zw_gui import ZWEditorGUI

class TestZWEditorGUI_DirtyState(unittest.TestCase):
    def setUp(self):
        # Create a root window but hide it
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = ZWEditorGUI(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_dirty_state_no_file(self):
        """Test the file label without a file loaded."""
        # Initial state should be clean
        self.assertEqual(self.app.file_label.cget("text"), "No file loaded")

        # Simulate typing
        self.app.zw_editor.insert("1.0", "New content")
        self.app.check_changes()

        # Should now be dirty
        self.assertEqual(self.app.file_label.cget("text"), "No file loaded *")

    def test_dirty_state_with_file(self):
        """Test the file label with a file loaded."""
        # Set file state manually to simulate loaded file
        self.app.current_file = "/fake/path/test_file.zw"
        self.app.original_content = "Initial content"
        self.app.zw_editor.insert("1.0", "Initial content")
        self.app.check_changes()

        # Should be clean
        self.assertEqual(self.app.file_label.cget("text"), "test_file.zw")

        # Simulate typing to make it dirty
        self.app.zw_editor.insert("end", " more text")
        self.app.check_changes()

        # Should now be dirty
        self.assertEqual(self.app.file_label.cget("text"), "test_file.zw *")

if __name__ == '__main__':
    unittest.main()
