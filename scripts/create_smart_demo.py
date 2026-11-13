"""Generate new disposable fixtures; never read or modify the real Downloads."""
import argparse
import json
from pathlib import Path
import tempfile


def create_demo(parent=None):
    root = Path(tempfile.mkdtemp(prefix="smart-review-", dir=parent)).resolve()
    source, destination = root / "source", root / "destination"
    source.mkdir()
    (destination / "Personal").mkdir(parents=True)
    (destination / "Personal" / "invoice.txt").write_text("existing invoice", encoding="utf-8")
    files = {"Computer Networks lecture.pdf": "networks", "DBMS assignment.pptx": "database",
             "invoice.txt": "new invoice", "mystery839.pdf": "unknown", "setup.exe": "never execute",
             "video.mp4": "video", "robot.pdf": "robotics", "pending.pdf.crdownload": "partial"}
    for name, text in files.items():
        (source / name).write_text(text, encoding="utf-8")
    (source / "nested").mkdir()
    (source / "Code").mkdir()
    (source / "Documents").mkdir()
    manifest = dict(root=str(root), source=str(source), destination=str(destination), files=files)
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, help="Existing parent folder (default: system temp)")
    args = parser.parse_args()
    print(json.dumps(create_demo(args.parent), indent=2))
