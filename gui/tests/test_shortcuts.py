import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch
import sys
import os
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from gui.zw_gui import ZWEditorGUI

class TestZWEditorGUIShortcuts(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.patcher_askopen = patch('tkinter.filedialog.askopenfilename')
        self.patcher_asksave = patch('tkinter.filedialog.asksaveasfilename')
        self.patcher_msg = patch('tkinter.messagebox.askyesno')
        self.patcher_open = patch('builtins.open', new_callable=unittest.mock.mock_open)

        self.mock_askopen = self.patcher_askopen.start()
        self.mock_asksave = self.patcher_asksave.start()
        self.mock_askyesno = self.patcher_msg.start()
        self.mock_open = self.patcher_open.start()

        self.app = ZWEditorGUI(self.root)

    def tearDown(self):
        self.patcher_askopen.stop()
        self.patcher_asksave.stop()
        self.patcher_msg.stop()
        self.patcher_open.stop()
        self.root.destroy()

    def test_f5_f6_bindings(self):
        bindings = self.app.root.bind()
        self.assertTrue(any('F5' in b for b in bindings), "F5 should be bound")
        self.assertTrue(any('F6' in b for b in bindings), "F6 should be bound")

        # Test headless execution of F5
        with patch.object(self.app, 'parse_content') as mock_parse:
            bind_script = self.app.root.bind('<F5>')
            cmd_name = re.search(r'\[(.*?) ', bind_script)
            if not cmd_name:
                cmd_name = re.search(r'if {\[catch {(.*?) ', bind_script)
            self.assertIsNotNone(cmd_name)
            self.app.root.tk.call(cmd_name.group(1))
            mock_parse.assert_called_once()

        # Test headless execution of F6
        with patch.object(self.app, 'validate_content') as mock_valid:
            bind_script = self.app.root.bind('<F6>')
            cmd_name = re.search(r'\[(.*?) ', bind_script)
            if not cmd_name:
                cmd_name = re.search(r'if {\[catch {(.*?) ', bind_script)
            self.assertIsNotNone(cmd_name)
            self.app.root.tk.call(cmd_name.group(1))
            mock_valid.assert_called_once()

if __name__ == '__main__':
    unittest.main()
