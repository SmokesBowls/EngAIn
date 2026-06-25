import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch
import sys
import os

# Add repo root to path so we can import gui.zw_gui
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from gui.zw_gui import ZWEditorGUI

class TestZWEditorGUI(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        # Mock file dialogs and messagebox
        self.patcher_askopen = patch('tkinter.filedialog.askopenfilename')
        self.mock_askopen = self.patcher_askopen.start()

        self.patcher_asksave = patch('tkinter.filedialog.asksaveasfilename')
        self.mock_asksave = self.patcher_asksave.start()

        self.patcher_msg = patch('tkinter.messagebox.askyesno')
        self.mock_askyesno = self.patcher_msg.start()

        # Prevent actual file I/O
        self.patcher_open = patch('builtins.open', new_callable=unittest.mock.mock_open)
        self.mock_open = self.patcher_open.start()

        self.app = ZWEditorGUI(self.root)

    def tearDown(self):
        self.patcher_askopen.stop()
        self.patcher_asksave.stop()
        self.patcher_msg.stop()
        self.patcher_open.stop()
        self.root.destroy()

    def test_unsaved_changes_indicator(self):
        """Test that * appears when modified"""
        self.app.current_file = "test.zw"
        self.app.original_content = "original"
        self.app.current_file = "test.zw"
        self.app.zw_editor.insert("1.0", "original")

        self.app.current_file = "test.zw"
        # Trigger check
        self.app.check_changes()
        title = self.root.title()
        label_text = self.app.file_label.cget("text")
        self.assertNotIn("*", title)
        self.assertNotIn("*", self.app.file_label.cget("text"))

        # Modify
        self.app.zw_editor.insert("end", " modified")
        self.app.check_changes()
        title = self.root.title()
        label_text = self.app.file_label.cget("text")
        self.assertIn("*", title)
        self.assertIn("*", self.app.file_label.cget("text"))

        # Undo (simulate save/revert)
        self.app.original_content = self.app.zw_editor.get("1.0", "end-1c")
        self.app.check_changes()
        title = self.root.title()
        label_text = self.app.file_label.cget("text")
        self.assertNotIn("*", title)
        self.assertNotIn("*", self.app.file_label.cget("text"))

    def test_confirm_discard_on_new_file(self):
        """Test confirm discard logic"""
        self.app.original_content = "clean"
        self.app.zw_editor.insert("1.0", "clean")

        # No changes
        self.assertTrue(self.app.confirm_discard())
        self.mock_askyesno.assert_not_called()

        # Changes
        self.app.zw_editor.insert("end", " dirty")

        # User says NO to discard
        self.mock_askyesno.return_value = False
        self.assertFalse(self.app.confirm_discard())

        # User says YES to discard
        self.mock_askyesno.return_value = True
        self.assertTrue(self.app.confirm_discard())

    def test_save_updates_original_content(self):
        """Test saving updates the dirty tracking baseline"""
        self.app.current_file = "test.zw"
        self.app.zw_editor.insert("1.0", "content")

        # Save
        self.app.save_file()

        self.assertEqual(self.app.original_content, "content")
        self.mock_open.assert_called_with("test.zw", "w")
        handle = self.mock_open()
        handle.write.assert_called_with("content")

    def test_cursor_position_updates(self):
        """Test the cursor position updates properly"""
        self.app.zw_editor.insert("1.0", "Line 1\nLine 2\nLine 3")

        # Test default initial position
        self.app.zw_editor.mark_set(tk.INSERT, "1.0")
        self.app.update_cursor_info()
        self.assertEqual(self.app.cursor_label.cget("text"), "Ln 1, Col 0")

        # Move cursor to another line and test
        self.app.zw_editor.mark_set(tk.INSERT, "2.4")
        self.app.update_cursor_info()
        self.assertEqual(self.app.cursor_label.cget("text"), "Ln 2, Col 4")

    def test_toolbar_buttons_active_colors(self):
        """Test that toolbar buttons have proper activebackground and activeforeground for dark theme"""
        buttons = []
        for child in self.app.root.winfo_children():
            if isinstance(child, tk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Button):
                        buttons.append(subchild)

        self.assertTrue(len(buttons) >= 4, "Should have at least 4 toolbar buttons")

        for btn in buttons:
            self.assertEqual(btn.cget("activebackground"), "#4c5052")
            self.assertEqual(btn.cget("activeforeground"), "white")

    def test_select_all(self):
        """Test the select all functionality and bindings"""
        self.app.zw_editor.insert("1.0", "Test text")

        # Test explicit method
        self.app.select_all(widget=self.app.zw_editor)
        sel_range = self.app.zw_editor.tag_ranges(tk.SEL)
        self.assertTrue(len(sel_range) > 0)

        # Test bindings exist
        bindings = self.app.zw_editor.bind()
        self.assertTrue(any('Control-Key-a' in b or 'Control-Key-A' in b for b in bindings))

        # Process events to let .after run
        self.app.root.update()
        # Wait for at least 100ms to allow .after callbacks to execute
        self.app.root.after(150, self.app.root.quit)
        self.app.root.mainloop()

        # Test disabled widgets temporarily normal
        self.app.parse_output.config(state=tk.NORMAL)
        self.app.parse_output.insert("1.0", "Output text")
        self.app.parse_output.config(state=tk.DISABLED)

        self.app.select_all(widget=self.app.parse_output)
        sel_range = self.app.parse_output.tag_ranges(tk.SEL)
        self.assertTrue(len(sel_range) > 0)

        bindings = self.app.parse_output.bind()
        self.assertTrue(any('Control-Key-a' in b or 'Control-Key-A' in b for b in bindings))

if __name__ == '__main__':
    unittest.main()
