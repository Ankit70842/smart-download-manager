# Verify the simplified interface

Use disposable fixtures only. No step below scans the real Downloads folder.

1. Run `python scripts/create_smart_demo.py` in your normal terminal. It prints a
   new `smart-review-*` root/source/destination and writes `manifest.json`. The
   source includes Code, Documents, and nested directories to verify exclusion.
2. Start `python web_app.py --port 8502 --database "ROOT\history.sqlite"`, replacing
   ROOT with that new root. Keep the same normal OS account for both commands.
3. Create `.runtime` for test screenshots, and use an installed Playwright CLI:

```powershell
playwright-cli -s=simple-review open http://127.0.0.1:8502 --browser=chrome
playwright-cli -s=simple-review click '#change-folder > summary'
playwright-cli -s=simple-review fill '#folder' 'SOURCE_FROM_MANIFEST'
playwright-cli -s=simple-review run-code --filename=tests/browser_simple.js
```

The script refuses a source without `smart-review-` in its path. It verifies the
collapsed interface, category groups, excluded directories, optional advanced
controls, safe default selection, external destination, and final confirmation.
**It stops before moving anything.**

At this point verify all eight source files still match the manifest, the source
directories still exist, and the only destination file is the pre-existing
`Personal/invoice.txt`. Then explicitly run the confirmation/undo test:

```powershell
playwright-cli -s=simple-review run-code --filename=tests/browser_simple_finish.js
playwright-cli -s=simple-review run-code --filename=tests/browser_mobile.js
playwright-cli -s=simple-review console error
playwright-cli -s=simple-review close
```

Three explicitly selected files are organized into Projects; the destination
invoice collision is excluded. Undo Last previews and then restores all three.
Verify the eight original contents again, Code/Documents/nested are untouched,
and the destination invoice still contains `existing invoice` with no extra files.
Empty category directories may remain. No placeholder EXE is executed.

Screenshots under ignored `.runtime` are actual browser captures. Checked-in
screenshots show the simplified initial UI without private paths or fake metrics.
