# Local verification

Checks run during implementation:

- `python -m unittest discover -s tests -v`: 12 tests executed; 11 passed,
  1 skipped because this Windows account cannot create symbolic links.
- `python -m compileall -q app.py web_app.py organizer scripts`: passed.
- Real HTTP integration test: isolated localhost server, preview without changes,
  apply, undo with content verification, invalid form token, untrusted Host header,
  and HTML escaping all passed.
- Git staged whitespace checks passed at each commit.

The browser flow was verified through HTTP integration tests, not manual visual
inspection. The optional Streamlit UI was syntax-checked but could not be launched:
the installed MSYS2 Python selected source dependencies and downloads timed out.
The default browser UI and CLI use no third-party packages and were executed.

No existing user downloads were organized. Tests used generated temporary files.
GitHub repository creation, pushing, and deployment have not been performed.
