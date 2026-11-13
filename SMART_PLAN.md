# Smart Downloads Manager upgrade

Preserve the standard-library HTTP server, legacy extension organizer API/CLI,
SQLite move journal, MIT license, and all Git commits. No real Downloads access.

1. Deterministic filename rules and persistent category/rule settings. Validate
   Windows folder names and classify ambiguity as Unsorted. No document execution
   or extraction in this version. Verify public rule/settings behavior.
2. Smart preview service: source-only scan, explicit destination roots, editable
   categories, selection, exclusions, explanations, and safe nested paths. Retain
   legacy `scan()` for CLI/experimental Streamlit compatibility.
3. Journal migration: timestamp and file identity; explicit destination boundary;
   cross-volume no-overwrite moves; previewed historical/individual undo. Preserve
   old entries, partial failure recovery, and content checks.
4. Dashboard: scan, destination choice, search/filter/sort, per-file and bulk edits,
   Apply confirmation, settings, operation/file undo confirmation, runtime status.
   Keep local-only Host/token protection; serve only bundled CSS/JS.
5. Test and review: API + HTTP tests at already-agreed boundaries; real disposable
   browser/filesystem flow; regression/security review; honest README/screenshots.

Commit each completed phase after affected tests and diff review. Do not publish,
rewrite history, automatically organize files, or modify filesystem folders when
renaming/deleting settings categories. Destination roots must be explicitly chosen;
cross-volume copies must finish and verify before removing a source.
