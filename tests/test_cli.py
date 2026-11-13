"""Exercise actual command-line processes against disposable files."""

from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys
import unittest


class CliTests(unittest.TestCase):
    def test_preview_and_cancel_do_not_move_files(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "notes.txt"
            source.write_text("sample")
            preview = subprocess.run([sys.executable, "-m", "organizer", directory],
                                     text=True, capture_output=True)
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertIn("1 eligible files", preview.stdout)
            self.assertTrue(source.exists())
            cancel = subprocess.run([sys.executable, "-m", "organizer", directory, "--apply"],
                                    input="no\n", text=True, capture_output=True)
            self.assertEqual(cancel.returncode, 0, cancel.stderr)
            self.assertIn("Cancelled", cancel.stdout)
            self.assertTrue(source.exists())
