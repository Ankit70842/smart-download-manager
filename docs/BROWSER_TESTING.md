# Reproduce browser verification

Use only new disposable fixtures, not real Downloads. Python needs no third-party
packages; Playwright CLI and Chrome are optional developer tooling.

1. Run `python scripts/create_smart_demo.py` from your own normal terminal. Note
   its new `root`, `source`, and `destination`. It also saves `manifest.json`.
2. Start `python web_app.py --port 8502 --database "ROOT\history.sqlite"`, replacing
   `ROOT` with that new root. Use the same normal OS account for both commands.
3. Create `.runtime` if necessary so review screenshots have a local output folder.
4. With Playwright CLI installed:

```powershell
playwright-cli -s=smart-review open http://127.0.0.1:8502 --browser=chrome
playwright-cli -s=smart-review fill '#folder' 'SOURCE_FROM_MANIFEST'
playwright-cli -s=smart-review run-code --filename=tests/browser_smart.js
playwright-cli -s=smart-review console error
playwright-cli -s=smart-review run-code --filename=tests/browser_mobile.js
playwright-cli -s=smart-review close
```

The script deliberately refuses a source without `smart-review-` in its path. It
creates `Studies/AI` and a `robot` rule; scans; checks uncertainty/incomplete-file
handling; chooses the sibling destination; searches/sorts/selects; bulk-edits two
categories; excludes the placeholder EXE; includes an explicitly categorized
uncertain file; Applies five successful moves plus one collision; restores one
file and then the remaining four; checks narrow-screen overflow. Nothing is
applied to any other folder. The placeholder EXE is never executed.

The developer must also verify actual filesystem results using the manifest:
all eight source files retain their recorded contents, the original destination
`Personal/invoice.txt` still contains `existing invoice`, and it is the only file
remaining below the destination. The source `nested` directory stays untouched.
Empty category directories may remain, by design.

Screenshots are generated under ignored `.runtime`, not uploaded anywhere.
The checked-in dashboard screenshot is an actual clean-start browser capture,
with no private source paths or fabricated usage metrics.
