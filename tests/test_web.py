"""Real HTTP integration checks with an isolated server and history database."""

import http.client
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from urllib.parse import urlencode


class WebTests(unittest.TestCase):
    def test_preview_apply_undo_and_request_protection(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "downloads"
            folder.mkdir()
            source = folder / "notes.txt"
            source.write_text("important notes")
            code = ("from pathlib import Path; import sys; from web_app import OrganizerServer; "
                    "s=OrganizerServer(('127.0.0.1',0),Path(sys.argv[1])); "
                    "print(s.server_port,flush=True); s.serve_forever()")
            process = subprocess.Popen([sys.executable, "-u", "-c", code, str(root / "history.sqlite")],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                port = int(process.stdout.readline().strip())

                def request(method, fields=None):
                    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                    try:
                        connection.request(method, "/", urlencode(fields or {}),
                                           {"Content-Type": "application/x-www-form-urlencoded"})
                        response = connection.getresponse()
                        return response.status, response.read().decode()
                    finally:
                        connection.close()

                status, html = request("GET")
                self.assertEqual(status, 200)
                self.assertIn("Make room for clarity", html)
                hostile = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                hostile.request("GET", "/", headers={"Host": "untrusted.example"})
                response = hostile.getresponse()
                self.assertEqual(response.status, 403)
                response.read()
                hostile.close()
                token = re.search(r'name="token" value="([^"]+)"', html).group(1)
                self.assertEqual(request("POST", {"action": "apply"})[0], 403)
                self.assertTrue(source.exists())
                request("POST", {"token": token, "action": "preview", "folder": str(folder)})
                html = request("GET")[1]
                self.assertIn("notes.txt", html)
                self.assertIn("Apply these moves", html)
                plan_id = re.search(r'name="plan_id" value="([^"]+)"', html).group(1)
                self.assertTrue(source.exists())
                request("POST", {"token": token, "action": "destination", "mode": "inside", "plan_id": plan_id})
                plan_id = re.search(r'name="plan_id" value="([^"]+)"', request("GET")[1]).group(1)
                request("POST", {"token": token, "action": "apply", "plan_id": plan_id,
                                 "confirmed": "yes", "edits_present": "yes", "selected_0": "yes", "category_0": "Personal"})
                self.assertFalse(source.exists())
                self.assertIn("Moved 1 of 1", request("GET")[1])
                request("POST", {"token": token, "action": "undo_preview"})
                undo_id = re.search(r'name="undo_id" value="([^"]+)"', request("GET")[1]).group(1)
                self.assertFalse(source.exists(), "Undo preview must not restore files")
                request("POST", {"token": token, "action": "undo_confirm", "undo_id": undo_id, "confirmed": "yes"})
                self.assertEqual(source.read_text(), "important notes")
                self.assertIn("undone", request("GET")[1])
                request("POST", {"token": token, "action": "preview", "folder": "<script>"})
                html = request("GET")[1]
                self.assertNotIn("<script>", html)
                self.assertIn("&lt;script&gt;", html)
            finally:
                process.terminate()
                process.communicate(timeout=10)
