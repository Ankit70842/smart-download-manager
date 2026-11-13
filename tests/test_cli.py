"""Exercise actual command-line processes against disposable files."""

from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys
import unittest


class CliTests(unittest.TestCase):
    def test_apply_and_undo_use_an_isolated_history_database(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            downloads = root / "downloads"
            downloads.mkdir()
            source = downloads / "notes.txt"
            source.write_text("original")
            command = [sys.executable, "-m", "organizer", "--database", str(root / "history.sqlite")]
            apply = subprocess.run(command + [str(downloads), "--apply"], input="APPLY\n",
                                   text=True, capture_output=True, timeout=10)
            self.assertEqual(apply.returncode, 0, apply.stderr)
            self.assertFalse(source.exists())
            undo = subprocess.run(command + ["--undo"], text=True, capture_output=True, timeout=10)
            self.assertEqual(undo.returncode, 0, undo.stderr)
            self.assertEqual(source.read_text(), "original")
            self.assertIn("undone:", undo.stdout)

    def test_preview_and_cancel_do_not_move_files(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "notes.txt"
            source.write_text("sample")
            command = [sys.executable, "-m", "organizer", "--database",
                       str(Path(directory) / ".history" / "test.sqlite"), directory]
            preview = subprocess.run(command, text=True, capture_output=True, timeout=10)
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertIn("1 eligible files", preview.stdout)
            self.assertTrue(source.exists())
            cancel = subprocess.run(command + ["--apply"],
                                    input="no\n", text=True, capture_output=True, timeout=10)
            self.assertEqual(cancel.returncode, 0, cancel.stderr)
            self.assertIn("Cancelled", cancel.stdout)
            self.assertTrue(source.exists())
