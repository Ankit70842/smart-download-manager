# Final quality review — 13 November 2026

## Publication follow-up — 14 November 2026

The current code, path/transfer/journal checks, rules/settings, HTTP protections,
test isolation, and asset handling were reviewed again. No newly confirmed
blocking runtime bug or security defect was found within the documented local,
trusted-idle-filesystem scope. The simple interface and runtime source are
unchanged. All 49 tests completed with one known permission skip, and the real
disposable browser/filesystem flow passed again.

Publication gaps addressed in focused commits: broader private-file exclusions,
SECURITY.md, an official-action-SHA-pinned read-only Windows CI workflow, README
setup/stack/structure, and a concrete owner/repository/main-branch proposal. CI is
not claimed to have run on GitHub before publication. Remote creation/push remain
pending explicit approval, and local GitHub sign-in may be needed for Git push.

Source/history scanning checks tracked artifacts rather than trusting ignore
rules alone. No local database, user Downloads content, credentials, generated
test files, or browser traces are intended for upload. Existing author metadata
and all 29 earlier commits are preserved. Remaining limits below are unchanged.

## Simplified UI review (latest)

Main controls are reduced to Scan Downloads → grouped folder review → Organize.
The default Downloads path is computed without reading it. A single final button
confirms the server-held plan; changing/canceling it invalidates the confirmation.
The existing journal, overwrite protection, file checks, and undo protections are
retained. Power controls and technical IDs are collapsed rather than removed.

Confirmed regressions were fixed test-first: existing category directories are
no longer file suggestions; medium-confidence files are not auto-selected; saving
advanced edits retains the chosen external destination. Real browser/filesystem
checks proved no movement occurred before confirmation and complete restoration
afterward. 49 tests passed except one permission-related symlink skip. Details are
in VERIFICATION.md; older review records below are historical.

## Smart Downloads Manager review (previous milestone)

The supported UI is now the smart dashboard; older sections below are historical.
The HTTP server and journal were extended in focused commits, not replaced by a
framework. The MIT license and all existing Git history remain intact.

### Confirmed upgrade findings, reproduced and fixed

- **Medium: readable Windows files can deny delete sharing.** A failing real-handle
  regression led to a non-destructive read/delete access probe in preview and Apply.
  No administrator access, security disabling, or ACL changes are used.
- **Medium: no-referrer conflicted with strict Origin checking.** Chrome sent
  `Origin: null`, causing same-origin forms to fail. Header regression + browser
  reproduction verified the fix: `same-origin` referrer policy, strict Host/Origin
  checks retained. Cross-site and null-origin submissions remain rejected.
- **Low: search included every dropdown option.** Browser search matched all
  categories for every row. Search now uses filename, chosen category, and reason;
  the same browser regression passed afterward.
- **Medium: source of truth needs protection.** The active journal and sidecars
  are explicitly excluded from scanning/moves, beyond ordinary lock detection.
- **Low: Unicode Windows device aliases.** `COM¹.txt` was accepted as a category;
  a failing name test led to normalized reserved-name checking.
- **Low: large preview form growth.** A visible 1,000-entry cap bounds submitted
  preview controls. Remaining entries are explicitly not processed.
- **Low: migration test leaked a SQLite connection on Windows.** The fixture now
  explicitly closes its database; the complete suite passes without that failure.

### Bug review coverage

| Category | Assessment |
|---|---|
| AI patterns | Public API/HTTP/browser tests; rule labels are not AI probabilities; no invented document extraction |
| Errors/resilience | Per-file failures preserved; verified partial-copy recovery; explicit locked/incomplete-file reasons |
| State/integrity | Additive journal migration, identity + hash checks, explicit roots, settings transactions, partial/idempotent undo |
| Concurrency | Existing operation lock retained; stale preview/restore IDs rejected; synchronous requests by design |
| Resources | File handles closed; bounded subprocess/socket/body operations; test fixture leak fixed |
| APIs/integrations | Updated tests reflect required destination and restore preview; legacy extension CLI retained |
| Performance | 1,000 preview entries, 50 rendered operations; hashing remains synchronous and journal grouping reads full history |
| Configuration | Normal-user process identity visible; no third-party runtime dependencies for dashboard |
| Tests | 43 tests, one real-symlink skip; browser + filesystem verification; EXDEV fault injection rather than physical-drive claim |
| Documentation | README, architecture, browser instructions, real screenshots, limitations, and metadata updated |

### Security review coverage

| Category | Assessment |
|---|---|
| Dependencies | Standard-library dashboard; local Playwright audited separately; Streamlit remains unsupported/unlocked |
| Secrets | Tracked source/history pattern scan and artifact inventory; runtime DBs, logs, and fixtures ignored |
| Access/CSRF | Loopback bind, exact Host/Origin, unpredictable token, stale-form protection, explicit Apply/restore/rule approval |
| Injection | Escaped HTML, bound SQL values, fixed asset allowlist; path/category validation and no file execution |
| Configuration | Same-origin JS/CSS/images only; no inline scripts, no eval, bounded request parse; local-only server |
| Infrastructure | No hosting/container/cloud surface added; native access probes do not change permissions |
| Code | Exclusive link/copy, hash verification, identity recorded before unlink; trusted-idle filesystem assumption explicit |
| AI/agent | No runtime AI/prompt/execution surface; no real Downloads access during development or verification |
| CI/CD | No remote actions or workflows added; no fabricated CI evidence |
| Governance | MIT preserved; no history rewrite, repository creation, push, tag, release, or public deployment |

Remaining limitations: physical multi-drive/power-loss coverage, true adversarial
filesystem races, skipped symlink creation case, no document extraction, no
background watcher/measured progress, no arbitrary per-file external roots, and
unverified optional Streamlit. These are disclosed rather than called complete.

---

## Follow-up: Apply permission failure

**Medium — configuration/error diagnosis, confirmed and fixed.** The server had
been launched as `CodexSandboxOffline`, using MSYS2 Python, while the successful
manual checks ran as Ankit. `OrganizerTest` granted the sandbox group read/execute
access and Ankit full control. Journal errors pointed to `parent.mkdir(exist_ok=True)`
for category directories, before hard-link creation or source removal. Destination
paths were the expected children (`Documents` and `Code`) of the selected folder.

The earlier automation launch, not a different Python implementation, caused this
permissions mismatch. The normal-account restart intentionally kept the same
interpreter to isolate the variable. No ACL changes, admin requirement, hard-link
fallback, or overwrite-policy relaxation was introduced.

New public-boundary regressions first failed, then passed: denied category creation
now includes the operation and destination while preserving the source; HTTP
diagnostics report the OS identity and interpreter. Identity uses `whoami` rather
than inherited environment usernames: `getpass.getuser()` incorrectly returned
Ankit for the sandbox process during diagnosis. A restricted-account warning and
normal-terminal instructions make the operational issue visible.

Live HTTP reproduction used only newly generated files in a unique child of
`OrganizerTest`: sandbox Apply moved 0/3 and preserved every source; after restart
under Ankit, Preview → Apply (3/3) → Undo restored all bytes. Existing test files
and Downloads were not modified. The full suite now has 22 tests: 21 passed and
one real-symlink permission skip. Existing history was retained. No remote action.

The remaining categories were checked against the small change: parameterized
journaling, operation lock, no-overwrite transfer, recovery states, and connection
cleanup remain intact; diagnostics run once with a bounded subprocess timeout and
no shell. Existing performance, optional-dependency, and symlink-test limits below
are unchanged.

---

Scope: full bug and security category review of the local application and tracked
history on branch `master`. Agreed test boundaries: public organizer API with real
temporary files, and HTTP/browser interactions. Confirmed fixes used failing
regression tests before implementation. No remote actions were authorized or taken.

## Result

Ready to share as a **local portfolio utility using the default browser UI or CLI**
with the documented limitations. No unresolved Critical or High findings were
identified in that scope. This is not approval for public web deployment or a claim
of safety under hostile concurrent filesystem changes. Streamlit remains an
experimental, unverified frontend. Choose a license before presenting the project
as reusable open-source software; no license has been selected automatically.

## Confirmed findings and fixes

| Severity | Finding / location | Risk | Fix and evidence |
|---|---|---|---|
| Medium | Stale file plan — `organizer/core.py`, `History.apply` | A replacement file could be moved without previewing it | Capture and compare file identity, size, and modification timestamp; replaced-file regression failed then passed |
| Medium | Shared preview across tabs — `web_app.py` | An old form could organize a different folder | Bind Apply to the displayed preview ID; stale-tab HTTP regression failed then passed |
| Medium | Partial undo status — `History.undo_latest` | Both hard-link names existed but history incorrectly remained eligible as `moved` | Preserve `undoing` and reconcile ambiguous paths to `review`; filesystem-failure regression failed then passed |
| Medium | Undo recovery trusted changed contents — `History._reconcile` | Recovery could falsely declare restoration successful | Verify restored regular file, canonical parent, and SHA-256; restart regression failed then passed |
| Low | Failure explanation discarded — `History._reconcile` | Unsupported filesystem/permission diagnosis was replaced with a generic message | Preserve the original operation error during reconciliation |
| Low | Non-ASCII form token — `Handler.do_POST` | `compare_digest` raised and dropped the response | Reject non-ASCII tokens with 403; malformed-token HTTP regression failed then passed |
| Medium | Confirmation enforced only by HTML — `Handler.do_POST` | A direct POST could bypass the checkbox | Require `confirmed=yes` on the server; confirmation regression failed then passed |
| Low | Incomplete request blocked single server — `OrganizerServer` | One stalled local client prevented normal requests indefinitely | Two-second socket inactivity timeout; incomplete-body regression failed then passed |
| Low | Mobile history became unreadable — `render` CSS | Status and filenames wrapped into fragments | Scrollable tables with minimum width on narrow screens; Playwright text-line regression failed then passed |
| Low | CLI test used real application journal — `tests/test_cli.py` | Tests could reconcile a user's existing history | Add CLI `--database`, isolate tests, and verify a full subprocess apply/undo round trip |
| Low | Recovery test mocked the journal — `tests/test_history.py` | Test depended on an internal implementation detail | Inject interruption at the filesystem boundary and reopen through the public API |
| Low | README described partially different UI | Setup and button labels were misleading | Identify built-in HTTP UI, exact labels, observed installation failure, and optional frontend status |

## Bug review: all categories

| Category | Assessment |
|---|---|
| 1. AI-generated patterns | Reviewed every application module; strengthened misleading recovery test and server validation |
| 2. Error handling | Fixed malformed-token response and retained original filesystem error; operations preserve files on ambiguity |
| 3. State/data integrity | Fixed stale plans and interrupted undo; collision, missing source, and occupied undo path tests pass |
| 4. Concurrency | Existing cross-process SQLite operation lock verified; fixed indefinitely stalled socket reads; external races remain out of scope |
| 5. Resources | Files, SQLite, and HTTP test connections close; history remains unbounded (Low, open) |
| 6. API/integration | HTTP form contract tested; no external API or webhook integration |
| 7. Performance | Full journal loading and synchronous file hashing can slow large workloads (Low, open); add pagination/background work if needed |
| 8. Configuration | Verified both interpreters and actual running command; Streamlit environment remains unresolved (experimental) |
| 9. Tests | Fixed CLI journal isolation and internal mock; Windows real-symlink coverage skipped due permissions |
| 10. Maintainability | README and verification records updated; server-rendered template is small enough for current scope |

## Security review: all categories

| Category | Assessment |
|---|---|
| 1. Supply chain | Default application has no third-party runtime packages. Local Playwright npm audit: zero findings. Optional unpinned Streamlit environment has no complete transitive audit (Low, open); resolve/pin/audit before supporting it |
| 2. Secrets | Deterministic pattern scan of tracked files and historical blobs found no candidates. No database, credentials, or runtime downloads tracked. External conversation logs were outside this repo audit |
| 3. Authentication/access | Single-user local tool, no account isolation. Random form token, exact Host validation, server confirmation, and stale-form rejection checked. Other local processes are trusted |
| 4. Input/injection | HTML output escaped; SQL parameterized; no user-controlled shell execution, deserialization, or outbound requests. Malformed-token fix verified |
| 5. Configuration | Main entry binds 127.0.0.1, no file-serving endpoint. CSP, no-store, and frame denial present. Additional response headers are a Low defense-in-depth opportunity; public hosting unsupported |
| 6. Infrastructure | No Docker, cloud, exposed database port, or deployment files. Local journal contains paths and should remain private |
| 7. Security-relevant code | Secure token randomness and SHA-256 fingerprints; no eval/pickle/shell=True. Filesystem checks do not eliminate hostile check/use races; use trusted, idle local folders |
| 8. AI/agent threats | No runtime AI integration, prompt processing, or model-generated commands. Review fixtures treated as data. No agent settings changed or remote publication attempted |
| 9. CI/CD | No existing workflows or remote pipeline to audit; not configured (Info). Add automated tests when publishing if desired |
| 10. Governance | No remote or branch protection to inspect. License unselected (Info); preserve incremental history and obtain explicit publication approval |

The skill's referenced secret-scanner and branch-protection scripts were not
present. A review-local deterministic scanner was used instead. No account-wide
agent permissions or unrelated conversation logs were audited. These limitations
prevent treating this as an account-wide security attestation.

## Actual UI and Streamlit diagnosis

Observed running command: MSYS2 `python.exe web_app.py`. The UI is handwritten
HTML/CSS with Python `http.server`, not a third-party UI framework. `app.py` is a
separate Streamlit entry point and was only syntax-checked.

PATH selects MSYS2 Python 3.12.7, platform `mingw_x86_64_ucrt_gnu`. The project
virtual environment lists pip only. Standard CPython 3.12.4 exists separately and
has no global Streamlit installation. Earlier pip attempts failed first on sandbox
socket restrictions, then on a read timeout downloading NumPy source. MSYS2's
[official Python documentation](https://www.msys2.org/docs/python/) confirms why
standard binary C-extension wheels cannot be reused. No compiler failure was
actually observed. Use a new standard-CPython environment for the optional frontend;
do not repurpose the existing MSYS2 environment.

## Remaining work and release boundary

- Keep use local and single-user. Same-volume hard-link support is required.
- Do not concurrently edit files with another application. Preview signatures are
  change detectors, not protection against a malicious process preserving metadata.
- Ambiguous `review` states require manual inspection. No automatic deletion or
  recovery guess is appropriate; a future guided resolution screen could help.
- Real Windows symlink coverage remains skipped. Run it under an account with
  permission before claiming broad link/junction compatibility.
- Large histories and long-running hashes remain synchronous/unbounded; add
  pagination and progress workers if larger-scale usage is required.
- Optional Streamlit has no verified dependency environment or execution evidence.
  Keep it experimental, or resolve, pin, audit, and test it before supporting it.
- Select a license and explicitly approve the destination/visibility before GitHub
  publication. No repository creation, push, or public deployment has occurred.

See [VERIFICATION.md](VERIFICATION.md) for executed checks. Pattern scans and tests
provide evidence for the tested cases, not proof that every possible bug is absent.
