# Download Folder Organizer

A local tool for turning a cluttered folder into categorized subfolders. Preview
every proposed move, apply it explicitly, and undo recorded moves without
overwriting existing files.

## Features

- Categories: Documents, Images, Videos, Audio, Archives, Code, and Other.
- Top-level scanning; directories, symbolic links, and dot-prefixed files skipped.
- Preview table, destination conflicts, operation history, and per-file errors.
- Exclusive destination creation: existing files are never overwritten.
- SHA-256 content checks before undo; occupied original paths are preserved.
- Interrupted-operation reconciliation and a lock preventing simultaneous moves
  from cooperating app sessions using the same history database.
- A command-line interface requiring only Python's standard library.

## Quick start — no installation needed

With Python 3.12 or newer, run:

```powershell
python web_app.py
```

Open **http://127.0.0.1:8501**. This browser interface uses only Python's standard
library and runs with the Python already installed on this machine. Stop it with
Ctrl+C. If the port is occupied, use `python web_app.py --port 8502`.

The server binds only to localhost and uses a form token to reject unauthorized
cross-site submissions. It is a personal local tool, not a production web server.
Do not expose it to a network. Files are never uploaded anywhere.

## Optional Streamlit interface

Use Python 3.12 or newer. The command line works with the installed MSYS2 Python;
the Streamlit UI should use standard Python from python.org, whose Windows wheels
avoid having to compile scientific dependencies under MSYS2.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

On Linux/macOS replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`.
Both interfaces run on your computer; enter a local folder path, click **Preview files**,
review the table, check the confirmation, then click **Apply organization**.
Use **Undo latest available batch** and inspect history for the outcome.

## Safe demo

```powershell
python scripts/create_demo.py
```

This prints a newly generated temporary folder path. Paste that path into the UI.
The sample `.jpg` contains placeholder text; the organizer categorizes by extension
and does not claim to validate image formats. No existing files are replaced.

Alternatively, use the printed path in the terminal:

```powershell
python -m organizer "PATH_PRINTED_BY_DEMO_SCRIPT"
python -m organizer "PATH_PRINTED_BY_DEMO_SCRIPT" --apply
python -m organizer --history
python -m organizer --undo
```

Applying from the terminal requires typing `APPLY`. Preview makes no changes to
the selected folder. The application creates its local history store separately.

## Design

```text
Local browser UI / optional Streamlit UI / CLI
       |
  scan and classify ----> preview plan
       |
  move service ---------> category folders
       |
  SQLite journal -------> reconciliation / guarded undo
```

`organizer/core.py` builds plans and computes fingerprints. `organizer/history.py`
records a pending entry before moving a file, then records completion. A move
creates an exclusive hard link in the category directory and removes the original
name. This avoids overwriting a destination and avoids copying large file contents.
It requires same-volume hard-link support, such as a local NTFS folder.

SQLite history lives in `.organizer/history.sqlite` next to the app; keep that
directory to retain undo information. It is excluded from Git because it contains
local paths. There are no credentials, API keys, uploads, or environment variables.

## Testing

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app.py web_app.py organizer scripts
```

Tests use temporary directories and cover classification, collisions, missing
sources, changed contents, occupied undo paths, interruption recovery, concurrent
operation locking, partial failures, CLI cancellation, and the complete browser
HTTP flow (preview, apply, undo, invalid token, escaped input). A real symlink test is
skipped when the account cannot create symlinks.

See [VERIFICATION.md](VERIFICATION.md) for the actual check results and the optional
Streamlit installation limitation. The default browser interface has been tested
through real HTTP requests; no manual visual inspection is claimed.

## Limitations

- Local, trusted folders only. Do not edit or reorganize files from another app
  while an operation is running; filesystem checks cannot prevent all external
  races. This is not a backup tool or a security boundary.
- No recursive scanning, duplicate deletion, or custom category editor.
- Categories use the last extension; file contents are not inspected for type.
- Unsupported filesystems, locked files, and permission failures are reported.
- Undo verifies contents rather than timestamps or full filesystem metadata.
- Empty category folders remain after undo. No directories are deleted.
- Ambiguous interrupted moves preserve both names and are marked `review` for
  manual inspection. Existing destination conflicts are marked `failed` and skipped.
- Undo targets the newest batch with moves still eligible for undo; earlier
  batches become available after it has been undone.
- No retention limit or pagination for history yet. No cloud or multi-machine sync.

## Roadmap

Optional: report exact duplicate files, configurable category rules, and history
filtering. Duplicate deletion is deliberately outside the current scope.

## Attribution and publication

Demo records are generated locally. Python, SQLite, and Streamlit are the main
tools. No project license has been selected yet. This project is local; GitHub
publication and a license choice require the owner's approval.

## Interview explanation

“I separated planning from execution so users can inspect changes before moving
files. Every move is journaled, destinations are created exclusively, and undo
checks the file's content fingerprint. When a failure leaves ambiguous state,
the tool preserves files and asks for review instead of guessing.”
