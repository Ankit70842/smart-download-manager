"""Local HTTP dashboard. No framework, network service, or automatic file moves."""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import secrets
import sqlite3
import subprocess
import sys
from urllib.parse import parse_qs, urlsplit

from organizer.actions import handle
from organizer.history import History
from organizer.settings import Settings
from organizer.ui import render

ROOT = Path(__file__).resolve().parent
ASSETS = {"/assets/style.css": (ROOT / "assets/style.css", "text/css; charset=utf-8"),
          "/assets/app.js": (ROOT / "assets/app.js", "text/javascript; charset=utf-8"),
          "/favicon.ico": (ROOT / "assets/icon.svg", "image/svg+xml")}


class OrganizerServer(HTTPServer):
    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(2)
        return connection, address

    def __init__(self, address, database):
        super().__init__(address, Handler)
        self.history = History(database)
        self.history.reconcile()
        self.settings = Settings(database)
        self.token = secrets.token_urlsafe(32)
        self.plan = None
        self.plan_id = ""
        self.confirm_id = ""
        self.undo_rows = []
        self.undo_id = ""
        # Prefill only: do not stat, resolve, scan, or create this folder at startup.
        self.folder = str(Path.home() / "Downloads")
        self.message = "Ready when you are. Nothing moves until you confirm."
        try:
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
        origin = self.headers.get("Origin")
        if origin and origin != "http://" + expected:
            self.send_error(403, "Cross-site requests are not allowed.")
            return False
        return True

    def log_message(self, *args):
        pass

    def do_GET(self):
        if not self.valid_host():
            return
        path = urlsplit(self.path).path
        if path in ASSETS:
            file, content_type = ASSETS[path]
            body = file.read_bytes()
        elif path == "/":
            body = render(self.server).encode("utf-8")
            content_type = "text/html; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if not self.valid_host():
            return
        if self.path != "/":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400)
            return
        if not 0 < length <= 524288:
            self.send_error(413)
            return
        try:
            fields = parse_qs(self.rfile.read(length).decode("utf-8", errors="replace"), max_num_fields=6000)
        except ValueError:
            self.send_error(400)
            return
        token = fields.get("token", [""])[0]
        if not token.isascii() or not secrets.compare_digest(token, self.server.token):
            self.send_error(403)
            return
        try:
            handle(self.server, fields)
        except (OSError, ValueError, sqlite3.Error) as error:
            self.server.message = f"Could not finish: {error}"
        self.send_response(303)
        self.send_header("Location", "/")
        self.send_header("Content-Length", "0")
        self.end_headers()


def main():
    parser = argparse.ArgumentParser(description="Run Smart Downloads Manager locally")
    parser.add_argument("--port", type=int, default=8501)
    parser.add_argument("--database", type=Path, default=ROOT / ".organizer/history.sqlite",
                        help="Use a separate database for disposable demos/tests")
    args = parser.parse_args()
    with OrganizerServer(("127.0.0.1", args.port), args.database) as server:
        print(f"Open http://127.0.0.1:{server.server_port} — press Ctrl+C to stop.", flush=True)
        print(f"Process account: {server.process_account}\nPython executable: {server.python_executable}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
