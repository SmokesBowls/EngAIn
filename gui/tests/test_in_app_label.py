import unittest
import tkinter as tk
from unittest.mock import patch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from gui.zw_gui import ZWEditorGUI

class TestInAppLabelDirtyState(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.app = ZWEditorGUI(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_in_app_label_dirty_no_file(self):
        self.app.original_content = "original"
        self.app.zw_editor.insert("1.0", "original")

        # clean state
        self.app.check_changes()
        self.assertEqual(self.app.file_label.cget("text"), "No file loaded")

        # modify
        self.app.zw_editor.insert("end", " modified")
        self.app.check_changes()
        self.assertEqual(self.app.file_label.cget("text"), "Unsaved file *")

    def test_in_app_label_dirty_with_file(self):
        self.app.original_content = "original"
        self.app.zw_editor.insert("1.0", "original")
        self.app.current_file = "/some/path/my_file.zw"

        # clean state
        self.app.check_changes()
        self.assertEqual(self.app.file_label.cget("text"), "my_file.zw")

        # modify
        self.app.zw_editor.insert("end", " modified")
        self.app.check_changes()
        self.assertEqual(self.app.file_label.cget("text"), "my_file.zw *")

if __name__ == '__main__':
    unittest.main()