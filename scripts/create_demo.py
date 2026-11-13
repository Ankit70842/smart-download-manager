"""Create a fresh disposable demo directory; never replace existing files."""

from pathlib import Path
import tempfile


def create_demo(parent=None):
    root = Path(tempfile.mkdtemp(prefix="organizer-demo-", dir=parent))
    for name, content in {
        "notes.txt": "Meeting notes\n", "budget.csv": "item,cost\nbook,200\n",
        "hello.py": "print('hello')\n", "LICENSE": "Demo sample\n",
        "photo.jpg": "Placeholder image file for organization demo\n",
    }.items():
        (root / name).write_text(content, encoding="utf-8")
    return root


if __name__ == "__main__":
    print(create_demo())
