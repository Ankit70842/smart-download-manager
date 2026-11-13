"""Server-rendered dashboard. All paths, settings, and error text are escaped."""
from collections import defaultdict
from html import escape
from pathlib import Path


def h(value):
    return escape(str(value), quote=True)


def options(categories, selected=""):
    return "".join(f'<option value="{h(c)}" {"selected" if c == selected else ""}>{h(c)}</option>' for c in categories)


def form(app, action, content, extra=""):
    return (f'<form method="post" action="/" {extra}><input type="hidden" name="token" value="{h(app.token)}">'
            f'<input type="hidden" name="action" value="{h(action)}">{content}</form>')


def button(text, secondary=False):
    return f'<button class="{"secondary" if secondary else ""}">{h(text)}</button>'


def render_settings(app, settings):
    cats = settings["categories"]
    add = form(app, "settings_add_category", '<label>New category path<input name="name" required placeholder="Studies/Distributed Systems"></label>' + button("Create category", True))
    rename = form(app, "settings_rename_category", f'<label>Category to rename<select name="old">{options([c for c in cats if c != "Unsorted"])}</select></label><label>New category path<input name="name" required></label>' + button("Rename category", True))
    delete = form(app, "settings_delete_category", f'<label>Delete category<select name="name">{options([c for c in cats if c != "Unsorted"])}</select></label><label class="checkbox"><input type="checkbox" name="confirmed" value="yes" required>Remove this category, nested categories, and their rules from settings only.</label>' + button("Delete category", True))
    def rule_form(rule):
        content = f'''<div class="form-grid"><label>Rule ID<input name="rule_id" value="{h(rule.get('id',''))}" required maxlength="80"></label>
        <label>Category<select name="category">{options(cats, rule.get('category',''))}</select></label>
        <label>Keywords (comma separated)<input name="keywords" value="{h(', '.join(rule.get('keywords',[])))}" placeholder="lecture, syllabus"></label>
        <label>Extensions (optional)<input name="extensions" value="{h(', '.join(rule.get('extensions',[])))}" placeholder="pdf, pptx"></label>
        <label>Priority<input type="number" name="priority" min="-1000" max="1000" value="{h(rule.get('priority',100))}" required></label></div>{button('Save rule', True)}'''
        return form(app, "settings_save_rule", content)
    rule_rows = []
    for rule in settings["rules"]:
        delete_rule = form(app, "settings_delete_rule", f'<input type="hidden" name="rule_id" value="{h(rule["id"])}"><label class="checkbox"><input type="checkbox" name="confirmed" value="yes" required>Confirm deleting this rule.</label>' + button("Delete rule", True))
        rule_rows.append(f'<details class="rule"><summary>{h(rule["id"])} <span class="muted">→ {h(rule["category"])} · priority {rule["priority"]}</span></summary>{rule_form(rule)}{delete_rule}</details>')
    return f'<section id="settings"><span class="step">MAKE IT YOURS</span><h2>Categories & rules</h2><p class="muted">Settings affect future previews only. Renaming or deleting categories never changes existing folders on disk. Higher priority wins; tied rules pointing to different categories require review.</p><details><summary>Manage categories ({len(cats)})</summary><div class="form-grid">{add}{rename}{delete}</div></details><details><summary>Create a classification rule</summary>{rule_form({})}</details><details><summary>Edit existing rules ({len(settings["rules"])})</summary>{"".join(rule_rows)}</details></section>'


def folder_summary(plan):
    groups = defaultdict(list)
    for entry in plan.entries:
        if entry.selected and not entry.skip_reason and not entry.status.startswith("Conflict"):
            groups[entry.category].append(entry)
    cards = []
    for category, entries in sorted(groups.items()):
        samples = ", ".join(entry.source.name for entry in entries[:2])
        if len(entries) > 2:
            samples += f" + {len(entries) - 2} more"
        cards.append(f'<li><span class="folder-icon" aria-hidden="true">▱</span><div><strong>{h(category)}</strong><small>{h(samples)}</small></div><span class="file-count">{len(entries)} {"file" if len(entries) == 1 else "files"}</span></li>')
    return '<ul id="folder-summary" class="folder-summary">' + ("".join(cards) or '<li>No files selected yet. Open Edit Details to choose files.</li>') + '</ul>'


def file_details(app, settings):
    rows = []
    for index, entry in enumerate(app.plan.entries):
        disabled = "disabled" if entry.skip_reason else ""
        rows.append(f'''<tr class="file-row" data-name="{h(entry.source.name.casefold())}" data-category="{h(entry.category)}" data-status="{h(entry.status)}">
        <td><input type="checkbox" name="selected_{index}" value="yes" aria-label="Select {h(entry.source.name)}" {"checked" if entry.selected else ""} {disabled}></td>
        <td><strong>{h(entry.source.name)}</strong><small>{h(entry.source.suffix or 'No extension')}</small><details class="path"><summary>Source path</summary><code>{h(entry.source)}</code></details></td>
        <td><select name="category_{index}" aria-label="Category for {h(entry.source.name)}" {disabled}>{options(settings['categories'], entry.category)}</select></td>
        <td><code>{h(entry.destination or 'Choose where files go')}</code></td>
        <td><span class="badge">{h(entry.confidence)}</span><small>{h(entry.skip_reason or entry.reason)}</small></td><td>{h(entry.status)}</td></tr>''')
    return f'''<details id="edit-details"><summary>Edit Details <span class="muted">— files, search, and bulk actions</span></summary>
        <input type="hidden" name="edits_present" value="yes">
        <div class="toolbar"><label>Search files<input type="search" id="search" placeholder="Filename, topic, or reason…"></label>
        <label>Category filter<select id="category-filter"><option value="">All categories</option>{options(settings['categories'])}</select></label>
        <label>Sort by<select id="sort"><option value="name">Filename</option><option value="category">Category</option><option value="status">Status</option></select></label></div>
        <div class="actions compact"><button type="button" class="text-button" id="select-visible">Select visible</button><button type="button" class="text-button" id="deselect-visible">Deselect visible</button><span class="muted">Filtering hides rows, not selections.</span></div>
        <div class="table-scroll"><table id="file-table"><thead><tr><th>Select</th><th>Filename / source</th><th>Category</th><th>Exact destination</th><th>Confidence / reason</th><th>Status</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
        <div class="bulk"><label>Bulk category<select name="bulk_category">{options(settings['categories'])}</select></label><button name="action" value="bulk" class="secondary">Update selected categories</button><button name="action" value="edit" class="secondary">Save preview edits</button></div></details>'''


def correction_form(app, settings):
    if app.plan is None:
        return ""
    choices = "".join(f'<option value="{i}">{h(e.source.name)}</option>' for i, e in enumerate(app.plan.entries) if not e.skip_reason)
    return '<details><summary>Save a filename correction as a rule</summary>' + form(app, "correction", f'''<input type="hidden" name="plan_id" value="{h(app.plan_id)}"><p>No rules are learned automatically. This saves the chosen filename stem at priority 200.</p>
        <label>File<select name="index">{choices}</select></label><label>Future category<select name="category">{options(settings['categories'])}</select></label>
        <label class="checkbox"><input type="checkbox" name="approved" value="yes" required>I approve saving this filename keyword as a new rule.</label>{button('Save filename rule')}''') + '</details>'


def render_preview(app, settings):
    plan = app.plan
    if plan is None:
        return '<section id="preview" class="quiet-empty"><span class="step">2 · REVIEW SUGGESTED FOLDERS</span><p>Your suggested folders will appear here after a scan.</p></section>'
    if app.confirm_id:
        selected = [e for e in plan.entries if e.selected and not e.skip_reason]
        paths = "".join(f'<tr><td><code>{h(e.source)}</code></td><td><code>{h(e.destination)}</code></td></tr>' for e in selected)
        confirm = form(app, "organize_confirm", f'<input type="hidden" name="confirm_id" value="{h(app.confirm_id)}"><input type="hidden" name="confirmed" value="yes">' + button("Confirm & Organize"))
        back = form(app, "organize_cancel", f'<input type="hidden" name="plan_id" value="{h(app.plan_id)}">' + button("Back to review", True))
        return f'<section id="preview"><span class="step">3 · ORGANIZE</span><h2>Ready to organize {len(selected)} {"file" if len(selected) == 1 else "files"}?</h2><p>Move the selected files into these folders under:</p><p class="root-path"><code>{h(plan.destination_root)}</code></p>{folder_summary(plan)}<details><summary>View exact file paths</summary><div class="table-scroll"><table><thead><tr><th>From</th><th>To</th></tr></thead><tbody>{paths}</tbody></table></div></details><p class="muted">Existing files will never be overwritten. Undo remains available.</p><div class="actions">{confirm}{back}</div></section>'
    root = plan.destination_root
    external = root is not None and root != plan.source
    selected = sum(e.selected and not e.skip_reason and not e.status.startswith("Conflict") for e in plan.entries)
    excluded = len(plan.entries) - selected
    ignored = f" {plan.ignored_directories} existing folders left untouched." if plan.ignored_directories else ""
    return f'''<section id="preview"><span class="step">2 · REVIEW SUGGESTED FOLDERS</span><h2>Review suggested folders</h2>
        <p class="muted">{selected} files ready · {excluded} left out.{ignored} Only safe, high-confidence suggestions start selected.</p>
        <form method="post" action="/" id="preview-form"><input type="hidden" name="token" value="{h(app.token)}"><input type="hidden" name="plan_id" value="{h(app.plan_id)}">
        {folder_summary(plan)}<fieldset class="destination-picker"><legend>Choose where files go</legend>
        <div class="destination-options"><label class="choice"><input type="radio" name="mode" value="inside" {"" if external else "checked"}><span>Keep inside {h(plan.source.name)}</span></label>
        <label class="choice"><input type="radio" name="mode" value="external" {"checked" if external else ""}><span>Another folder</span></label></div>
        <label class="destination-path">Destination folder<input name="destination" placeholder="Paste an existing folder path" value="{h(root if external else '')}"></label></fieldset>
        {file_details(app, settings)}<div class="organize-bar"><button name="action" value="organize_review">Organize</button><span class="muted">You'll confirm once before anything moves.</span></div></form></section>'''


def render_restore(app):
    if not app.undo_rows:
        return ""
    eligible = sum(row["can_undo"] for row in app.undo_rows)
    rows = "".join(f'<tr><td><code>{h(r["destination"])}</code></td><td><code>{h(r["source"])}</code></td><td>{h(r["undo_reason"])}</td></tr>' for r in app.undo_rows)
    confirm = form(app, "undo_confirm", f'<input type="hidden" name="undo_id" value="{h(app.undo_id)}"><input type="hidden" name="confirmed" value="yes">' + button("Confirm restore"))
    return f'<section class="restore"><h2>Confirm restore preview</h2><p>{eligible} files can be safely restored. Each will be checked again before undo.</p><details><summary>Review files and restore paths</summary><div class="table-scroll"><table><thead><tr><th>From</th><th>Restore to</th><th>Safety check</th></tr></thead><tbody>{rows}</tbody></table></div></details>{confirm}</section>'


def render_history(app):
    groups = defaultdict(list)
    for row in app.history.rows():
        groups[row["batch"]].append(row)
    operations = []
    for batch, items in list(groups.items())[:50]:
        count = sum(row["state"] == "moved" for row in items)
        cells = []
        for row in items:
            undo = form(app, "undo_preview", f'<input type="hidden" name="file_id" value="{row["id"]}">' + button("Undo file", True)) if row["state"] == "moved" else ""
            cells.append(f'<tr><td><strong>{h(Path(row["source"]).name)}</strong><small>Original: {h(row["source"])}</small><small>Destination: {h(row["destination"])}</small></td><td>{h(row["state"])}</td><td>{h(row["error"])}</td><td>{undo}</td></tr>')
        operation_undo = form(app, "undo_preview", f'<input type="hidden" name="batch" value="{h(batch)}">' + button("Undo operation", True))
        operations.append(f'<details class="operation"><summary><strong>{h((items[0]["created_at"] or "Earlier organization")[:16].replace("T", " "))}</strong><span>{len(items)} files · {count} potentially reversible</span></summary>{operation_undo}<div class="table-scroll"><table><thead><tr><th>File / paths</th><th>Status</th><th>Details</th><th>Restore</th></tr></thead><tbody>{"".join(cells)}</tbody></table></div><details><summary>Technical details</summary><code>{h(batch)}</code></details></details>')
    lookup = form(app, "undo_preview", '<label>Operation ID<input name="batch" required></label>' + button("Preview operation undo", True))
    return f'<details id="history" class="disclosure"><summary>History <span class="muted">· {len(groups)} organizations</span></summary>{"".join(operations) or "<p>No organizations yet.</p>"}<details><summary>Find an older operation</summary>{lookup}</details></details>'


def render(app):
    settings = app.settings.load()
    scan_label = "Scan Downloads" if Path(app.folder).name.casefold() == "downloads" else "Scan folder"
    scan = form(app, "scan", f'<span class="step">1 · SCAN DOWNLOADS</span><h2>Start with {h(Path(app.folder).name or "Downloads")}</h2><details id="change-folder"><summary>Change folder</summary><label>Source folder path<input name="folder" id="folder" value="{h(app.folder)}" required></label></details>{button(scan_label)}')
    source_section = (f'<details id="source" class="disclosure"><summary>Scanned {h(app.plan.source.name)} <span class="muted">· change folder or scan again</span></summary>{scan}</details>'
                      if app.plan else f'<section id="source">{scan}</section>')
    undo = form(app, "undo_preview", button("Undo Last", True))
    warning = '<p class="warning">Restricted automation account. Start python web_app.py from your normal terminal to use your folder permissions.</p>' if "codexsandbox" in app.process_account.casefold() else ""
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Smart Downloads Manager</title><link rel="stylesheet" href="/assets/style.css"><script src="/assets/app.js" defer></script></head><body class="simple">
        <main><header class="simple-header"><a class="brand" href="/"><span class="logo">S</span><span>Smart Downloads Manager<small>LOCAL. PRIVATE. IN YOUR CONTROL.</small></span></a>{undo}</header>
        <div class="simple-hero"><h1>Make room for clarity.</h1><p>Scan Downloads → Review suggested folders → Organize.</p></div>
        <div class="notice" role="status">{h(app.message)}</div>{render_restore(app)}{source_section}{render_preview(app, settings)}{render_history(app)}
        <details id="advanced" class="disclosure"><summary>Advanced <span class="muted">· categories, rules, and diagnostics</span></summary>{render_settings(app, settings)}{correction_form(app, settings)}<details><summary>Server diagnostics</summary><p>Process account: <code>{h(app.process_account)}</code><br>Python executable: <code>{h(app.python_executable)}</code></p>{warning}</details></details>
        <footer>Nothing moves automatically. Existing files are never overwritten. Your undo history stays on this computer.</footer></main>
        <div class="busy" role="status" aria-live="polite"><div><progress></progress><h2>Working on your request…</h2><p>Keep this tab open. Large files may take a moment.</p></div></div></body></html>'''
