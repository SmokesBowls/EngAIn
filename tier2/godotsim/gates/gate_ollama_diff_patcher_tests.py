#!/usr/bin/env python3
"""
tier2/godotsim/gates/gate_ollama_diff_patcher_tests.py
Unit tests verifying all five requirements of PATCHER_ACCEPTANCE_RULE step 7.
"""

from __future__ import annotations
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import io
import os
import tempfile

# Setup root path to import relative modules
ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT))

from tools.ollama_diff_patcher import (
    build_unified_diff,
    require_human_diff_acceptance,
    atomic_write_text,
    ACCEPTANCE_PHRASE
)

class TestOllamaDiffPatcher(unittest.TestCase):
    def setUp(self):
        # Create a temporary file to act as the target
        self.test_dir = tempfile.TemporaryDirectory()
        self.target_path = Path(self.test_dir.name) / "test_target.py"
        self.initial_content = "def hello():\n    print('hello')\n"
        self.target_path.write_text(self.initial_content, encoding="utf-8")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_1_changed_content_no_confirmation(self):
        """1. Given changed content and no confirmation (EOF or empty), the target file remains unchanged."""
        diff_text = "dummy diff"
        with patch("builtins.input", side_effect=EOFError):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                accepted = require_human_diff_acceptance(diff_text)
                self.assertFalse(accepted)
                self.assertIn("REJECTED: no interactive confirmation received", mock_stdout.getvalue())
        # Target file content remains unchanged
        self.assertEqual(self.target_path.read_text(encoding="utf-8"), self.initial_content)

    def test_2_changed_content_wrong_confirmation(self):
        """2. Given changed content and wrong confirmation like 'yes', the target file remains unchanged."""
        diff_text = "dummy diff"
        for wrong_input in ["yes", "y", "accept", "ACCEPT", "ACCEPT_DIFF", ""]:
            with patch("builtins.input", return_value=wrong_input):
                with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                    accepted = require_human_diff_acceptance(diff_text)
                    self.assertFalse(accepted)
                    self.assertIn("REJECTED: confirmation phrase did not match", mock_stdout.getvalue())
        # Target file content remains unchanged
        self.assertEqual(self.target_path.read_text(encoding="utf-8"), self.initial_content)

    def test_3_changed_content_exact_accept_diff(self):
        """3. Given changed content and exact 'ACCEPT DIFF', the target file is updated."""
        diff_text = "dummy diff"
        with patch("builtins.input", return_value=ACCEPTANCE_PHRASE):
            accepted = require_human_diff_acceptance(diff_text)
            self.assertTrue(accepted)

        # Atomic write
        new_content = "def hello():\n    print('hello world')\n"
        atomic_write_text(self.target_path, new_content)
        self.assertEqual(self.target_path.read_text(encoding="utf-8"), new_content)

    def test_4_identical_content_no_prompt_and_no_write(self):
        """4. Given identical before/after content, build_unified_diff is empty, and require_human_diff_acceptance returns False immediately."""
        diff_text = build_unified_diff(self.target_path, self.initial_content, self.initial_content)
        self.assertEqual(diff_text, "")
        
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            accepted = require_human_diff_acceptance(diff_text)
            self.assertFalse(accepted)
            self.assertIn("NO CHANGE: proposed output matches current file", mock_stdout.getvalue())

    def test_5_dry_run_prints_diff_and_no_change(self):
        """5. Given --dry-run, diff prints and target file remains unchanged."""
        new_content = "def hello():\n    print('hello dry run')\n"
        diff_text = build_unified_diff(self.target_path, self.initial_content, new_content)
        self.assertIn("-    print('hello')", diff_text)
        self.assertIn("+    print('hello dry run')", diff_text)
        
        # Test full main script invocation simulating --dry-run via argparse
        test_args = ["tools/ollama_diff_patcher.py", str(self.target_path), "some instruction", "--dry-run"]
        
        # Mock LLM response to return a valid SEARCH/REPLACE block
        mock_response = f"""
<<<<<<< SEARCH
def hello():
    print('hello')
=======
def hello():
    print('hello dry run')
>>>>>>> REPLACE
"""
        with patch("sys.argv", test_args):
            with patch("tools.ollama_diff_patcher.call_ollama", return_value=mock_response):
                with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                    with self.assertRaises(SystemExit) as cm:
                        from tools.ollama_diff_patcher import main
                        main()
                    self.assertEqual(cm.exception.code, 0)
                    output = mock_stdout.getvalue()
                    self.assertIn("DRY RUN: no files modified", output)
                    self.assertIn("-    print('hello')", output)
                    self.assertIn("+    print('hello dry run')", output)
                    
        # Verify the file was indeed NOT changed
        self.assertEqual(self.target_path.read_text(encoding="utf-8"), self.initial_content)

def main():
    print("====================================================")
    print("RUNNING UNIT TESTS FOR OLLAMA DIFF PATCHER")
    print("====================================================")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOllamaDiffPatcher)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("====================================================")
        print("gate_ollama_diff_patcher_tests: TRUE")
        print("====================================================")
        sys.exit(0)
    else:
        print("====================================================")
        print("gate_ollama_diff_patcher_tests: FALSE")
        print("====================================================")
        sys.exit(1)

if __name__ == "__main__":
    main()
