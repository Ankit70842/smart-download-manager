from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


class SmartTests(unittest.TestCase):
    def test_destination_is_explicit_and_nested_paths_are_editable_without_writes(self):
        from organizer.smart import preview
        from organizer.rules import default_settings
        with TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source, destination = root / "source", root / "destination"
            source.mkdir()
            destination.mkdir()
            (source / "CN lecture.pdf").write_text("notes")
            (source / "unfinished.pdf.crdownload").write_text("partial")
            plan = preview(source, default_settings())
            with self.assertRaises(ValueError):
                plan.moves()
            plan.choose_destination(destination)
            self.assertEqual(plan.entries[0].category, "Studies/Computer Networks")
            self.assertEqual(plan.entries[0].destination, destination / "Studies" / "Computer Networks" / "CN lecture.pdf")
            plan.edit(0, "Projects", True, default_settings())
            self.assertEqual(plan.moves()[0].destination, destination / "Projects" / "CN lecture.pdf")
            self.assertTrue(plan.entries[1].skip_reason)
            self.assertFalse((destination / "Projects").exists())
            plan.edit(0, "Projects", False, default_settings())
            self.assertEqual(plan.moves(), [])

    def test_destination_traversal_and_category_file_conflicts_are_blocked(self):
        from organizer.smart import preview
        from organizer.rules import default_settings
        from organizer.paths import safe_destination
        with TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "CN.pdf").write_text("notes")
            plan = preview(root, default_settings())
            with self.assertRaises(ValueError):
                safe_destination(root, root / ".." / "escape" / "x.pdf")
            (root / "Studies").write_text("occupied")
            with self.assertRaises(ValueError):
                plan.choose_destination(root)
            self.assertIsNone(plan.destination_root)

    def test_separate_destination_nested_move_and_undo_round_trip(self):
        from organizer.smart import preview
        from organizer.rules import default_settings
        from organizer.history import History
        with TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source, target = root / "source", root / "target"
            source.mkdir()
            target.mkdir()
            original = source / "DBMS notes.pptx"
            original.write_bytes(b"study notes")
            plan = preview(source, default_settings())
            plan.choose_destination(target)
            history = History(root / "history.sqlite")
            try:
                batch = history.apply(plan.moves())
                moved = target / "Studies" / "DBMS" / original.name
                self.assertEqual(moved.read_bytes(), b"study notes")
                self.assertFalse(original.exists())
                self.assertTrue(history.rows()[0]["created_at"])
                self.assertEqual(history.rows()[0]["batch"], batch)
                history.undo_latest()
                self.assertEqual(original.read_bytes(), b"study notes")
            finally:
                history.close()

    def test_cross_volume_fallback_preserves_contents_and_never_overwrites(self):
        import errno
        from unittest.mock import patch
        from organizer.history import History
        from organizer.smart import preview
        from organizer.rules import default_settings
        with TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source, target = root / "source", root / "target"
            source.mkdir()
            target.mkdir()
            original = source / "CN.pdf"
            original.write_bytes(b"large enough study contents")
            plan = preview(source, default_settings())
            plan.choose_destination(target)
            history = History(root / "history.sqlite")
            try:
                with patch("os.link", side_effect=OSError(errno.EXDEV, "Different device")):
                    history.apply(plan.moves())
                    self.assertFalse(original.exists())
                    self.assertEqual((target / "Studies" / "Computer Networks" / "CN.pdf").read_bytes(), b"large enough study contents")
                    history.undo_latest()
                self.assertEqual(original.read_bytes(), b"large enough study contents")
            finally:
                history.close()
