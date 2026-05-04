import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from gui.zw_gui import ZWEditorGUI

class TestNotebookTabSwitch(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.app = ZWEditorGUI(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_notebook_exists(self):
        self.assertTrue(hasattr(self.app, 'notebook'), "Notebook should be saved to self")

    def test_auto_switch_parse_validate(self):
        # Set to validation tab initially
        self.app.notebook.select(self.app.valid_frame)
        self.assertEqual(self.app.notebook.tab(self.app.notebook.select(), "text"), "Validation")

        # Trigger parse and check if it switched
        self.app.parse_content()
        self.assertEqual(self.app.notebook.tab(self.app.notebook.select(), "text"), "Parsed")

        # Trigger validate and check if it switched
        self.app.validate_content()
        self.assertEqual(self.app.notebook.tab(self.app.notebook.select(), "text"), "Validation")


if __name__ == '__main__':
    unittest.main()
