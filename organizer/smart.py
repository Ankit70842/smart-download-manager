"""Editable preview state. Constructing or editing a plan never moves files."""
from dataclasses import dataclass, field
from pathlib import Path

from organizer.core import Move, file_signature
from organizer.paths import folder_root, safe_destination
from organizer.rules import category_path, classify
from organizer.access import ensure_movable

INCOMPLETE = {".crdownload", ".part", ".partial", ".tmp", ".download", ".opdownload"}


@dataclass
class Entry:
    source: Path
    signature: tuple | None = None
    category: str = "Unsorted"
    confidence: str = "Needs review"
    reason: str = ""
    skip_reason: str = ""
    selected: bool = False
    destination: Path | None = None

    @property
    def status(self):
        if self.skip_reason:
            return "Skipped: " + self.skip_reason
        if self.destination is None:
            return "Choose destination"
        if self.destination.exists() or self.destination.is_symlink():
            return "Conflict: skipped"
        return "Ready" if self.selected else "Excluded"


@dataclass
class Preview:
    source: Path
    entries: list[Entry] = field(default_factory=list)
    destination_root: Path | None = None

    def choose_destination(self, root):
        root = folder_root(root)
        targets = []
        for entry in self.entries:
            target = root.joinpath(*entry.category.split("/"), entry.source.name)
            if not entry.skip_reason:
                safe_destination(root, target)
            targets.append(target)
        self.destination_root = root
        for entry, target in zip(self.entries, targets):
            entry.destination = target if not entry.skip_reason else None

    def edit(self, index, category, selected, settings):
        if not 0 <= index < len(self.entries):
            raise ValueError("File no longer belongs to this preview.")
        category = category_path(category)
        if category not in settings["categories"]:
            raise ValueError("Choose an existing category.")
        entry = self.entries[index]
        if entry.skip_reason:
            raise ValueError("Skipped items cannot be selected or moved.")
        if self.destination_root is not None:
            target = self.destination_root.joinpath(*category.split("/"), entry.source.name)
            safe_destination(self.destination_root, target)
            entry.destination = target
        entry.selected = bool(selected)
        if entry.category != category:
            entry.category = category
            entry.confidence = "User choice"
            entry.reason = "Category explicitly selected by you; no rule was saved."

    def moves(self):
        if self.destination_root is None:
            raise ValueError("Choose where organized files should go before applying.")
        result = []
        for entry in self.entries:
            if entry.selected and not entry.skip_reason:
                safe_destination(self.destination_root, entry.destination)
                result.append(Move(entry.source, entry.destination, entry.signature, self.destination_root))
        return result


def preview(folder, settings):
    root = folder_root(folder)
    plan = Preview(root)
    for source in sorted(root.iterdir(), key=lambda p: p.name.casefold()):
        entry = Entry(source)
        try:
            if source.is_symlink() or (hasattr(source, "is_junction") and source.is_junction()):
                entry.skip_reason = "Link or junction"
            elif not source.is_file():
                entry.skip_reason = "Directory or unsupported item"
            elif source.name.startswith("."):
                entry.skip_reason = "Hidden application file"
            elif source.suffix.lower() in INCOMPLETE:
                entry.skip_reason = "Incomplete download or temporary file"
            else:
                entry.signature = file_signature(source)
                ensure_movable(source)
                result = classify(source.name, settings)
                entry.category, entry.confidence, entry.reason = result.category, result.confidence, result.reason
                entry.selected = result.confidence != "Needs review"
        except OSError as error:
            entry.skip_reason = f"File unavailable or locked: {error}"
        plan.entries.append(entry)
    return plan
