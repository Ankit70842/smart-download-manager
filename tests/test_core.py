from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from organizer.core import scan


class ScanTests(unittest.TestCase):
    def test_categories_and_skipped_entries(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ["PHOTO.JPG", "notes.txt", "unknown.xyz", "LICENSE", ".hidden"]:
                (root / name).write_text("sample")
            (root / "nested").mkdir()
            result = {m.source.name: m.destination.parent.name for m in scan(root)}
            self.assertEqual(result, {"PHOTO.JPG": "Images", "notes.txt": "Documents",
                                      "unknown.xyz": "Other", "LICENSE": "Other"})
            self.assertTrue((root / "notes.txt").exists())

    def test_empty_and_invalid_folder(self):
        with TemporaryDirectory() as directory:
            self.assertEqual(scan(directory), [])
            with self.assertRaises(FileNotFoundError):
                scan(Path(directory) / "missing")
