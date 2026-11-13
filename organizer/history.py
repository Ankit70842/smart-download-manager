"""Durable move journal. Operations are intended for one local app instance."""

import os
from pathlib import Path
import sqlite3
import uuid
import json
import errno
import shutil
from functools import wraps

from organizer.core import Move, file_signature, fingerprint
from organizer.paths import safe_destination


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


def transfer(source: Path, destination: Path, on_ready=None):
    """Exclusive link, or verified exclusive copy for another filesystem."""
    try:
        os.link(source, destination)
    except OSError as error:
        if error.errno not in (errno.EXDEV, errno.ENOTSUP) and getattr(error, "winerror", None) not in (1, 17, 50):
            raise
        before = file_signature(source)
        with source.open("rb") as reader, destination.open("xb") as writer:
            shutil.copyfileobj(reader, writer, length=1024 * 1024)
            writer.flush()
            os.fsync(writer.fileno())
        if file_signature(source) != before or fingerprint(source) != fingerprint(destination):
            raise ValueError("Source changed during copy; both paths preserved for review.")
    if on_ready:
        on_ready(destination)
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
        columns = {row[1] for row in self.db.execute("PRAGMA table_info(moves)")}
        for name in ("created_at", "destination_identity", "restore_identity"):
            if name not in columns:
                self.db.execute(f"ALTER TABLE moves ADD COLUMN {name} TEXT NOT NULL DEFAULT ''")
        self.db.execute("""CREATE TRIGGER IF NOT EXISTS timestamp_move AFTER INSERT ON moves
            BEGIN UPDATE moves SET created_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=NEW.id; END""")
        self.db.commit()

    def close(self):
        self.db.close()

    def rows(self):
        return [dict(row) for row in self.db.execute("SELECT * FROM moves ORDER BY id DESC")]

    def update(self, row_id, state, error=""):
        self.db.execute("UPDATE moves SET state=?, error=? WHERE id=?",
                        (state, error, row_id))
        self.db.commit()

    def _remember_identity(self, row_id, path, column):
        if column not in ("destination_identity", "restore_identity"):
            raise ValueError("Invalid identity field")
        self.db.execute(f"UPDATE moves SET {column}=? WHERE id=?",
                        (json.dumps(file_signature(path)), row_id))
        self.db.commit()

    @staticmethod
    def _identity_matches(path, stored):
        return not stored or tuple(json.loads(stored)) == file_signature(path)

    @exclusive
    def apply(self, moves: list[Move]):
        batch = uuid.uuid4().hex
        for move in moves:
            source, destination = move.source, move.destination
            row_id = None
            operation = "Validate source and destination"
            try:
                if source.is_symlink() or not source.is_file():
                    raise ValueError("Source is missing or is not a regular file.")
                if move.signature is None or file_signature(source) != move.signature:
                    raise ValueError("Source changed after preview; preview again before moving it.")
                if move.destination_root is not None:
                    safe_destination(move.destination_root, destination)
                elif destination.parent.parent != source.parent:
                    raise ValueError("Destination must be a category inside the source folder.")
                parent = destination.parent
                if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
                    raise ValueError("Category links and junctions are not supported.")
                operation = f"Create category folder {parent}"
                parent.mkdir(parents=True, exist_ok=True)
                operation = "Read source fingerprint"
                digest = fingerprint(source)
                cursor = self.db.execute(
                    "INSERT INTO moves(batch,source,destination,digest,state) VALUES(?,?,?,?,?)",
                    (batch, str(source), str(destination), digest, "pending"))
                row_id = cursor.lastrowid
                self.db.commit()
                operation = "Move file (create destination hard link, then remove source name)"
                transfer(source, destination,
                         lambda path: self._remember_identity(row_id, path, "destination_identity"))
                self.update(row_id, "moved")
            except FileExistsError as error:
                if row_id is not None:
                    self.update(row_id, "failed", "Destination already exists; file skipped.")
                else:
                    self.db.execute(
                        "INSERT INTO moves(batch,source,destination,digest,state,error) VALUES(?,?,?,?,?,?)",
                        (batch, str(source), str(destination), "", "failed", str(error)))
                    self.db.commit()
            except (OSError, ValueError) as error:
                details = f"{operation}: {error}"
                if row_id is None:
                    cursor = self.db.execute(
                        "INSERT INTO moves(batch,source,destination,digest,state,error) VALUES(?,?,?,?,?,?)",
                        (batch, str(source), str(destination), "", "failed", details))
                    self.db.commit()
                else:
                    # Both paths may exist if unlink failed; preserve both for review.
                    self.update(row_id, "pending", details)
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
                    if row["state"] == "undoing":
                        valid = (source.is_file() and not source.is_symlink()
                                 and source.parent.resolve() == source.parent
                                 and self._identity_matches(source, row["restore_identity"])
                                 and fingerprint(source) == row["digest"])
                        state = "undone" if valid else "review"
                    else:
                        state = "failed"
                elif not source.exists() and destination.is_file() and not destination.is_symlink():
                    valid = (destination.parent.resolve() == destination.parent
                             and self._identity_matches(destination, row["destination_identity"])
                             and fingerprint(destination) == row["digest"])
                    state = "moved" if valid else "review"
                else:
                    state = "review"
                self.update(row["id"], state, row["error"] or "Interrupted operation reconciled.")
            except OSError as error:
                self.update(row["id"], "review", str(error))

    @exclusive
    def undo_latest(self):
        self._reconcile()
        self._undo_rows(self._undo_targets())

    def _undo_targets(self, batch=None, file_id=None):
        rows = self.rows()
        if file_id is not None:
            return [row for row in rows if row["id"] == int(file_id)]
        if batch is None:
            latest = next((row for row in rows if row["state"] == "moved"), None)
            batch = latest["batch"] if latest else None
        return [row for row in rows if row["batch"] == batch]

    def _undo_problem(self, move):
        if move["state"] != "moved":
            return "Not reversible: " + move["state"]
        source, destination = Path(move["source"]), Path(move["destination"])
        if source.exists() or source.is_symlink():
            return "Original path is occupied; undo skipped."
        if not source.parent.is_dir() or source.parent.resolve() != source.parent:
            return "Original folder is missing or redirected; undo skipped."
        if (not destination.is_file() or destination.is_symlink()
                or destination.parent.resolve() != destination.parent):
            return "Organized file is missing or its path changed; undo skipped."
        if fingerprint(destination) != move["digest"]:
            return "File contents changed; undo skipped."
        if not self._identity_matches(destination, move["destination_identity"]):
            return "File identity or metadata changed (possibly replaced); undo skipped."
        return ""

    def preview_undo(self, batch=None, file_id=None):
        result = []
        for move in self._undo_targets(batch, file_id):
            try:
                problem = self._undo_problem(move)
            except OSError as error:
                problem = str(error)
            result.append(dict(move, can_undo=not problem, undo_reason=problem or "Ready to restore"))
        return result

    @exclusive
    def undo_operation(self, batch):
        self._reconcile()
        self._undo_rows(self._undo_targets(batch=batch))

    @exclusive
    def undo_file(self, file_id):
        self._reconcile()
        self._undo_rows(self._undo_targets(file_id=file_id))

    def _undo_rows(self, rows):
        for move in rows:
            if move["state"] != "moved":
                continue
            source, destination = Path(move["source"]), Path(move["destination"])
            started = False
            try:
                problem = self._undo_problem(move)
                if problem:
                    raise ValueError(problem)
                self.update(move["id"], "undoing")
                started = True
                transfer(destination, source,
                         lambda path: self._remember_identity(move["id"], path, "restore_identity"))
                self.update(move["id"], "undone")
            except (OSError, ValueError) as error:
                self.update(move["id"], "undoing" if started else "moved", str(error))
                if started:
                    self._reconcile()
