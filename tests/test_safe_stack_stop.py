"""Targeted real-process safety gates for the stack stop helper."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HELPER = Path(__file__).resolve().parents[1] / 'tools/stop_stack_safe.py'


class SafeStopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / '.run').mkdir()
        self.children = []

    def tearDown(self):
        for child in self.children:
            if child.poll() is None:
                child.terminate()
            child.wait(timeout=5)
        self.tmp.cleanup()

    def run_stop(self):
        return subprocess.run([sys.executable, str(HELPER), '--root', str(self.root)],
                              capture_output=True, text=True, timeout=20)

    def pidfile(self, value):
        path = self.root / '.run/sim_runtime.pid'
        path.write_text(value)
        return path

    def test_no_pidfiles_is_safe(self):
        result = self.run_stop()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_malformed_pid_is_retained(self):
        path = self.pidfile('0\n')
        result = self.run_stop()
        self.assertEqual(result.returncode, 1)
        self.assertTrue(path.exists())
        self.assertIn('REFUSE', result.stdout)

    def test_unrelated_live_process_is_not_signalled(self):
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], cwd=self.root)
        self.children.append(child)
        path = self.pidfile(str(child.pid))
        result = self.run_stop()
        self.assertEqual(result.returncode, 1)
        self.assertIsNone(child.poll())
        self.assertTrue(path.exists())
        self.assertIn('REFUSE', result.stdout)

    def test_symlink_pidfile_is_refused(self):
        target = self.root / 'target'
        target.write_text('0')
        (self.root / '.run/sim_runtime.pid').symlink_to(target)
        result = self.run_stop()
        self.assertEqual(result.returncode, 1)
        self.assertIn('REFUSE', result.stdout)
        self.assertEqual(target.read_text(), '0')

    def test_dead_process_pidfile_is_removed_without_signal(self):
        child = subprocess.Popen([sys.executable, '-c', 'pass'])
        child.wait(timeout=5)
        path = self.pidfile(str(child.pid))
        result = self.run_stop()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(path.exists())
        self.assertIn('[STALE]', result.stdout)

    def owned_child(self, cwd):
        package = Path(cwd) / 'tier2/godotsim'
        package.mkdir(parents=True)
        (package / 'sim_runtime.py').write_text('import time\ntime.sleep(60)\n')
        child = subprocess.Popen([sys.executable, '-u', '-m', 'tier2.godotsim.sim_runtime'], cwd=cwd)
        self.children.append(child)
        return child

    def test_matching_command_wrong_checkout_is_refused(self):
        other = self.root / 'other'
        child = self.owned_child(other)
        path = self.pidfile(str(child.pid))
        result = self.run_stop()
        self.assertEqual(result.returncode, 1)
        self.assertIsNone(child.poll())
        self.assertTrue(path.exists())

    def test_exact_owned_process_stops_and_pidfile_is_removed(self):
        child = self.owned_child(self.root)
        path = self.pidfile(str(child.pid))
        result = self.run_stop()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        child.wait(timeout=5)
        self.assertFalse(path.exists())
        self.assertIn('[STOP]', result.stdout)


if __name__ == '__main__':
    unittest.main()
