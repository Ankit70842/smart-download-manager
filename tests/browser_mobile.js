// Run through playwright-cli run-code --filename=tests/browser_mobile.js.
// Prerequisite: open the local app with at least one history row.
async page => {
  await page.setViewportSize({width:390,height:844});
  const lines = await page.getByRole('columnheader',{name:'Status',exact:true}).evaluate(el => {
    const range = document.createRange();
    range.selectNodeContents(el);
    return range.getClientRects().length;
  });
  if (lines !== 1) throw new Error('Status header wraps into unreadable fragments');
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
  if (overflow) throw new Error('Page overflows the mobile viewport');
  return 'PASS: mobile history header is readable and page fits the viewport';
}
