# Publication record — 14 November 2026

Status: **published after the owner's explicit approval**. Repository:
[Ankit70842/smart-download-manager](https://github.com/Ankit70842/smart-download-manager).

## Concrete destination

- Owner: **Ankit70842** (confirmed by the connected GitHub account).
- Repository: **smart-download-manager**.
- Visibility: **public**.
- Target/default branch: **main**. The local `master` branch was renamed without
  rewriting commits. `origin` uses the credential-free HTTPS repository URL.
- URL: `https://github.com/Ankit70842/smart-download-manager`.
- Description: `An offline-first Windows downloads manager with explainable filename rules, a simple review workflow, and safe journaled undo.`
- Topics: `python`, `windows`, `file-organizer`, `automation`, `sqlite`,
  `local-first`, `file-management`, `rule-engine`, `portfolio-project`.
- License: existing MIT, Copyright (c) 2026 Ankit Chaurasia.

The repository did not exist. It was created empty and public, with no generated
README/license/initial commit. A normal non-force push uploaded the existing Git
history directly; no merge, squash, rebase, or replacement history was needed.

## Content and history

Preserve all **29 pre-preparation commits** through `b933e67`, plus the new focused
security, CI, and documentation preparation commits. No squash, rebase, amend,
reset, author changes, or force-push. Author names/emails already in Git metadata
will remain visible in the public history.

Include the working simple HTTP dashboard, existing CLI, supported source/tests,
MIT license, actual screenshots, design/review documents, and CI configuration.
Streamlit remains clearly experimental/unsupported. No UI redesign or runtime
feature changes were made for this publication preparation.

Exclude local journals/settings, personal Downloads files, runtime fixtures,
secrets, credentials, environments, editor state, logs, and caches. Keep local
undo data on disk; it is not part of the publication artifact.

## Verification and limits

- Python suite: **49 tests, 48 passed, 1 permission-related symlink skip**, on
  MSYS2 Python 3.12.7 and standard CPython 3.12.4.
- Python compilation and bundled JavaScript syntax checks passed.
- Chrome/Playwright: Scan → grouped Preview → final confirmation → Organize →
  Undo passed using new disposable workspace fixtures. Actual contents were
  checked before confirmation and after undo; collisions/directories preserved.
- Desktop/mobile screenshots match the existing interface. Browser console had
  no errors or warnings in the test workflow.
- Tracked-source/history credential-pattern scan, ignore probes, and historical
  file inventory are checked before approval. Pattern scans are not a proof of
  detecting every possible credential format.
- Windows CI for Python 3.12/3.13 uses pinned official actions, read-only
  permissions, and no persisted checkout credential. Both hosted jobs passed on
  the [initial push](https://github.com/Ankit70842/smart-download-manager/actions/runs/43510775124).
  Python 3.13 was tested in hosted CI rather than locally.
- Existing limitations remain: synchronous work, trusted idle local folders,
  bounded previews, unbounded stored journal, no physical multi-drive/power-loss
  validation, one skipped symlink test, unsupported Streamlit.

## Publication verification

The first push contained **32 commits** through
`bf1214f2495f6596782a26c56fd9bdc923d153df`: all 29 original commits and three
preparation commits. Remote/local commit sets, public visibility, default `main`,
README, MIT license, and the 48-file source tree were verified via GitHub's API.
The follow-up publication-record commit preserves that full ancestry.

The owner completed local Git Credential Manager authentication. No password or
token was pasted into chat, embedded in a remote URL, or committed to source.
Current checks use the normal credential manager without printing credentials.

No tag, release, or public demo was created. The published project remains a
local application, not a publicly hosted file-management service.
