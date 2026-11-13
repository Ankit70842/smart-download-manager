"""Preview plans without changing the selected folder."""

from dataclasses import dataclass
from pathlib import Path
import hashlib


CATEGORIES = {
    "Documents": "pdf doc docx txt odt rtf xls xlsx csv ppt pptx",
    "Images": "jpg jpeg png gif webp svg bmp heic",
    "Videos": "mp4 mkv mov avi webm",
    "Audio": "mp3 wav flac aac ogg m4a",
    "Archives": "zip rar 7z tar gz bz2",
    "Code": "py js ts tsx jsx html css java c cpp h json yaml yml sql sh",
}


@dataclass(frozen=True)
class Move:
    source: Path
    destination: Path


def fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan(folder: str | Path) -> list[Move]:
    root = Path(folder).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Select a directory.")
    moves = []
    for source in sorted(root.iterdir(), key=lambda p: p.name.casefold()):
        if source.is_symlink() or not source.is_file() or source.name.startswith("."):
            continue
        extension = source.suffix.lower().lstrip(".")
        category = next(
            (name for name, extensions in CATEGORIES.items()
             if extension in extensions.split()), "Other"
        )
        moves.append(Move(source, root / category / source.name))
    return moves
