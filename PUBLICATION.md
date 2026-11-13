# Publication candidate — 14 November 2026

Status: prepared locally. Public repository creation and pushing require the
owner's explicit approval immediately before those actions. Neither has occurred.

## Concrete destination

- Owner: **Ankit70842** (confirmed by the connected GitHub account).
- Repository: **smart-download-manager**.
- Visibility: **public**.
- Target/default branch: **main**. The local `master` branch was renamed without
  rewriting commits. There is no configured remote yet.
- Proposed URL: `https://github.com/Ankit70842/smart-download-manager`.
- Description: `An offline-first Windows downloads manager with explainable filename rules, a simple review workflow, and safe journaled undo.`
- Topics: `python`, `windows`, `file-organizer`, `automation`, `sqlite`,
  `local-first`, `file-management`, `rule-engine`, `portfolio-project`.
- License: existing MIT, Copyright (c) 2026 Ankit Chaurasia.

The initial GitHub lookup returned 404. Recheck immediately before creating it. If
absent, create an **empty** repository without an auto-generated README, license,
or initial commit. If an existing repository is found, inspect its branches and
history before proceeding; do not overwrite or force-push unrelated history.

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
- Windows CI for Python 3.12/3.13 is configured with pinned official actions,
  read-only permissions, and no persisted checkout credential. Its hosted result
  is pending the first approved push; Python 3.13 was not tested locally.
- Existing limitations remain: synchronous work, trusted idle local folders,
  bounded previews, unbounded stored journal, no physical multi-drive/power-loss
  validation, one skipped symlink test, unsupported Streamlit.

## After approval

Create the public repository if absent, configure the credential-free HTTPS
remote URL, and perform a normal non-force push of `main` with complete history.
Verify the remote commit SHA, default branch, visibility, commit count/ancestry,
README/license, and CI status. Report the actual repository URL and final Git
status. Git CLI authentication may require a local sign-in: no saved GitHub
account was listed by Git Credential Manager during preparation. Credentials
must not be pasted into chat or embedded in a URL or repository file.

Do not create a tag, release, or public demo as part of this approval proposal.
