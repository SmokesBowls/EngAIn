import unittest
import tkinter as tk
from unittest.mock import patch, MagicMock
import sys
import os

# Add repo root to path so we can import gui.zw_gui
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from gui.zw_gui import ZWEditorGUI

class TestSelectAll(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()

        # Mock dialogs and file io to prevent UI freezing or errors
        self.patcher_askopen = patch('tkinter.filedialog.askopenfilename')
        self.mock_askopen = self.patcher_askopen.start()
        self.patcher_asksave = patch('tkinter.filedialog.asksaveasfilename')
        self.mock_asksave = self.patcher_asksave.start()
        self.patcher_msg = patch('tkinter.messagebox.askyesno')
        self.mock_askyesno = self.patcher_msg.start()
        self.patcher_open = patch('builtins.open', new_callable=unittest.mock.mock_open)
        self.mock_open = self.patcher_open.start()

        self.app = ZWEditorGUI(self.root)

    def tearDown(self):
        self.patcher_askopen.stop()
        self.patcher_asksave.stop()
        self.patcher_msg.stop()
        self.patcher_open.stop()
        self.root.destroy()

    def test_select_all_editable(self):
        """Test select all works on the editable ZW editor"""
        self.app.zw_editor.insert("1.0", "Line 1\nLine 2\nLine 3")

        # Simulate Ctrl+A event
        event = MagicMock()
        event.widget = self.app.zw_editor
        result = self.app._select_all(event)

        # Check that it returns "break"
        self.assertEqual(result, "break")

        # Check that tk.SEL tag covers all text
        sel_ranges = self.app.zw_editor.tag_ranges(tk.SEL)
        self.assertTrue(len(sel_ranges) >= 2)

        # Start should be 1.0
        self.assertEqual(str(sel_ranges[0]), "1.0")

    def test_select_all_disabled_widgets(self):
        """Test select all works on output panels even if disabled"""
        # Parse output
        self.app.parse_output.config(state=tk.NORMAL)
        self.app.parse_output.insert("1.0", "Parse Output Text")
        self.app.parse_output.config(state=tk.DISABLED)

        event = MagicMock()
        event.widget = self.app.parse_output
        self.app._select_all(event)

        sel_ranges = self.app.parse_output.tag_ranges(tk.SEL)
        self.assertTrue(len(sel_ranges) >= 2)
        self.assertEqual(str(sel_ranges[0]), "1.0")

        # Valid output
        self.app.valid_output.config(state=tk.NORMAL)
        self.app.valid_output.insert("1.0", "Valid Output Text")
        self.app.valid_output.config(state=tk.DISABLED)

        event.widget = self.app.valid_output
        self.app._select_all(event)

        sel_ranges = self.app.valid_output.tag_ranges(tk.SEL)
        self.assertTrue(len(sel_ranges) >= 2)
        self.assertEqual(str(sel_ranges[0]), "1.0")

if __name__ == '__main__':
    unittest.main()
