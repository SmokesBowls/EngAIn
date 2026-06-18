import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from gui.zw_gui import ZWEditorGUI

class TestSelectAll(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.patcher_askopen = patch('tkinter.filedialog.askopenfilename')
        self.mock_askopen = self.patcher_askopen.start()
        self.app = ZWEditorGUI(self.root)

    def tearDown(self):
        self.patcher_askopen.stop()
        self.root.destroy()

    def test_select_all_method(self):
        """Test the select_all method applies selection tags correctly"""
        # Insert some text
        self.app.zw_editor.insert("1.0", "Hello\nWorld")

        # Verify no selection initially
        self.assertEqual(len(self.app.zw_editor.tag_ranges(tk.SEL)), 0)

        # Call select_all explicitly
        result = self.app.select_all(widget=self.app.zw_editor)

        # Verify it returns "break"
        self.assertEqual(result, "break")

        # Verify selection is applied (should have start and end indices)
        ranges = self.app.zw_editor.tag_ranges(tk.SEL)
        self.assertEqual(len(ranges), 2)

        # The start should be 1.0, and the end should be the end of the text
        self.assertEqual(str(ranges[0]), "1.0")

if __name__ == '__main__':
    unittest.main()
