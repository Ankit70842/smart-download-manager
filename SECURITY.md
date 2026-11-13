# Security and data safety

Smart Downloads Manager is a personal, local Windows utility. It is not a public
web service, a multi-user application, a backup system, or an antivirus tool.

## Intended use

- Run `python web_app.py` as your normal user and open the printed loopback URL.
- Never expose its HTTP port to a network, run it as administrator, or weaken
  filesystem permissions to make an operation succeed.
- Use local, idle folders. Avoid editing files or changing directory links while
  the organizer is working. Checks cannot defeat hostile concurrent filesystem
  mutation or guarantee recovery after physical storage failure.
- Downloaded files are never executed. Filename rules classify purpose; hashes
  and file identities protect move/restore operations.

The server validates Host/Origin and form tokens. Explicit confirmation, selected
destination boundaries, escaped HTML, parameterized SQL, exclusive destination
creation, and a persistent journal support safe local operation. These controls
do not isolate the app from other programs running with your own account rights.

## Private local data

`.organizer/` contains paths, hashes, settings, and undo history. Keep it local and
retain it if you need undo. It and database sidecars are ignored by Git. Runtime
fixtures, browser traces, logs, environments, secrets, and editor configuration
are excluded too. Ignore rules do not make an already tracked file private:
inspect `git ls-files` before sharing a fork or submitting a pull request.

Use generated disposable fixtures for tests. Never submit personal Downloads
files, a real journal/database, credentials, browser storage, or unredacted traces.

## Reporting a problem

For a suspected security vulnerability, use GitHub's private vulnerability
reporting feature if the repository offers it. Otherwise contact the maintainer
privately before publishing exploit details or private paths. Do not put secrets
or user data in a public issue. No guaranteed response time is offered.

For an ordinary bug, provide the Python/Windows version, exact operation/error,
and a reproduction using synthetic filenames and disposable files. If a move is
marked `review`, preserve both paths and the local journal until you understand
the failure; do not delete originals or partial files based on a guess.

The Streamlit entry point is experimental and outside the supported release.
Full threat assumptions and known limits are in the README and design notes.
