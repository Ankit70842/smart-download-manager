# Download Folder Organizer

Build a local Python application that scans only top-level regular files, previews
category destinations, moves without overwriting, and records recoverable history.
Skip symbolic links and directories. Never delete duplicate files.

Architecture: Streamlit interface → organizer service → filesystem and SQLite log.
The default interface is now a dependency-free local HTTP UI (`web_app.py`),
because this machine's MSYS2 Python cannot readily install Streamlit's scientific
dependencies. Streamlit remains optional; both interfaces use the same service.
The database stores each move before execution, including a content fingerprint.
Undo checks fingerprints and refuses occupied original paths. Interrupted moves
are reconciled against both paths. One operation at a time is supported.

Milestones: foundation; scan and preview; safe moves; history and undo; interface;
documentation and verification. Run `python -m unittest discover -s tests -v`
after each behavior change. Review and commit each milestone using Conventional
Commits. No remote creation, push, or deployment without explicit approval.

Acceptance demo: generate disposable sample files, preview, apply, inspect sorted
files, undo, and confirm original contents. Test collisions, partial failures,
changed files, missing files, symlinks, and interrupted operations.
