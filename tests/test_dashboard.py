import tests.http_support as support


class DashboardTests(support.ServerCase):
    def test_browser_policy_preserves_same_origin_form_origin(self):
        import http.client
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("GET", "/")
            response = connection.getresponse()
            self.assertEqual(response.getheader("Referrer-Policy"), "same-origin")
            response.read()
        finally:
            connection.close()

    def test_scan_requires_destination_then_edits_and_confirmed_apply(self):
        folder = self.root / "smart"
        folder.mkdir()
        source = folder / "CN lecture.pdf"
        source.write_text("networks")
        self.request({"token": self.token, "action": "preview", "folder": str(folder)})
        html = self.request()[1]
        self.assertIn("Studies/Computer Networks", html)
        self.assertIn("Choose where files go", html)
        plan_id = self.field(html, "plan_id")
        self.request({"token": self.token, "action": "apply", "confirmed": "yes", "plan_id": plan_id})
        self.assertTrue(source.exists())
        self.assertIn("Choose where", self.request()[1])
        target = self.root / "target"
        target.mkdir()
        self.request({"token": self.token, "action": "destination", "plan_id": plan_id,
                      "mode": "external", "destination": str(target)})
        html = self.request()[1]
        self.request({"token": self.token, "action": "apply", "plan_id": self.field(html, "plan_id"),
                      "confirmed": "yes", "edits_present": "yes", "selected_0": "yes", "category_0": "Projects"})
        self.assertFalse(source.exists())
        self.assertEqual((target / "Projects" / source.name).read_text(), "networks")

    def test_undo_preview_and_individual_confirm_do_not_restore_other_files(self):
        folder = self.root / "undo"
        folder.mkdir()
        for name in ["CN.pdf", "DBMS.pptx"]:
            (folder / name).write_text(name)
        self.request({"token": self.token, "action": "preview", "folder": str(folder)})
        html = self.request()[1]
        self.request({"token": self.token, "action": "destination", "mode": "inside", "plan_id": self.field(html, "plan_id")})
        self.request({"token": self.token, "action": "apply", "confirmed": "yes", "plan_id": self.field(self.request()[1], "plan_id")})
        self.assertFalse((folder / "CN.pdf").exists())
        html = self.request()[1]
        # The newest row is DBMS (sorted source order); extract its public Undo File form.
        file_id = self.field(html, "file_id")
        self.request({"token": self.token, "action": "undo_preview", "file_id": file_id})
        html = self.request()[1]
        self.assertIn("Confirm restore preview", html)
        self.assertFalse((folder / "DBMS.pptx").exists())
        self.request({"token": self.token, "action": "undo_confirm", "undo_id": self.field(html, "undo_id")})
        self.assertFalse((folder / "DBMS.pptx").exists())
        self.request({"token": self.token, "action": "undo_confirm", "undo_id": self.field(html, "undo_id"), "confirmed": "yes"})
        self.assertEqual((folder / "DBMS.pptx").read_text(), "DBMS.pptx")
        self.assertFalse((folder / "CN.pdf").exists())

    def test_settings_and_correction_rules_require_explicit_approval(self):
        self.request({"token": self.token, "action": "settings_add_category", "name": "Studies/AI"})
        self.assertIn("Studies/AI", self.request()[1])
        folder, html = self.preview("correction")
        self.request({"token": self.token, "action": "correction", "plan_id": self.field(html, "plan_id"), "index": "0", "category": "Studies/AI"})
        self.assertIn("Explicitly approve", self.request()[1])
        self.assertTrue((folder / "notes.txt").exists())
        self.request({"token": self.token, "action": "correction", "plan_id": self.field(html, "plan_id"), "index": "0", "category": "Studies/AI", "approved": "yes"})
        self.request({"token": self.token, "action": "preview", "folder": str(folder)})
        self.assertIn("Rule corrected-", self.request()[1])
        self.assertTrue((folder / "notes.txt").exists())

    def test_cross_site_and_path_injection_requests_cannot_change_files(self):
        folder, html = self.preview("security")
        status, _ = self.request({"token": self.token, "action": "apply", "plan_id": self.field(html, "plan_id"), "confirmed": "yes"},
                                 headers={"Origin": "https://untrusted.example", "Content-Type": "application/x-www-form-urlencoded"})
        self.assertEqual(status, 403)
        self.assertEqual(self.request(path="/assets/../../README.md")[0], 404)
        self.request({"token": self.token, "action": "apply", "plan_id": self.field(html, "plan_id"), "confirmed": "yes",
                      "edits_present": "yes", "selected_0": "yes", "category_0": "../escape"})
        self.assertTrue((folder / "notes.txt").exists())
