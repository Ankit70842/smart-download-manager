"""Durable move journal. Operations are intended for one local app instance."""

import os
from pathlib import Path
import sqlite3
import uuid
from functools import wraps

from organizer.core import Move, fingerprint


def exclusive(operation):
    """Serialize cooperating app sessions using a separate SQLite write lock."""
    @wraps(operation)
    def guarded(self, *args, **kwargs):
        lock = sqlite3.connect(self.lock_path, timeout=0)
        try:
            lock.execute("BEGIN IMMEDIATE")
            return operation(self, *args, **kwargs)
        finally:
            lock.close()
    return guarded


def transfer(source: Path, destination: Path):
    """Create a same-volume hard link exclusively, then remove the old name."""
    os.link(source, destination)
    source.unlink()


class History:
    def __init__(self, database: Path):
        database.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path = str(database) + ".lock"
        self.db = sqlite3.connect(database)
        self.db.row_factory = sqlite3.Row
        self.db.execute("""CREATE TABLE IF NOT EXISTS moves (
            id INTEGER PRIMARY KEY, batch TEXT, source TEXT, destination TEXT,
            digest TEXT, state TEXT, error TEXT DEFAULT '')""")
        self.db.commit()

    def close(self):
        self.db.close()

    def rows(self):
        return [dict(row) for row in self.db.execute("SELECT * FROM moves ORDER BY id DESC")]

    def update(self, row_id, state, error=""):
        self.db.execute("UPDATE moves SET state=?, error=? WHERE id=?",
                        (state, error, row_id))
        self.db.commit()

    @exclusive
    def apply(self, moves: list[Move]):
        batch = uuid.uuid4().hex
        for move in moves:
            source, destination = move.source, move.destination
            row_id = None
            try:
                if source.is_symlink() or not source.is_file():
                    raise ValueError("Source is missing or is not a regular file.")
                if destination.parent.parent != source.parent:
                    raise ValueError("Destination must be a category inside the source folder.")
                parent = destination.parent
                if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
                    raise ValueError("Category links and junctions are not supported.")
                parent.mkdir(exist_ok=True)
                digest = fingerprint(source)
                cursor = self.db.execute(
                    "INSERT INTO moves(batch,source,destination,digest,state) VALUES(?,?,?,?,?)",
                    (batch, str(source), str(destination), digest, "pending"))
                row_id = cursor.lastrowid
                self.db.commit()
                transfer(source, destination)
                self.update(row_id, "moved")
            except (OSError, ValueError) as error:
                if row_id is None:
                    cursor = self.db.execute(
                        "INSERT INTO moves(batch,source,destination,digest,state,error) VALUES(?,?,?,?,?,?)",
                        (batch, str(source), str(destination), "", "failed", str(error)))
                    self.db.commit()
                else:
                    # Both paths may exist if unlink failed; preserve both for review.
                    self.update(row_id, "pending", str(error))
        return batch

    @exclusive
    def reconcile(self):
        self._reconcile()

    def _reconcile(self):
        for row in self.rows():
            if row["state"] not in ("pending", "undoing"):
                continue
            source, destination = Path(row["source"]), Path(row["destination"])
            try:
                if source.exists() and not destination.exists():
                    state = "undone" if row["state"] == "undoing" else "failed"
                elif not source.exists() and destination.is_file() and not destination.is_symlink():
                    state = "moved" if fingerprint(destination) == row["digest"] else "review"
                else:
                    state = "review"
                self.update(row["id"], state, "Interrupted or failed operation reconciled.")
            except OSError as error:
                self.update(row["id"], "review", str(error))

    @exclusive
    def undo_latest(self):
        self._reconcile()
        row = self.db.execute(
            "SELECT batch FROM moves WHERE state='moved' ORDER BY id DESC LIMIT 1").fetchone()
        if row is None:
            return
        for move in self.rows():
            if move["batch"] != row["batch"] or move["state"] != "moved":
                continue
            source, destination = Path(move["source"]), Path(move["destination"])
            try:
                if source.exists() or source.is_symlink():
                    raise ValueError("Original path is occupied; undo skipped.")
                if destination.is_symlink() or destination.parent.resolve() != destination.parent:
                    raise ValueError("Destination path changed; undo skipped.")
                if fingerprint(destination) != move["digest"]:
                    raise ValueError("File contents changed; undo skipped.")
                self.update(move["id"], "undoing")
                transfer(destination, source)
                self.update(move["id"], "undone")
            except (OSError, ValueError) as error:
                self.update(move["id"], "moved", str(error))
