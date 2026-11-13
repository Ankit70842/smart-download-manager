"""Dependency-free browser UI. Bind only to localhost; never publish this server."""

import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import secrets
import sqlite3
import subprocess
import sys
from urllib.parse import parse_qs

from organizer.core import scan
from organizer.history import History


class OrganizerServer(HTTPServer):
    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(2)
        return connection, address

    def __init__(self, address, database):
        super().__init__(address, Handler)
        self.history = History(database)
        self.history.reconcile()
        self.token = secrets.token_urlsafe(32)
        self.plan = None
        self.plan_id = ""
        self.folder = ""
        self.message = "Start with a sample folder, then preview before moving anything."
        try:
            # USERNAME/getpass can describe the parent environment rather than
            # this process's Windows access token (as with sandbox launches).
            self.process_account = subprocess.run(
                ["whoami"], check=True, capture_output=True, text=True, timeout=2
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            self.process_account = "Unavailable (could not query OS identity)"
        self.python_executable = sys.executable

    def server_close(self):
        if hasattr(self, "history"):
            self.history.close()
        super().server_close()


class Handler(BaseHTTPRequestHandler):
    def valid_host(self):
        expected = f"127.0.0.1:{self.server.server_port}"
        if self.headers.get("Host") != expected:
            self.send_error(403, "Use the local 127.0.0.1 address printed by the app.")
            return False
        return True

    def log_message(self, *args):
        pass

    def do_GET(self):
        if not self.valid_host():
            return
        if self.path != "/":
            self.send_error(404)
            return
        body = render(self.server).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if not self.valid_host():
            return
        app = self.server
        if self.path != "/":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400)
            return
        if not 0 < length <= 16384:
            self.send_error(413)
            return
        fields = parse_qs(self.rfile.read(length).decode("utf-8", errors="replace"))
        token = fields.get("token", [""])[0]
        if not token.isascii() or not secrets.compare_digest(token, app.token):
            self.send_error(403)
            return
        action = fields.get("action", [""])[0]
        try:
            if action == "preview":
                app.plan = None
                app.plan_id = ""
                app.folder = fields.get("folder", [""])[0].strip()
                if not app.folder:
                    raise ValueError("Enter a folder path first.")
                app.plan = scan(app.folder)
                app.plan_id = secrets.token_urlsafe(24)
                app.message = f"Preview ready: {len(app.plan)} eligible files. No files moved."
            elif action == "apply":
                if app.plan is None:
                    raise ValueError("Preview files before applying.")
                if fields.get("plan_id", [""])[0] != app.plan_id:
                    raise ValueError("Preview changed in another tab; preview again before applying.")
                if fields.get("confirmed", [""])[0] != "yes":
                    raise ValueError("Confirm the preview before applying these moves.")
                batch = app.history.apply(app.plan)
                app.history.reconcile()
                rows = [r for r in app.history.rows() if r["batch"] == batch]
                count = sum(r["state"] == "moved" for r in rows)
                app.plan = None
                app.plan_id = ""
                app.message = f"Moved {count} of {len(rows)} files. Check history for skipped files."
            elif action == "undo":
                app.history.undo_latest()
                app.plan = None
                app.plan_id = ""
                app.message = "Undo attempted. Check each file's status and details in history."
            else:
                raise ValueError("Unknown action.")
        except (OSError, ValueError, sqlite3.Error) as error:
            app.message = f"Could not finish: {error}"
        self.send_response(303)
        self.send_header("Location", "/")
        self.send_header("Content-Length", "0")
        self.end_headers()


def render(app):
    def form(action, content):
        return (f'<form method="post" action="/"><input type="hidden" name="token" value="{app.token}">'
                f'<input type="hidden" name="action" value="{action}">{content}</form>')

    preview = "<p class='muted'>Your move preview will appear here.</p>"
    if app.plan is not None:
        rows = "".join(
            f"<tr><td>{escape(m.source.name)}</td><td>{escape(m.destination.parent.name)}</td>"
            f"<td>{'Conflict: skipped' if m.destination.exists() else 'Ready'}</td></tr>"
            for m in app.plan)
        preview = (f"<div class='scroll'><table><thead><tr><th>File</th><th>Move to</th><th>Status</th></tr></thead>"
                   f"<tbody>{rows}</tbody></table></div>" if rows else "<p>No eligible files found.</p>")
        if rows:
            preview += form("apply", f'<input type="hidden" name="plan_id" value="{app.plan_id}">'
                            '<label class="confirm"><input type="checkbox" name="confirmed" value="yes" required> '
                            'I reviewed this preview and approve these moves.</label>'
                            '<button>Apply these moves</button>')
    history = app.history.rows()
    history_rows = "".join(
        f"<tr><td>{escape(Path(r['source']).name)}</td><td><span class='status'>{escape(r['state'])}</span></td>"
        f"<td>{escape(r['error']) or escape(r['destination'])}</td></tr>" for r in history)
    history_html = ("<div class='scroll'><table><thead><tr><th>File</th><th>Status</th><th>Details / destination</th></tr>"
                    f"</thead><tbody>{history_rows}</tbody></table></div>" if history else
                    "<p class='muted'>No operations yet. Your history stays on this computer.</p>")
    undo = form("undo", '<button class="secondary">Undo latest available batch</button>') if any(
        r["state"] == "moved" for r in history) else ""
    folder_form = form("preview", '<label for="folder">Folder path</label>'
                       f'<input id="folder" name="folder" value="{escape(app.folder, quote=True)}" '
                       'placeholder="Paste a local folder path" required>'
                       '<button>Preview files →</button>')
    account_warning = (
        '<p>This server runs under a restricted automation account. Start '
        '<code>python web_app.py</code> from your own terminal to use your account’s folder permissions.</p>'
        if "codexsandbox" in app.process_account.casefold() else ""
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Folder Organizer</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f5f5ef;color:#20352b;font:16px/1.6 system-ui,sans-serif}}
main{{max-width:1100px;margin:48px auto;padding:0 24px}}.eyebrow{{font-size:12px;letter-spacing:2px;font-weight:700}}
h1{{font-size:clamp(32px,6vw,54px);line-height:1.1;letter-spacing:-2px;margin:18px 0}}h2{{font-size:21px;margin-top:0}}
.muted,.intro{{color:#637166}}.intro{{max-width:640px}}.grid{{display:grid;grid-template-columns:1fr 1.4fr;gap:20px;margin:24px 0}}
section{{background:white;border:1px solid #dce2d8;border-radius:16px;padding:25px;min-width:0}}
.notice{{padding:14px 18px;background:#e5eddf;border-left:4px solid #63804d;border-radius:5px;margin:28px 0}}
label{{display:block;font-weight:600}}input:not([type=checkbox]){{width:100%;padding:12px;border:1px solid #b9c5b5;border-radius:8px;margin:8px 0 15px;font:inherit}}
button{{background:#294d38;color:white;border:0;border-radius:8px;padding:12px 18px;font:inherit;cursor:pointer}}
button:hover{{background:#396549}}button:focus-visible,input:focus-visible{{outline:3px solid #a7b970;outline-offset:3px}}
.secondary{{background:#edf0e8;color:#294d38;margin-top:12px}}.confirm{{font-size:14px;font-weight:400;margin:18px 0}}
table{{border-collapse:collapse;width:100%;font-size:14px;text-align:left}}th,td{{padding:12px 8px;border-bottom:1px solid #e5e9e1;overflow-wrap:anywhere}}
th{{color:#637166;font-size:12px}}.scroll{{overflow:auto;max-height:400px}}.status{{font-weight:600}}footer{{font-size:13px;color:#637166;margin:25px 0}}
@media(max-width:720px){{.grid{{grid-template-columns:1fr}}main{{margin-top:28px}}section{{padding:18px}}.scroll table{{min-width:540px}}}}
</style></head><body><main><div class="eyebrow">A LITTLE ORDER, LOCALLY</div>
<h1>Make room for clarity.</h1><p class="intro">Turn a cluttered download folder into a place where everything is easy to find. Preview first. Organize when you're ready.</p>
<div class="notice" role="status">{escape(app.message)}</div>
<div class="grid"><section><h2>1. Choose your folder</h2>{folder_form}
<p class="muted">Top-level files only. Subfolders, dot-prefixed files, and symbolic links stay untouched.</p>
<p class="muted">Categories: Documents, Images, Videos, Audio, Archives, Code, and Other.</p></section>
<section><h2>2. Review your moves</h2>{preview}</section></div>
<section><h2>Operation history</h2>{history_html}{undo}
<p class="muted">Undo checks file contents and skips occupied original paths. Empty category folders remain. A “review” status means inspect both paths manually.</p></section>
<footer>Runs on your computer · No uploads · No automatic deletion · Keep files closed while organizing</footer>
<details><summary>Server diagnostics</summary>
<p>Process account: <code>{escape(app.process_account)}</code><br>
Python executable: <code>{escape(app.python_executable)}</code></p>
{account_warning}</details>
</main></body></html>"""


def main():
    parser = argparse.ArgumentParser(description="Run the local folder organizer")
    parser.add_argument("--port", type=int, default=8501)
    args = parser.parse_args()
    with OrganizerServer(("127.0.0.1", args.port), Path(__file__).parent / ".organizer/history.sqlite") as server:
        print(f"Open http://127.0.0.1:{server.server_port} — press Ctrl+C to stop.", flush=True)
        print(f"Process account: {server.process_account}\nPython executable: {server.python_executable}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
