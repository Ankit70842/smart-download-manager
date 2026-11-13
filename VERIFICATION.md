# Verification — 13 November 2026

## Executed checks

- `python -m unittest discover -s tests -v`: 22 tests, 21 passed, 1 skipped.
  The skipped test needs Windows symbolic-link creation permission.
- The same suite passed under standard CPython 3.12.4 and PATH-selected
  MSYS2 Python 3.12.7.
- `python -m compileall -q app.py web_app.py organizer scripts`: passed.
- Real HTTP tests cover preview/apply/undo, stale-tab forms, required confirmation,
  malformed tokens, Host validation, escaped input, and bounded incomplete requests.
- Filesystem/service tests cover filename conflicts, changed source and undo files,
  occupied original paths, missing files, operation locking, partial moves, and
  interrupted apply/undo recovery. Crash injection occurs at the filesystem seam;
  it is not a physical power-loss or storage durability test.
- CLI tests cover preview, cancellation, apply, and undo with isolated databases.
- Permission regressions cover denied category creation without data loss and
  HTTP diagnostics that identify the actual process account/interpreter.
- Live permission reproduction: the sandbox-owned server previewed three new
  files in a unique subfolder of `OrganizerTest`, then failed category creation
  with WinError 5. The same interpreter was restarted under Ankit; Preview,
  Apply (3/3), and Undo passed and original contents were verified. The folder's
  ACL was not changed and no existing test files or Downloads were organized.
- Playwright CLI 0.1.24 + Chrome: preview four files; confirmation blocks unchecked
  submission; remove one source before apply; move two files; skip one collision
  and one missing source; undo both moves. Filesystem contents verified afterward.
- Desktop (1280 px) and mobile (390 × 844) screenshots visually inspected. A mobile
  table wrapping regression was reproduced and fixed; browser assertion passed.
- Browser console: zero errors and warnings during the tested workflow.
- `npm audit --prefix .runtime/browser --audit-level=moderate`: zero reported
  vulnerabilities in the optional local Playwright tooling.
- Deterministic credential-pattern scan of tracked source and unique Git-history
  blobs: no candidates. Review tool emitted locations only, never secret values.
- Staged whitespace checks passed; tracked artifact inventory inspected. Local
  databases, runtime downloads, snapshots, and virtual environments are ignored.

## Limits

The optional Streamlit frontend was syntax-checked only, not executed. No resolved
Streamlit dependency lock or transitive vulnerability audit is available. It is
not the running application. See the README for the observed install failure.

Agent conversation logs outside the repository were not scanned; no claim is made
about unrelated account data. Automated secret scans are pattern-based and cannot
prove absence of every possible credential format.

No existing user downloads were organized. Tests used generated temporary files
or the ignored `.runtime/review` directory. No GitHub remote creation, push,
deployment, or publication was performed.
