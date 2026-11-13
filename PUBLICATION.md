# GitHub publication proposal

Status: prepared locally; no remote repository, push, tag, or release created.
All original commits must remain intact. No squash, rebase, amend, or force-push.

## Suggested metadata

- Repository name: `open-folder-organizer`
- Description: `A local Python file organizer with a browser UI, safe move previews, collision protection, and journaled undo.`
- Topics: `python`, `file-organizer`, `automation`, `file-management`, `sqlite`,
  `http-server`, `undo`, `local-first`, `portfolio-project`
- Suggested visibility: public, pending approval.
- Existing branch: `master`. Keep it unless the owner requests a rename.
- Proposed first release: `v0.1.0`, an initial feature-complete local utility with
  explicit filesystem and recovery limitations. No tag or release exists yet.
- GitHub owner: not selected; confirm before any remote creation or push.

## Supported initial release

Default `web_app.py` HTTP-server browser interface and `python -m organizer` CLI;
preview, confirmed apply, no-overwrite collisions, SQLite journal, and guarded undo.
Python 3.12+, no third-party runtime dependencies for these entry points.

`app.py` and `requirements.txt` remain in source as experimental, unsupported
Streamlit material. They are not the running UI or a tested installation target.

## Approved license

The owner approved the MIT License for this utility. It is short and permissive,
with preservation of copyright/license notices.
See [MIT license summary](https://choosealicense.com/licenses/mit/).

The root `LICENSE` contains the standard MIT text with
`Copyright (c) 2026 Ankit Chaurasia`. License approval does not authorize creating
a remote repository, pushing commits, or publishing a release.

## Publication checks

- Keep source, tests, demo generator, README, planning, verification, and review docs.
- Exclude local journals, credentials/configuration, virtual environments, failed
  downloads, browser tooling, screenshots, caches, and machine-specific output.
- Preserve `.organizer` locally because it may be needed for undo; never upload it.
- Run tests and scan the content actually tracked by Git, including history.
- Commit preparation changes as new focused commits, preserving the original
  16-commit history ending at `7745827c1e6b3ceab6917e53ea654aac2c5dbf27`.
- Before publication, confirm owner, repository name, visibility, target branch,
  license decision, and the exact actions approved. Remote creation, push, and
  release publication require explicit approval; this proposal authorizes none.

## Preparation verification

- 20 tests executed: 19 passed, 1 Windows symlink-permission skip; syntax checks passed.
- Ignore rules checked for credentials, local journals/sidecars, runtime tools,
  environments, and cache files; safe `.env.example` and `.env.sample` remain allowed.
- Tracked working content and Git history checked for credential patterns; no
  candidates found. Pattern scans are not a guarantee of detecting every secret.
- Removed incomplete Python downloads/environment, disposable review data,
  browser snapshots, temporary browser scripts, and bytecode caches.
- Local undo history and reusable ignored browser tooling retained.
- Existing commit author names/emails remain in Git metadata and would be visible
  in a public repository. They were deliberately not rewritten.
