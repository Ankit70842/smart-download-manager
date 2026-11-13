"""Regression tests through the public HTTP interface."""

import http.client
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from urllib.parse import urlencode


class WebReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
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

    def request(self, fields=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("GET" if fields is None else "POST", "/",
                               None if fields is None else urlencode(fields),
                               {"Content-Type": "application/x-www-form-urlencoded"})
            response = connection.getresponse()
            return response.status, response.read().decode()
        finally:
            connection.close()

    def preview(self, name):
        folder = self.root / name
        folder.mkdir()
        (folder / "notes.txt").write_text(name)
        self.request({"token": self.token, "action": "preview", "folder": str(folder)})
        return folder, self.request()[1]

    def test_old_tab_cannot_apply_another_tabs_preview(self):
        first, first_html = self.preview("first")
        second, _ = self.preview("second")
        # Submit the form that the first tab actually received.
        fields = {"token": self.token, "action": "apply", "confirmed": "yes",
                  "plan_id": self.field(first_html, "plan_id")}
        self.request(fields)
        self.assertTrue((first / "notes.txt").exists())
        self.assertTrue((second / "notes.txt").exists(), "A stale form moved files from another preview")
        self.assertIn("Preview changed", self.request()[1])
