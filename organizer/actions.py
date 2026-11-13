"""HTTP dashboard actions. All changes require the server's form token upstream."""
import copy
import secrets
from pathlib import Path

from organizer.rules import words
from organizer.smart import preview


def value(fields, name, default=""):
    return fields.get(name, [default])[0]


def refresh(app):
    app.plan_id = secrets.token_urlsafe(24)


def require_plan(app, fields):
    if app.plan is None:
        raise ValueError("Preview files before applying.")
    if value(fields, "plan_id") != app.plan_id:
        raise ValueError("Preview changed in another tab; preview again before applying.")


def edited(app, fields):
    result = copy.deepcopy(app.plan)
    if value(fields, "edits_present") == "yes":
        settings = app.settings.load()
        for index, entry in enumerate(result.entries):
            if not entry.skip_reason:
                result.edit(index, value(fields, f"category_{index}", entry.category),
                            value(fields, f"selected_{index}") == "yes", settings)
    return result


def handle(app, fields):
    action = value(fields, "action")
    if action == "preview":
        app.plan = None
        refresh(app)
        app.folder = value(fields, "folder").strip()
        if not app.folder:
            raise ValueError("Enter a folder path first.")
        app.plan = preview(app.folder, app.settings.load())
        for entry in app.plan.entries:
            if entry.source.resolve() in app.history.protected_paths:
                entry.skip_reason = "Active application journal or sidecar"
                entry.selected = False
        eligible = sum(not entry.skip_reason for entry in app.plan.entries)
        app.message = f"Preview ready: {eligible} eligible files. No files moved. Choose where files go next."
        if app.plan.truncated:
            app.message += f" Showing the first {len(app.plan.entries)} of {app.plan.total_entries} top-level items; remaining items are not selected or processed."
    elif action == "destination":
        require_plan(app, fields)
        mode = value(fields, "mode")
        if mode not in ("inside", "external"):
            raise ValueError("Choose inside the source folder or an explicit external folder.")
        app.plan.choose_destination(app.plan.source if mode == "inside" else value(fields, "destination"))
        refresh(app)
        app.message = "Destination chosen. Review exact paths and selections before Apply."
    elif action in ("edit", "bulk", "apply"):
        require_plan(app, fields)
        candidate = edited(app, fields)
        if action == "bulk":
            category = value(fields, "bulk_category")
            for index, entry in enumerate(candidate.entries):
                if entry.selected and not entry.skip_reason:
                    candidate.edit(index, category, True, app.settings.load())
        if action == "apply":
            if candidate.destination_root is None:
                raise ValueError("Choose where files go before applying.")
            if value(fields, "confirmed") != "yes":
                raise ValueError("Confirm the preview before applying these moves.")
            moves = candidate.moves()
            if not moves:
                raise ValueError("Select at least one eligible file before Apply.")
            # Consume the plan before filesystem work so replaying a form cannot
            # retry a partially completed batch without a new preview.
            app.plan = None
            refresh(app)
            batch = app.history.apply(moves)
            app.history.reconcile()
            rows = [row for row in app.history.rows() if row["batch"] == batch]
            moved = sum(row["state"] == "moved" for row in rows)
            app.message = f"Moved {moved} of {len(rows)} files. Operation {batch[:8]}. Check history for skipped files."
        else:
            app.plan = candidate
            refresh(app)
            app.message = "Preview edits saved. No files moved and no classification rules were saved."
    elif action == "undo_preview":
        file_id = value(fields, "file_id")
        batch = value(fields, "batch")
        if file_id and batch:
            raise ValueError("Choose one file or one operation.")
        app.undo_rows = app.history.preview_undo(batch=batch or None, file_id=int(file_id) if file_id else None)
        app.undo_id = secrets.token_urlsafe(24)
        app.message = "Restore preview ready. Nothing restored until you confirm."
    elif action in ("undo_confirm", "undo"):
        # Even the former immediate endpoint now requires a current restore preview.
        if not app.undo_rows or value(fields, "undo_id") != app.undo_id:
            raise ValueError("Preview an undo operation before confirming restoration.")
        if value(fields, "confirmed") != "yes":
            raise ValueError("Confirm the restore preview first.")
        ids = [row["id"] for row in app.undo_rows if row["can_undo"]]
        app.undo_rows = []
        app.undo_id = ""
        for row_id in ids:
            app.history.undo_file(row_id)
        restored = sum(row["state"] == "undone" for row in app.history.rows() if row["id"] in ids)
        app.plan = None
        refresh(app)
        app.message = f"Undo attempted: restored {restored} of {len(ids)} eligible files. Check history for any skipped files."
    elif action.startswith("settings_") or action == "correction":
        if action == "settings_add_category":
            app.settings.add_category(value(fields, "name"))
        elif action == "settings_rename_category":
            app.settings.rename_category(value(fields, "old"), value(fields, "name"))
        elif action == "settings_delete_category":
            if value(fields, "confirmed") != "yes":
                raise ValueError("Confirm deleting the category and its rules from settings.")
            app.settings.delete_category(value(fields, "name"))
        elif action == "settings_save_rule":
            app.settings.save_rule(value(fields, "rule_id"), value(fields, "category"),
                                   value(fields, "keywords").split(","), value(fields, "extensions").split(","),
                                   int(value(fields, "priority", "100")))
        elif action == "settings_delete_rule":
            if value(fields, "confirmed") != "yes":
                raise ValueError("Confirm deleting this rule.")
            app.settings.delete_rule(value(fields, "rule_id"))
        elif action == "correction":
            require_plan(app, fields)
            if value(fields, "approved") != "yes":
                raise ValueError("Explicitly approve saving this filename as a rule.")
            index = int(value(fields, "index", "-1"))
            if not 0 <= index < len(app.plan.entries) or app.plan.entries[index].skip_reason:
                raise ValueError("Choose an eligible preview file.")
            entry = app.plan.entries[index]
            app.settings.save_rule("corrected-" + secrets.token_hex(4), value(fields, "category", entry.category),
                                   [words(Path(entry.source).stem)], [], 200)
        else:
            raise ValueError("Unknown settings action.")
        app.plan = None
        refresh(app)
        app.message = "Settings saved. Existing folders and files were not changed. Scan again to use the new rules."
    else:
        raise ValueError("Unknown action.")
