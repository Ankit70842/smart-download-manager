from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import sqlite3

from organizer.core import scan
from organizer.history import History


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.folder = self.root / "downloads"
        self.folder.mkdir()
        self.history = History(self.root / "history.sqlite")

    def tearDown(self):
        self.history.close()
        self.temp.cleanup()

    def test_round_trip(self):
        original = {"a.txt": b"hello", "b.JPG": b"image", "LICENSE": b"license"}
        for name, content in original.items():
            (self.folder / name).write_bytes(content)
        self.history.apply(scan(self.folder))
        self.assertTrue(all(r["state"] == "moved" for r in self.history.rows()))
        self.history.undo_latest()
        for name, content in original.items():
            self.assertEqual((self.folder / name).read_bytes(), content)
        self.assertTrue(all(r["state"] == "undone" for r in self.history.rows()))

    def test_collision_preserves_both_files(self):
        (self.folder / "a.txt").write_text("new")
        (self.folder / "Documents").mkdir()
        destination = self.folder / "Documents" / "a.txt"
        destination.write_text("existing")
        self.history.apply(scan(self.folder))
        self.history.reconcile()
        self.assertEqual(destination.read_text(), "existing")
        self.assertEqual((self.folder / "a.txt").read_text(), "new")
        self.assertEqual(self.history.rows()[0]["state"], "review")

    def test_undo_refuses_changed_file_and_occupied_path(self):
        (self.folder / "a.txt").write_text("original")
        self.history.apply(scan(self.folder))
        destination = self.folder / "Documents" / "a.txt"
        destination.write_text("edited")
        self.history.undo_latest()
        self.assertFalse((self.folder / "a.txt").exists())
        destination.write_text("original")
        (self.folder / "a.txt").write_text("occupied")
        self.history.undo_latest()
        self.assertEqual((self.folder / "a.txt").read_text(), "occupied")
        self.assertTrue(destination.exists())

    def test_missing_source_does_not_stop_other_moves(self):
        for name in ["a.txt", "b.txt"]:
            (self.folder / name).write_text(name)
        plan = scan(self.folder)
        plan[0].source.unlink()
        self.history.apply(plan)
        self.assertEqual({r["state"] for r in self.history.rows()}, {"failed", "moved"})

    def test_interrupted_move_reconciles(self):
        (self.folder / "a.txt").write_text("original")
        real_update = self.history.update
        with patch.object(self.history, "update", side_effect=RuntimeError("crash")):
            with self.assertRaises(RuntimeError):
                self.history.apply(scan(self.folder))
        self.history.update = real_update
        self.history.reconcile()
        self.assertEqual(self.history.rows()[0]["state"], "moved")
        self.history.undo_latest()
        self.assertTrue((self.folder / "a.txt").exists())

    def test_sessions_cannot_move_concurrently(self):
        lock = sqlite3.connect(self.history.lock_path)
        try:
            lock.execute("BEGIN IMMEDIATE")
            with self.assertRaises(sqlite3.OperationalError):
                self.history.apply([])
        finally:
            lock.close()

    def test_category_link_is_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        try:
            (self.folder / "Documents").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("Creating symlinks is unavailable for this account")
        (self.folder / "a.txt").write_text("original")
        self.history.apply(scan(self.folder))
        self.assertTrue((self.folder / "a.txt").exists())
        self.assertEqual(list(outside.iterdir()), [])

    def test_unlink_failure_preserves_both_names_for_review(self):
        (self.folder / "a.txt").write_text("original")
        with patch.object(Path, "unlink", side_effect=PermissionError("locked")):
            self.history.apply(scan(self.folder))
        self.history.reconcile()
        self.assertTrue((self.folder / "a.txt").exists())
        self.assertTrue((self.folder / "Documents" / "a.txt").exists())
        self.assertEqual(self.history.rows()[0]["state"], "review")
