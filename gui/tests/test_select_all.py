import unittest
import tkinter as tk
from unittest.mock import patch
import sys
import os
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gui.zw_gui import ZWEditorGUI

class TestSelectAll(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.patcher_askopen = patch('tkinter.filedialog.askopenfilename')
        self.patcher_askopen.start()
        self.patcher_asksave = patch('tkinter.filedialog.asksaveasfilename')
        self.patcher_asksave.start()
        self.patcher_msg = patch('tkinter.messagebox.askyesno')
        self.patcher_msg.start()
        self.patcher_open = patch('builtins.open', new_callable=unittest.mock.mock_open)
        self.patcher_open.start()
        self.app = ZWEditorGUI(self.root)

    def tearDown(self):
        patch.stopall()
        self.root.destroy()

    def test_select_all_enabled_widget(self):
        self.app.zw_editor.insert("1.0", "Hello World")

        bind_str = self.app.zw_editor.bind('<Control-a>')
        self.assertTrue(bool(bind_str))
        cmd = re.search(r'\[(.*?) ', bind_str).group(1)
        self.root.tk.call(cmd)

        self.assertEqual(len(self.app.zw_editor.tag_ranges(tk.SEL)), 2)

    def test_select_all_disabled_widget(self):
        self.app.parse_output.config(state=tk.NORMAL)
        self.app.parse_output.insert("1.0", "Output Text")
        self.app.parse_output.config(state=tk.DISABLED)

        bind_str = self.app.parse_output.bind('<Control-a>')
        self.assertTrue(bool(bind_str))
        cmd = re.search(r'\[(.*?) ', bind_str).group(1)
        self.root.tk.call(cmd)

        self.assertEqual(len(self.app.parse_output.tag_ranges(tk.SEL)), 2)

if __name__ == '__main__':
    unittest.main()
