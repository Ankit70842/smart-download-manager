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

    def test_apply_skips_a_file_replaced_after_preview(self):
        source = self.folder / "a.txt"
        source.write_text("reviewed contents")
        plan = scan(self.folder)
        source.unlink()
        source.write_text("different contents after preview")
        self.history.apply(plan)
        self.assertEqual(source.read_text(), "different contents after preview")
        self.assertFalse((self.folder / "Documents" / "a.txt").exists())
        self.assertEqual(self.history.rows()[0]["state"], "failed")

    def test_collision_preserves_both_files(self):
        (self.folder / "a.txt").write_text("new")
        (self.folder / "Documents").mkdir()
        destination = self.folder / "Documents" / "a.txt"
        destination.write_text("existing")
        self.history.apply(scan(self.folder))
        self.history.reconcile()
        self.assertEqual(destination.read_text(), "existing")
        self.assertEqual((self.folder / "a.txt").read_text(), "new")
        self.assertEqual(self.history.rows()[0]["state"], "failed")

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

    def test_denied_category_creation_identifies_operation_and_preserves_source(self):
        source = self.folder / "a.txt"
        source.write_text("original")
        plan = scan(self.folder)
        denied = PermissionError(13, "Access is denied", str(self.folder / "Documents"))
        with patch.object(Path, "mkdir", side_effect=denied):
            self.history.apply(plan)
        self.history.reconcile()
        row = self.history.rows()[0]
        self.assertEqual(row["state"], "failed")
        self.assertEqual(source.read_text(), "original")
        self.assertFalse((self.folder / "Documents" / "a.txt").exists())
        self.assertIn("Create category folder", row["error"])
        self.assertIn(str(self.folder / "Documents"), row["error"])

    def test_interrupted_move_reconciles(self):
        (self.folder / "a.txt").write_text("original")
        original_unlink = Path.unlink

        def terminate_after_unlink(path, *args, **kwargs):
            original_unlink(path, *args, **kwargs)
            raise SystemExit("process interrupted")

        with patch.object(Path, "unlink", terminate_after_unlink):
            with self.assertRaises(SystemExit):
                self.history.apply(scan(self.folder))
        self.history.close()
        self.history = History(self.root / "history.sqlite")
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

    def test_undo_unlink_failure_is_reconciled_as_manual_review(self):
        source = self.folder / "a.txt"
        source.write_text("original")
        self.history.apply(scan(self.folder))
        with patch.object(Path, "unlink", side_effect=PermissionError("file locked")):
            self.history.undo_latest()
        self.history.reconcile()
        self.assertEqual(source.read_text(), "original")
        self.assertEqual((self.folder / "Documents" / "a.txt").read_text(), "original")
        self.assertEqual(self.history.rows()[0]["state"], "review")

    def test_recovery_does_not_trust_changed_restored_contents(self):
        source = self.folder / "a.txt"
        source.write_text("original")
        self.history.apply(scan(self.folder))
        # Emulate process termination at the filesystem boundary after unlink.
        original_unlink = Path.unlink

        def terminate_after_unlink(path, *args, **kwargs):
            original_unlink(path, *args, **kwargs)
            raise SystemExit("process interrupted")

        with patch.object(Path, "unlink", terminate_after_unlink):
            with self.assertRaises(SystemExit):
                self.history.undo_latest()
        source.write_text("externally changed after interruption")
        self.history.close()
        self.history = History(self.root / "history.sqlite")
        self.history.reconcile()
        self.assertEqual(source.read_text(), "externally changed after interruption")
        self.assertEqual(self.history.rows()[0]["state"], "review")
