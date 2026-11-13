"""Transactional category/rule settings in the existing SQLite database."""
from contextlib import closing
import json
from pathlib import Path
import re
import sqlite3

from organizer.rules import category_path, default_settings


def validate(data):
    categories = data["categories"]
    if len(categories) > 200 or len(data["rules"]) > 500:
        raise ValueError("Limit: 200 categories and 500 rules.")
    if "Unsorted" not in categories:
        raise ValueError("Unsorted must remain available.")
    if len({c.casefold() for c in categories}) != len(categories):
        raise ValueError("Category names conflict (Windows ignores letter case).")
    for category in categories:
        category_path(category)
        if "/" in category and category.rsplit("/", 1)[0] not in categories:
            raise ValueError("Create the parent category first.")
    ids = set()
    for rule in data["rules"]:
        if not rule["id"] or len(rule["id"]) > 80 or rule["id"] in ids:
            raise ValueError("Rule IDs must be unique and at most 80 characters.")
        ids.add(rule["id"])
        if rule["category"] not in categories or not -1000 <= int(rule["priority"]) <= 1000:
            raise ValueError("Choose an existing category and priority from -1000 to 1000.")
        if not rule["keywords"] and not rule["extensions"]:
            raise ValueError("A rule needs keywords or extensions.")
        if len(rule["keywords"]) > 30 or any(not word.strip() or len(word) > 80 for word in rule["keywords"]):
            raise ValueError("Use up to 30 non-empty keywords of at most 80 characters.")
        if any(not re.fullmatch(r"[a-z0-9]{1,16}", ext) for ext in rule["extensions"]):
            raise ValueError("Use extensions such as pdf, pptx, or txt, without dots.")
    return data


class Settings:
    def __init__(self, database):
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK(id=1), data TEXT NOT NULL)")
            db.execute("INSERT OR IGNORE INTO settings VALUES (1,?)", (json.dumps(default_settings()),))

    def load(self):
        with closing(sqlite3.connect(self.database)) as db:
            return validate(json.loads(db.execute("SELECT data FROM settings WHERE id=1").fetchone()[0]))

    def _change(self, mutation):
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            data = json.loads(db.execute("SELECT data FROM settings WHERE id=1").fetchone()[0])
            mutation(data)
            db.execute("UPDATE settings SET data=? WHERE id=1", (json.dumps(validate(data)),))

    def add_category(self, name):
        name = category_path(name)
        def mutation(data):
            if name.casefold() in {c.casefold() for c in data["categories"]}:
                raise ValueError("Category already exists.")
            parts = name.split("/")
            for index in range(1, len(parts) + 1):
                parent = "/".join(parts[:index])
                if parent not in data["categories"]:
                    data["categories"].append(parent)
        self._change(mutation)

    def rename_category(self, old, new):
        new = category_path(new)
        def mutation(data):
            if old == "Unsorted" or old not in data["categories"] or new.startswith(old + "/"):
                raise ValueError("Cannot rename this category or move it inside itself.")
            def rename(value):
                return new + value[len(old):] if value == old or value.startswith(old + "/") else value
            data["categories"] = [rename(c) for c in data["categories"]]
            for rule in data["rules"]:
                rule["category"] = rename(rule["category"])
        self._change(mutation)

    def delete_category(self, name):
        def mutation(data):
            if name == "Unsorted" or name not in data["categories"]:
                raise ValueError("Unsorted cannot be deleted; choose an existing category.")
            removed = {c for c in data["categories"] if c == name or c.startswith(name + "/")}
            data["categories"] = [c for c in data["categories"] if c not in removed]
            data["rules"] = [r for r in data["rules"] if r["category"] not in removed]
        self._change(mutation)

    def save_rule(self, rule_id, category, keywords, extensions, priority):
        rule = dict(id=rule_id.strip(), category=category_path(category),
                    keywords=[word.strip().casefold() for word in keywords if word.strip()],
                    extensions=[ext.strip().lower().lstrip(".") for ext in extensions if ext.strip()], priority=int(priority))
        def mutation(data):
            data["rules"] = [r for r in data["rules"] if r["id"] != rule["id"]] + [rule]
        self._change(mutation)

    def delete_rule(self, rule_id):
        def mutation(data):
            if rule_id not in {r["id"] for r in data["rules"]}:
                raise ValueError("Rule not found.")
            data["rules"] = [r for r in data["rules"] if r["id"] != rule_id]
        self._change(mutation)
