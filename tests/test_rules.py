from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


class RuleTests(unittest.TestCase):
    def test_related_formats_share_a_subject_and_unknown_is_unsorted(self):
        from organizer.rules import classify, default_settings
        settings = default_settings()
        for name in ["Computer Networks notes.pdf", "CN_lecture.pptx", "networking.docx"]:
            result = classify(name, settings)
            self.assertEqual(result.category, "Studies/Computer Networks")
            self.assertEqual(result.confidence, "High")
            self.assertIn("keyword", result.reason)
        self.assertEqual(classify("x83912.pdf", settings).category, "Unsorted")

    def test_custom_rules_and_categories_persist_and_rename_without_disk_moves(self):
        from organizer.settings import Settings
        from organizer.rules import classify
        with TemporaryDirectory() as directory:
            database = Path(directory) / "settings.sqlite"
            store = Settings(database)
            store.add_category("Studies/Distributed Systems")
            store.save_rule("distributed", "Studies/Distributed Systems", ["raft", "consensus"], ["pdf", "pptx"], 120)
            store.rename_category("Studies/Distributed Systems", "Studies/Distributed Computing")
            settings = Settings(database).load()
            self.assertEqual(classify("raft.pdf", settings).category, "Studies/Distributed Computing")
            self.assertEqual(classify("raft.exe", settings).category, "Installers")
            self.assertFalse((Path(directory) / "Studies").exists())
            store.delete_category("Studies/Distributed Computing")
            self.assertEqual(classify("raft.pdf", store.load()).category, "Unsorted")

    def test_unsafe_names_conflicts_and_ambiguous_rules_are_rejected(self):
        from organizer.settings import Settings
        from organizer.rules import classify
        with TemporaryDirectory() as directory:
            store = Settings(Path(directory) / "settings.sqlite")
            for name in ["../escape", "Studies/CON.txt", "Bad:name", "Bad\\name", "Trailing.", "media", "COM¹.txt"]:
                with self.subTest(name=name), self.assertRaises(ValueError):
                    store.add_category(name)
            store.save_rule("first", "Projects", ["robot"], [], 200)
            store.save_rule("second", "Personal", ["robot"], [], 200)
            result = classify("robot.pdf", store.load())
            self.assertEqual(result.category, "Unsorted")
            self.assertIn("Conflicting", result.reason)
            store.save_rule("second", "Personal", ["robot"], [], 201)
            self.assertEqual(classify("robot.pdf", store.load()).category, "Personal")
