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


def render_preview(app, settings):
    plan = app.plan
    if plan is None:
        return '<section id="preview" class="empty"><div class="empty-icon">↗</div><h2>A clear plan before every move.</h2><p>Scan a folder to see suggested topics, reasons, and exact paths.<br>No file moves until you explicitly Apply.</p></section>'
    root = plan.destination_root
    mode = "inside" if root == plan.source else "external" if root else ""
    destination = form(app, "destination", f'''
        <input type="hidden" name="plan_id" value="{h(app.plan_id)}">
        <div class="section-heading"><div><span class="step">02 / DESTINATION</span><h2>Choose where files go</h2></div></div>
        <div class="destination-options"><label class="choice"><input type="radio" name="mode" value="inside" required {"checked" if mode == "inside" else ""}>
        <span><strong>Inside the source folder</strong><small>{h(plan.source)}</small></span></label>
        <label class="choice"><input type="radio" name="mode" value="external" required {"checked" if mode == "external" else ""}>
        <span><strong>A separate local folder</strong><small>Paste an existing folder path below.</small></span></label></div>
        <label>Separate destination path<input name="destination" placeholder="C:\\Users\\YourName\\Documents" value="{h(root if mode == 'external' else '')}"></label>
        <div class="actions">{button('Set destination')}<span class="muted">No folders created at this step.</span></div>''')
    rows = []
    for index, entry in enumerate(plan.entries):
        disabled = "disabled" if entry.skip_reason else ""
        reason = entry.skip_reason or entry.reason
        path = h(entry.destination) if entry.destination else "Choose a destination first"
        rows.append(f'''<tr class="file-row" data-name="{h(entry.source.name.casefold())}" data-category="{h(entry.category)}" data-status="{h(entry.status)}">
        <td><input type="checkbox" name="selected_{index}" value="yes" aria-label="Select {h(entry.source.name)}" {"checked" if entry.selected else ""} {disabled}></td>
        <td><strong>{h(entry.source.name)}</strong><small>{h(entry.source.suffix.lower() or 'No extension')}</small>
        <details class="path"><summary>Source path</summary><code>{h(entry.source)}</code></details></td>
        <td><select name="category_{index}" aria-label="Category for {h(entry.source.name)}" {disabled}>{options(settings['categories'], entry.category)}</select></td>
        <td class="destination-cell"><code>{path}</code></td>
        <td><span class="badge {"review" if entry.confidence == 'Needs review' else ''}">{h(entry.confidence)}</span><small>{h(reason)}</small></td>
        <td><span class="status">{h(entry.status)}</span></td></tr>''')
    controls = f'''<input type="hidden" name="token" value="{h(app.token)}"><input type="hidden" name="plan_id" value="{h(app.plan_id)}">
        <input type="hidden" name="edits_present" value="yes">
        <div class="section-heading"><div><span class="step">03 / REVIEW & ORGANIZE</span><h2>Your file preview</h2></div>
        <span class="badge"><span data-selected-count>{sum(e.selected for e in plan.entries)}</span> selected</span></div>
        <div class="toolbar"><label class="search">Search files<input type="search" id="search" placeholder="Filename, topic, or reason…"></label>
        <label>Category filter<select id="category-filter"><option value="">All categories</option>{options(settings['categories'])}</select></label>
        <label>Sort by<select id="sort"><option value="name">Filename</option><option value="category">Category</option><option value="status">Status</option></select></label></div>
        <div class="actions compact"><button type="button" class="text-button" id="select-visible">Select visible</button>
        <button type="button" class="text-button" id="deselect-visible">Deselect visible</button><span class="muted">Filtering hides rows; it does not exclude files.</span></div>
        <div class="table-scroll"><table id="file-table"><thead><tr><th>Select</th><th>Filename / source</th><th>Category</th><th>Exact destination</th><th>Confidence / reason</th><th>Status</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
        <div class="bulk"><label>Bulk category<select name="bulk_category">{options(settings['categories'])}</select></label>
        <button name="action" value="bulk" class="secondary">Update selected categories</button>
        <button name="action" value="edit" class="secondary">Save preview edits</button></div>
        <div class="apply-bar"><label class="checkbox"><input type="checkbox" name="confirmed" value="yes">I reviewed the exact paths and approve moving the selected files.</label>
        <button name="action" value="apply" {"disabled" if root is None else ""}>Apply these moves</button></div>
        <p class="muted">Apply uses your current selections and categories. Conflicts are skipped without overwriting. Uncertain files start excluded.</p>'''
    correction = ""
    eligible = [(i, e) for i, e in enumerate(plan.entries) if not e.skip_reason]
    if eligible:
        choices = "".join(f'<option value="{i}">{h(e.source.name)}</option>' for i, e in eligible)
        correction = '<details class="correction"><summary>Save a correction as an explicit filename rule</summary>' + form(app, "correction", f'''
            <input type="hidden" name="plan_id" value="{h(app.plan_id)}"><p>No rules are learned automatically. This saves the chosen filename stem as a keyword at priority 200.</p>
            <div class="toolbar"><label>File<select name="index">{choices}</select></label><label>Future category<select name="category">{options(settings['categories'])}</select></label></div>
            <label class="checkbox"><input type="checkbox" name="approved" value="yes" required>I approve saving this filename keyword as a new rule.</label>{button('Save filename rule')}''') + '</details>'
    return f'<section id="destination">{destination}</section><section id="preview"><form method="post" action="/" id="preview-form">{controls}</form>{correction}</section>'


def render_history(app):
    rows = app.history.rows()
    groups = defaultdict(list)
    for row in rows:
        groups[row["batch"]].append(row)
    undo_last = form(app, "undo_preview", button("Undo Last Organization", True))
    lookup = form(app, "undo_preview", '<label>Operation ID<input name="batch" required placeholder="Paste any full operation ID"></label>' + button("Preview operation undo", True), 'class="lookup"')
    operations = []
    for batch, items in list(groups.items())[:50]:
        count = sum(row["state"] == "moved" for row in items)
        cells = []
        for row in items:
            undo = form(app, "undo_preview", f'<input type="hidden" name="file_id" value="{row["id"]}">' + button("Undo file", True)) if row["state"] == "moved" else ""
            cells.append(f'<tr><td><strong>{h(Path(row["source"]).name)}</strong><small>Original: {h(row["source"])}</small><small>Destination: {h(row["destination"])}</small></td><td>{h(row["state"])}</td><td>{h(row["error"])}</td><td>{undo}</td></tr>')
        operation_undo = form(app, "undo_preview", f'<input type="hidden" name="batch" value="{h(batch)}">' + button("Undo operation", True))
        operations.append(f'<details class="operation"><summary><strong>{h(batch[:8])}</strong> <span>{h(items[0]["created_at"] or "Legacy operation")} · {len(items)} files · {count} potentially reversible</span></summary><p class="muted">Operation ID: <code>{h(batch)}</code></p>{operation_undo}<div class="table-scroll"><table><thead><tr><th>File / paths</th><th>Status</th><th>Details</th><th>Restore</th></tr></thead><tbody>{"".join(cells)}</tbody></table></div></details>')
    restore = ""
    if app.undo_rows:
        items = "".join(f'<tr><td><code>{h(r["destination"])}</code></td><td><code>{h(r["source"])}</code></td><td>{h(r["undo_reason"])}</td></tr>' for r in app.undo_rows)
        restore = f'<div class="restore"><h3>Confirm restore preview</h3><p>Only eligible files will be restored. Every file is checked again when you confirm.</p><div class="table-scroll"><table><thead><tr><th>From</th><th>Restore to</th><th>Safety check</th></tr></thead><tbody>{items}</tbody></table></div>' + form(app, "undo_confirm", f'<input type="hidden" name="undo_id" value="{h(app.undo_id)}"><label class="checkbox"><input type="checkbox" name="confirmed" value="yes" required>I approve restoring the eligible files shown above.</label>' + button("Confirm restore")) + '</div>'
    return f'<section id="history"><div class="section-heading"><div><span class="step">YOUR SAFETY NET</span><h2>Organization history</h2></div>{undo_last}</div>{restore}{"".join(operations) or "<p class=muted>No operations yet. Your journal stays on this computer.</p>"}<p class="muted">Showing the latest 50 operations. Older operations can be looked up by full ID. Empty folders are never deleted.</p>{lookup}</section>'


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


def render(app):
    settings = app.settings.load()
    entries = app.plan.entries if app.plan else []
    metrics = [("Files in preview", len(entries)), ("Selected", sum(e.selected for e in entries)),
               ("Need review", sum(e.confidence == "Needs review" and not e.skip_reason for e in entries)),
               ("Conflicts / skipped", sum(bool(e.skip_reason) or e.status.startswith("Conflict") for e in entries))]
    cards = "".join(f'<div class="metric"><strong>{count}</strong><span>{label}</span></div>' for label, count in metrics)
    scan = form(app, "preview", f'<span class="step">01 / SOURCE</span><h2>Start with a folder</h2><label>Source folder path<input name="folder" id="folder" value="{h(app.folder)}" placeholder="Paste an existing local folder path" required></label><div class="actions">{button("Scan & Preview")}<span class="muted">Top-level files only. No automatic moves.</span></div>')
    warning = '<p class="warning">Restricted automation account: start python web_app.py from your own normal terminal for access to your folders.</p>' if "codexsandbox" in app.process_account.casefold() else ""
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Smart Downloads Manager</title><link rel="stylesheet" href="/assets/style.css"><script src="/assets/app.js" defer></script></head><body>
    <aside class="sidebar"><a class="brand" href="#"><span class="logo">S</span><span>Smart Downloads<small>BY OPEN FOLDER ORGANIZER</small></span></a><nav><a href="#source">⌂ <span>Workspace</span></a><a href="#history">↶ <span>History & undo</span></a><a href="#settings">⚙ <span>Categories & rules</span></a></nav><div class="local-note"><span class="dot"></span>Offline by design<small>Your files stay on your computer.</small></div></aside>
    <main><header><span>YOUR PERSONAL FILE WORKSPACE</span><span class="offline"><span class="dot"></span> Local & offline</span></header>
    <div class="hero"><div><p class="eyebrow">LESS CLUTTER. MORE CLARITY.</p><h1>Make room for clarity.</h1><p>Organize by purpose, not just file type.<br>Every suggestion explained. Every move in your control.</p></div><div class="hero-mark" aria-hidden="true">↗</div></div>
    <div class="notice" role="status">{h(app.message)}</div><div class="metrics">{cards}</div>
    <section id="source">{scan}</section>{render_preview(app, settings)}{render_history(app)}{render_settings(app, settings)}
    <footer>Deterministic filename rules, not AI. No uploads, no file execution, no automatic deletion.
    <details><summary>Server diagnostics</summary><p>Process account: <code>{h(app.process_account)}</code><br>Python executable: <code>{h(app.python_executable)}</code></p>{warning}</details></footer>
    </main><div class="busy" role="status" aria-live="polite"><div><progress></progress><h2>Working on your request…</h2><p>Keep this tab open. Large files may take a moment.</p></div></div></body></html>'''
