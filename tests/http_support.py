"""Isolated real HTTP server fixture, shared by dashboard regression tests."""
import http.client
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from urllib.parse import urlencode


class ServerCase(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        code = ("from pathlib import Path; import sys; from web_app import OrganizerServer; "
                "s=OrganizerServer(('127.0.0.1',0),Path(sys.argv[1])); "
                "print(s.server_port,flush=True); s.serve_forever()")
        self.process = subprocess.Popen(
            [sys.executable, "-u", "-c", code, str(self.root / "history.sqlite")],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.port = int(self.process.stdout.readline().strip())
        self.token = self.field(self.request()[1], "token")

    def tearDown(self):
        self.process.terminate()
        self.process.communicate(timeout=10)
        self.temp.cleanup()

    @staticmethod
    def field(html, name):
        return re.search(rf'name="{name}" value="([^"]+)"', html).group(1)

    def request(self, fields=None, path="/", headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("GET" if fields is None else "POST", path,
                               None if fields is None else urlencode(fields),
                               headers or {"Content-Type": "application/x-www-form-urlencoded"})
            response = connection.getresponse()
            return response.status, response.read().decode()
        finally:
            connection.close()

    def preview(self, name):
        folder = self.root / name
        folder.mkdir()
        (folder / "notes.txt").write_text(name)
        self.request({"token": self.token, "action": "preview", "folder": str(folder)})
        html = self.request()[1]
        self.request({"token": self.token, "action": "destination", "mode": "inside",
                      "plan_id": self.field(html, "plan_id")})
        html = self.request()[1]
        self.request({"token": self.token, "action": "edit", "plan_id": self.field(html, "plan_id"),
                      "edits_present": "yes", "selected_0": "yes", "category_0": "Personal"})
        return folder, self.request()[1]
