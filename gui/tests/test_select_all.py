import unittest
import tkinter as tk
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.zw_gui import ZWEditorGUI
from unittest.mock import patch

class TestSelectAll(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
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

    def test_select_all(self):
        self.app.zw_editor.insert("1.0", "Hello World")
        # Ensure no selection initially
        self.app.zw_editor.tag_remove(tk.SEL, "1.0", tk.END)
        self.assertEqual(len(self.app.zw_editor.tag_ranges(tk.SEL)), 0)

        # Focus on zw_editor and call method to simulate shortcut
        # Use explicit widget param because headless tests struggle with focus_get()
        self.app.zw_editor.focus_set()
        self.app.select_all(widget=self.app.zw_editor)

        # Verify selection range has start and end indices
        self.assertEqual(len(self.app.zw_editor.tag_ranges(tk.SEL)), 2)

if __name__ == '__main__':
    unittest.main()
