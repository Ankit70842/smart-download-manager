"""Validate explicitly selected local roots and category descendants."""
from pathlib import Path
from organizer.rules import category_path


def folder_root(value):
    text = str(value).strip()
    if not text or text.startswith(("\\\\", "//")):
        raise ValueError("Choose an existing local folder; network paths are unsupported.")
    path = Path(text).expanduser()
    if not path.is_absolute():
        raise ValueError("Use an absolute folder path.")
    path = path.resolve(strict=True)
    if not path.is_dir():
        raise ValueError("Choose a folder, not a file.")
    return path


def safe_destination(root, destination):
    root, destination = Path(root), Path(destination)
    if not root.is_absolute() or root.resolve(strict=True) != root or not root.is_dir():
        raise ValueError("Selected destination root changed or is unavailable.")
    relative = destination.relative_to(root)
    if len(relative.parts) < 2:
        raise ValueError("Destination must be inside a category under the chosen root.")
    category_path("/".join(relative.parts))
    current = root
    for part in relative.parts[:-1]:
        current = current / part
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            raise ValueError("Category links and junctions are unsupported.")
        if current.exists() and not current.is_dir():
            raise ValueError("A category path is occupied by a file.")
    if destination.is_symlink():
        raise ValueError("Destination is a symbolic link.")
    return destination
