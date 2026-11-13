"""Regression tests through the public HTTP interface."""
from pathlib import Path
import socket
import subprocess
import sys
import tests.http_support as support


class WebReviewTests(support.ServerCase):
    def test_old_tab_cannot_apply_another_tabs_preview(self):
        first, first_html = self.preview("first")
        second, _ = self.preview("second")
        fields = {"token": self.token, "action": "apply", "confirmed": "yes",
                  "plan_id": self.field(first_html, "plan_id")}
        self.request(fields)
        self.assertTrue((first / "notes.txt").exists())
        self.assertTrue((second / "notes.txt").exists())
        self.assertIn("Preview changed", self.request()[1])

    def test_non_ascii_form_token_is_rejected_without_dropping_connection(self):
        status, _ = self.request({"token": "invalid-\u2603", "action": "apply"})
        self.assertEqual(status, 403)
        self.assertEqual(self.request()[0], 200)

    def test_apply_requires_explicit_confirmation(self):
        folder, html = self.preview("confirmation")
        self.request({"token": self.token, "action": "apply", "plan_id": self.field(html, "plan_id")})
        self.assertTrue((folder / "notes.txt").exists())
        self.assertIn("Confirm the preview", self.request()[1])

    def test_server_diagnostics_identify_actual_process_account_and_interpreter(self):
        _, html = self.request()
        self.assertIn("Server diagnostics", html)
        self.assertIn("Process account", html)
        self.assertIn(str(Path(sys.executable)), html)
        self.assertIn(subprocess.check_output(["whoami"], text=True).strip(), html)

    def test_incomplete_request_cannot_block_the_local_server_indefinitely(self):
        stalled = socket.create_connection(("127.0.0.1", self.port), timeout=5)
        try:
            stalled.sendall((f"POST / HTTP/1.0\r\nHost: 127.0.0.1:{self.port}\r\n"
                             "Content-Length: 100\r\n\r\ntoken=").encode())
            self.assertEqual(self.request()[0], 200)
        finally:
            stalled.close()
