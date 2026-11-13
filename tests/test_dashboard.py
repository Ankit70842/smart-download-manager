import tests.http_support as support


class DashboardTests(support.ServerCase):
    def test_get_prefills_downloads_without_scanning_it(self):
        from pathlib import Path
        from html import escape
        html = self.request()[1]
        self.assertIn(f'value="{escape(str(Path.home() / "Downloads"), quote=True)}"', html)
        self.assertNotIn('id="folder-summary"', html)
        self.assertIn('id="change-folder"', html)

    def test_simple_scan_groups_files_and_organizes_only_after_one_final_confirmation(self):
        folder = self.root / "simple"
        folder.mkdir()
        (folder / "Code").mkdir()
        (folder / "Documents").mkdir()
        source = folder / "CN.pdf"
        source.write_text("notes")
        self.request({"token": self.token, "action": "scan", "folder": str(folder)})
        html = self.request()[1]
        self.assertIn("Review suggested folders", html)
        self.assertIn('id="folder-summary"', html)
        self.assertTrue(source.exists())
        self.request({"token": self.token, "action": "organize_review", "mode": "inside", "plan_id": self.field(html, "plan_id")})
        html = self.request()[1]
        self.assertIn("Confirm &amp; Organize", html)
        self.assertTrue(source.exists())
        self.request({"token": self.token, "action": "organize_confirm", "confirmed": "yes", "confirm_id": self.field(html, "confirm_id")})
        self.assertEqual((folder / "Studies" / "Computer Networks" / "CN.pdf").read_text(), "notes")
        self.assertFalse(source.exists())

    def test_advanced_edits_keep_the_explicit_external_destination(self):
        folder, html = self.preview("destination-edit")
        target = self.root / "external"
        target.mkdir()
        self.request({"token": self.token, "action": "edit", "plan_id": self.field(html, "plan_id"),
                      "mode": "external", "destination": str(target), "edits_present": "yes",
                      "selected_0": "yes", "category_0": "Personal"})
        self.assertIn(f'value="{target}"', self.request()[1])
        self.assertTrue((folder / "notes.txt").exists())

    def test_canceling_invalidates_the_final_confirmation_without_moving_files(self):
        folder, html = self.preview("cancel-confirm")
        self.request({"token": self.token, "action": "organize_review", "mode": "inside", "plan_id": self.field(html, "plan_id")})
        html = self.request()[1]
        old_confirmation = self.field(html, "confirm_id")
        self.request({"token": self.token, "action": "organize_cancel", "plan_id": self.field(html, "plan_id")})
        self.request({"token": self.token, "action": "organize_confirm", "confirm_id": old_confirmation, "confirmed": "yes"})
        self.assertTrue((folder / "notes.txt").exists())
        self.assertIn("confirmation is stale", self.request()[1])

    def test_empty_undo_explains_that_no_operation_is_available(self):
        self.request({"token": self.token, "action": "undo_preview"})
        self.assertIn("No matching organization", self.request()[1])

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

    def test_an_older_operation_can_be_restored_without_undoing_the_newer_one(self):
        folder = self.root / "historical"
        folder.mkdir()
        def organize(name):
            (folder / name).write_text(name)
            self.request({"token": self.token, "action": "preview", "folder": str(folder)})
            self.request({"token": self.token, "action": "destination", "mode": "inside", "plan_id": self.field(self.request()[1], "plan_id")})
            self.request({"token": self.token, "action": "apply", "confirmed": "yes", "plan_id": self.field(self.request()[1], "plan_id")})
        organize("CN.pdf")
        older = self.field(self.request()[1], "batch")
        organize("DBMS.pdf")
        self.request({"token": self.token, "action": "undo_preview", "batch": older})
        undo_id = self.field(self.request()[1], "undo_id")
        self.request({"token": self.token, "action": "undo_confirm", "undo_id": undo_id, "confirmed": "yes"})
        self.assertEqual((folder / "CN.pdf").read_text(), "CN.pdf")
        self.assertFalse((folder / "DBMS.pdf").exists())
        self.assertEqual((folder / "Studies" / "DBMS" / "DBMS.pdf").read_text(), "DBMS.pdf")
