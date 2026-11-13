// Run only after browser_simple.js and a filesystem check proves no files moved.
async page => {
  await page.getByRole('button',{name:'Confirm & Organize',exact:true}).click();
  if (!(await page.locator('.notice').innerText()).includes('Moved 3 of 3 files')) throw new Error('Organization failed');
  await page.getByRole('button',{name:'Undo Last',exact:true}).click();
  if (!(await page.locator('.restore').innerText()).includes('3 files can be safely restored')) throw new Error('Undo preview missing');
  await page.getByRole('button',{name:'Confirm restore',exact:true}).click();
  if (!(await page.locator('.notice').innerText()).includes('restored 3 of 3')) throw new Error('Undo failed');
  return 'PASS: explicit final confirmation organizes 3 files; prominent Undo Last safely restores all 3';
}
