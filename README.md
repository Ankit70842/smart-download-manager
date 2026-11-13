# Open Folder Organizer

A local tool for turning a cluttered folder into categorized subfolders. Preview
every proposed move, apply it explicitly, and undo recorded moves without
overwriting existing files.

## Features

- Categories: Documents, Images, Videos, Audio, Archives, Code, and Other.
- Top-level scanning; directories, symbolic links, and dot-prefixed files skipped.
- Preview table, destination conflicts, operation history, and per-file errors.
- Apply rejects files replaced or changed since preview, and rejects an old tab's
  form when another tab has generated a newer preview.
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

## Use the application

1. Paste a local folder path and click **Preview files**.
2. Review each filename, category, and destination conflict.
3. Check the confirmation and click **Apply these moves**.
4. Inspect operation history. Use **Undo latest available batch** to reverse
   eligible moves; changed files and occupied original paths are skipped.

The supported browser UI is handwritten HTML/CSS served by Python's built-in
`HTTPServer` and `BaseHTTPRequestHandler`. No framework installation is required.

## Optional Streamlit interface

**Experimental and unsupported for the initial release.** `app.py` is a separate
Streamlit frontend, not the working default interface. It has only been
syntax-checked; its dependency environment has not been resolved or audited.
`requirements.txt` is only for that frontend. The default UI and CLI have no
third-party runtime dependencies.

See [experimental Streamlit notes](docs/EXPERIMENTAL_STREAMLIT.md) for optional
setup and the observed installation failure.

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
For isolated demos or tests, pass `--database "PATH_TO_DEMO_HISTORY.sqlite"` on
every CLI command, including undo. Keep that database outside the scanned files.

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
Moves and undo are not a single filesystem transaction. If linking succeeds but
unlinking fails, both names remain and the operation is marked `review`. Original
filesystem error details are retained. Interrupted undo is only marked complete
when the restored content still matches its recorded SHA-256 fingerprint.

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
Streamlit installation limitation, and [QUALITY_REVIEW.md](QUALITY_REVIEW.md) for
the audit. The default UI was exercised with Playwright CLI in Chrome, and desktop
and mobile screenshots were visually inspected. Browser testing used disposable
data; automated HTTP/CLI tests use isolated history databases.

With Playwright CLI installed, a reusable mobile regression check is available:

```powershell
playwright-cli open http://127.0.0.1:8501 --browser=chrome
# First create at least one history row using a disposable sample folder.
playwright-cli run-code --filename=tests/browser_mobile.js
playwright-cli close
```

The check resizes the viewport to 390 × 844 and verifies readable history headers
without page-level horizontal overflow. Browser tooling is optional for running
the application and is not a production dependency.

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
- The single-process UI handles one request/operation at a time. Idle socket reads
  time out after two seconds; moving or hashing large files can still delay the UI.
- The local form token and Host check protect against web-based cross-site
  submissions, not other local programs or users with access to your account.
- Streamlit dependencies remain unpinned and unaudited as a resolved environment;
  the optional frontend is outside the verified release surface.

## Roadmap

Optional: report exact duplicate files, configurable category rules, and history
filtering. Duplicate deletion is deliberately outside the current scope.

## Attribution and publication

Demo records are generated locally. Python's standard library, HTML/CSS, and
SQLite power the default application; Streamlit is optional. No project license
has been selected yet. A license will be added only after the owner's approval;
the project is not currently offered under an open-source license. GitHub
publication also requires explicit approval. See
[publication proposal](PUBLICATION.md) for suggested repository metadata and scope.

## Interview explanation

“I separated planning from execution so users can inspect changes before moving
files. Every move is journaled, destinations are created exclusively, and undo
checks the file's content fingerprint. When a failure leaves ambiguous state,
the tool preserves files and asks for review instead of guessing.”
