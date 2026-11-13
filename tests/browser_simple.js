// Requires create_smart_demo fixtures (plus Code/Documents folders), with the
// disposable source already entered in #folder. Never use actual Downloads.
async page => {
  const source = await page.locator('#folder').inputValue();
  if (!source.includes('smart-review-')) throw new Error('Disposable fixture required');
  const open = async selector => {
    const details = page.locator(selector);
    if (!(await details.evaluate(el => el.open))) await details.locator(':scope > summary').click();
  };
  if (await page.locator('#change-folder').evaluate(el => el.open)) await page.locator('#change-folder > summary').click();
  await page.setViewportSize({width:1280,height:900});
  await page.screenshot({path:'.runtime/simple-dashboard.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:'.runtime/simple-mobile.png',fullPage:true});
  if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)) throw new Error('Mobile page overflow');
  await page.setViewportSize({width:1280,height:900});
  await page.locator('#source button').click();
  if (await page.locator('#file-table').isVisible()) throw new Error('Large file table visible by default');
  if (await page.locator('#advanced').evaluate(el => el.open)) throw new Error('Advanced expanded automatically');
  if (await page.locator('#history').evaluate(el => el.open)) throw new Error('History expanded automatically');
  for (const name of ['code','documents','nested']) {
    if (await page.locator(`.file-row[data-name="${name}"]`).count()) throw new Error('Directory shown as a file');
  }
  if (!(await page.locator('#folder-summary').innerText()).includes('Studies/Computer Networks')) throw new Error('Folder groups missing');
  await open('#edit-details');
  const row = name => page.locator('.file-row').filter({has:page.getByText(name,{exact:true})});
  if (await row('setup.exe').locator('input[type=checkbox]').isChecked()) throw new Error('Medium-confidence file auto-selected');
  if (await row('mystery839.pdf').locator('input[type=checkbox]').isChecked()) throw new Error('Unknown file auto-selected');
  await page.locator('#search').fill('DBMS');
  if (await page.locator('.file-row:visible').count() !== 1) throw new Error('Search failed');
  await page.locator('#search').fill('');
  await page.locator('#category-filter').selectOption('Studies/DBMS');
  if (await page.locator('.file-row:visible').count() !== 1) throw new Error('Filter failed');
  await page.locator('#category-filter').selectOption('');
  await page.getByRole('button',{name:'Deselect visible',exact:true}).click();
  await row('Computer Networks lecture.pdf').locator('input[type=checkbox]').check();
  await row('DBMS assignment.pptx').locator('input[type=checkbox]').check();
  await page.locator('select[name=bulk_category]').selectOption('Projects');
  await page.getByRole('button',{name:'Update selected categories',exact:true}).click();
  await open('#edit-details');
  await row('robot.pdf').locator('select').selectOption('Projects');
  await row('robot.pdf').locator('input[type=checkbox]').check();
  await row('invoice.txt').locator('input[type=checkbox]').check();
  await page.getByRole('button',{name:'Save preview edits',exact:true}).click();
  await page.getByRole('radio',{name:'Another folder',exact:true}).check();
  await page.getByLabel('Destination folder',{exact:true}).fill(source.replace(/source$/, 'destination'));
  await page.getByRole('button',{name:'Organize',exact:true}).click();
  if (!(await page.getByRole('heading',{level:2}).allTextContents()).includes('Ready to organize 3 files?')) throw new Error('Safe final summary count is wrong');
  if (await page.getByRole('checkbox').count()) throw new Error('Redundant final confirmation checkbox');
  await page.screenshot({path:'.runtime/simple-confirmation.png',fullPage:true});
  return 'REVIEW PASS: grouped folders, directories excluded, advanced controls hidden/reachable, selections, search/filter/bulk, external destination, one final confirmation; no moves yet';
}
