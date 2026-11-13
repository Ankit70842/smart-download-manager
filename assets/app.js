/* Progressive enhancement only: classification and filesystem safety live in Python. */
(() => {
  const table = document.querySelector('#file-table');
  if (table) {
    const rows = [...table.querySelectorAll('tbody tr')];
    const search = document.querySelector('#search');
    const filter = document.querySelector('#category-filter');
    const selectedCount = document.querySelector('[data-selected-count]');
    const count = () => { selectedCount.textContent = rows.filter(row => row.querySelector('input[type=checkbox]:checked')).length; };
    const update = () => {
      const query = search.value.trim().toLocaleLowerCase();
      for (const row of rows) {
        const category = row.querySelector('select').value;
        row.dataset.category = category;
        // Do not search every option in the category dropdown: otherwise every
        // file matches every category, even when that category was not chosen.
        const text = [row.dataset.name, category, row.cells[4].textContent].join(' ').toLocaleLowerCase();
        row.hidden = !(text.includes(query) && (!filter.value || filter.value === category));
      }
      count();
    };
    search.addEventListener('input', update);
    filter.addEventListener('change', update);
    table.addEventListener('change', update);
    document.querySelector('#sort').addEventListener('change', event => {
      const field = event.target.value;
      rows.sort((a,b) => a.dataset[field].localeCompare(b.dataset[field]));
      for (const row of rows) table.tBodies[0].append(row);
    });
    for (const [id, checked] of [['select-visible',true],['deselect-visible',false]]) {
      document.getElementById(id).addEventListener('click', () => {
        rows.filter(row => !row.hidden).forEach(row => {
          const checkbox = row.querySelector('input[type=checkbox]');
          if (!checkbox.disabled) checkbox.checked = checked;
        });
        count();
      });
    }
  }
  let submitting = false;
  document.addEventListener('submit', event => {
    if (submitting) { event.preventDefault(); return; }
    if (event.submitter?.value === 'apply' && !event.target.querySelector('[name=confirmed]').checked) {
      event.preventDefault();
      alert('Review the exact paths and check the Apply confirmation first.');
      return;
    }
    submitting = true;
    document.body.classList.add('is-busy');
  });
  // Back/forward cache can restore a page with the loading overlay still active.
  addEventListener('pageshow', () => { submitting = false; document.body.classList.remove('is-busy'); });
})();
