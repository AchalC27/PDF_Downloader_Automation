function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

let startPicker = null;
let endPicker = null;

const state = {
  reports: [],
  total: 0,
  search: '',
  source: 'All Sources',
  startDate: todayStr(),
  endDate: todayStr(),
  sortField: 'date',
  sortOrder: 'desc',
  selectedIds: new Set(),
};

function currentFilterParams() {
  return {
    search: state.search,
    source: state.source,
    start_date: state.startDate,
    end_date: state.endDate,
    sort_field: state.sortField,
    sort_order: state.sortOrder,
  };
}

function showToast(message) {
  const toast = document.getElementById('toast');
  document.getElementById('toast-message').textContent = message;
  toast.classList.remove('hidden');
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => toast.classList.add('hidden'), 4000);
}

function updateResetVisibility() {
  const active = state.search || state.source !== 'All Sources' || state.startDate || state.endDate;
  document.getElementById('reset-filters-btn').classList.toggle('hidden', !active);
}

async function loadReports() {
  document.getElementById('table-body').innerHTML =
    '<tr><td colspan="6" class="loading-row">Loading catalog…</td></tr>';

  const res = await Api.getReports(currentFilterParams());
  if (res.ok) {
    state.reports = res.reports;
  } else {
    state.reports = [];
    showToast('Could not load PDFs — check the database connection.');
  }
  Render.table(state.reports, state.total, state.selectedIds);
  Render.sortIcons(state.sortField, state.sortOrder);
  bindEmptyStateReset();
  updateBulkBar();
}

async function loadStats() {
  const res = await Api.getStats();
  if (res.ok) {
    state.total = res.stats.total;
    Render.kpis(res.stats);
    document.getElementById('footer-total').textContent = res.stats.total;
  }
}

async function loadSources() {
  const res = await Api.getSources();
  const sources = res.sources || [];
  Render.sources(document.getElementById('source-filter-select'), sources, state.source);
}

function bindEmptyStateReset() {
  const btn = document.getElementById('empty-state-reset-btn');
  if (btn) btn.addEventListener('click', resetFilters);
}

function resetFilters() {
  state.search = '';
  state.source = 'All Sources';
  state.startDate = '';
  state.endDate = '';
  state.sortField = 'date';
  state.sortOrder = 'desc';

  document.getElementById('search-input').value = '';
  document.getElementById('source-filter-select').value = 'All Sources';
  startPicker.clear(false);
  endPicker.clear(false);

  updateResetVisibility();
  loadReports();
}

function setQuickDateRange(days) {
  const today = new Date();
  const past = new Date(today);
  past.setDate(today.getDate() - days);
  const fmt = (d) => d.toISOString().slice(0, 10);

  state.startDate = fmt(past);
  state.endDate = fmt(today);
  startPicker.setDate(state.startDate, false);
  endPicker.setDate(state.endDate, false);

  updateResetVisibility();
  loadReports();
}

function handleSort(field) {
  if (state.sortField === field) {
    state.sortOrder = state.sortOrder === 'asc' ? 'desc' : 'asc';
  } else {
    state.sortField = field;
    state.sortOrder = 'desc';
  }
  loadReports();
}

function debounce(fn, wait) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), wait);
  };
}

async function handleAddSubmit() {
  const name = document.getElementById('report-name-input').value.trim();
  const source = document.getElementById('report-source-input').value.trim();
  const category = document.getElementById('report-category-input').value.trim();
  const link = document.getElementById('report-link-input').value.trim();
  const uploadDate = document.getElementById('report-date-input').value;

  let valid = true;
  const nameInput = document.getElementById('report-name-input');
  const sourceInput = document.getElementById('report-source-input');
  const linkInput = document.getElementById('report-link-input');
  [nameInput, sourceInput, linkInput].forEach((el) => el.classList.remove('invalid'));
  document.getElementById('err-name').textContent = '';
  document.getElementById('err-source').textContent = '';
  document.getElementById('err-link').textContent = '';

  if (!name) { document.getElementById('err-name').textContent = 'Document name is required'; nameInput.classList.add('invalid'); valid = false; }
  if (!source) { document.getElementById('err-source').textContent = 'Source is required'; sourceInput.classList.add('invalid'); valid = false; }
  if (!link) { document.getElementById('err-link').textContent = 'PDF link is required'; linkInput.classList.add('invalid'); valid = false; }
  if (!valid) return;

  const { ok, data } = await Api.addReport({
    pdf_name: name,
    source,
    category,
    pdf_link: link,
    upload_date: uploadDate,
  });

  if (ok) {
    Modals.closeAdd();
    showToast(`"${name.substring(0, 40)}" added to the catalog!`);
    await Promise.all([loadReports(), loadStats(), loadSources()]);
  } else {
    showToast(data.error || 'Could not add the report.');
  }
}

function updateBulkBar() {
  const count = state.selectedIds.size;
  const btn = document.getElementById('download-selected-btn');
  btn.classList.toggle('hidden', count === 0);
  document.getElementById('download-selected-count').textContent = `Download Selected (${count})`;

  const selectAll = document.getElementById('select-all-checkbox');
  const visibleIds = state.reports.map((r) => r.id);
  const visibleSelected = visibleIds.filter((id) => state.selectedIds.has(id));

  if (visibleIds.length === 0) {
    selectAll.checked = false;
    selectAll.indeterminate = false;
  } else if (visibleSelected.length === visibleIds.length) {
    selectAll.checked = true;
    selectAll.indeterminate = false;
  } else if (visibleSelected.length > 0) {
    selectAll.checked = false;
    selectAll.indeterminate = true;
  } else {
    selectAll.checked = false;
    selectAll.indeterminate = false;
  }
}

function handleSelectAllChange(e) {
  const checked = e.target.checked;
  state.reports.forEach((r) => {
    if (checked) state.selectedIds.add(r.id);
    else state.selectedIds.delete(r.id);
  });
  document.querySelectorAll('.row-checkbox').forEach((cb) => {
    cb.checked = checked;
  });
  updateBulkBar();
}

function handleRowCheckboxChange(e) {
  const cb = e.target.closest('.row-checkbox');
  if (!cb) return;
  const id = Number(cb.dataset.id);
  if (cb.checked) state.selectedIds.add(id);
  else state.selectedIds.delete(id);
  updateBulkBar();
}

async function handleDownloadSelected() {
  const ids = Array.from(state.selectedIds);
  if (!ids.length) return;

  const btn = document.getElementById('download-selected-btn');
  const originalLabel = document.getElementById('download-selected-count').textContent;
  btn.disabled = true;
  document.getElementById('download-selected-count').textContent = 'Preparing download…';

  try {
    const blob = await Api.downloadZip(ids);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ISEC_PDF_Selected_${todayStr()}.zip`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showToast(`Downloading ${ids.length} selected PDF${ids.length === 1 ? '' : 's'} as a zip.`);
  } catch (err) {
    showToast(err.message || 'Could not download the selected PDFs.');
  } finally {
    btn.disabled = false;
    document.getElementById('download-selected-count').textContent = originalLabel;
  }
}

function exportCsv() {
  window.open(Api.exportCsvUrl(currentFilterParams()), '_blank');
  showToast('Catalog export started — check your downloads.');
}

function init() {
  document.getElementById('footer-year').textContent = new Date().getFullYear();
  document.getElementById('live-date').textContent =
    new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) + ' UTC';

  // Date pickers: display dd-mm-yyyy, but keep the underlying value in
  // yyyy-mm-dd (ISO) so filtering/API calls are unaffected.
  startPicker = flatpickr('#date-picker-start', {
    dateFormat: 'Y-m-d',
    altInput: true,
    altFormat: 'd-m-Y',
    allowInput: true,
    defaultDate: state.startDate,
    onChange: (selectedDates, dateStr) => {
      state.startDate = dateStr;
      updateResetVisibility();
      loadReports();
    },
  });

  endPicker = flatpickr('#date-picker-end', {
    dateFormat: 'Y-m-d',
    altInput: true,
    altFormat: 'd-m-Y',
    allowInput: true,
    defaultDate: state.endDate,
    onChange: (selectedDates, dateStr) => {
      state.endDate = dateStr;
      updateResetVisibility();
      loadReports();
    },
  });

  updateResetVisibility();

  document.getElementById('select-all-checkbox').addEventListener('change', handleSelectAllChange);
  document.getElementById('table-body').addEventListener('change', handleRowCheckboxChange);
  document.getElementById('download-selected-btn').addEventListener('click', handleDownloadSelected);

  document.getElementById('search-input').addEventListener('input', debounce((e) => {
    state.search = e.target.value;
    updateResetVisibility();
    loadReports();
  }, 300));

  document.getElementById('source-filter-select').addEventListener('change', (e) => {
    state.source = e.target.value;
    updateResetVisibility();
    loadReports();
  });

  document.getElementById('quick-date-7d').addEventListener('click', () => setQuickDateRange(7));
  document.getElementById('quick-date-30d').addEventListener('click', () => setQuickDateRange(30));
  document.getElementById('reset-filters-btn').addEventListener('click', resetFilters);
  document.getElementById('refresh-catalog-btn').addEventListener('click', () => {
    loadReports();
    loadStats();
  });
  document.getElementById('export-csv-btn').addEventListener('click', exportCsv);

  document.querySelectorAll('.th-sort').forEach((th) => {
    th.addEventListener('click', () => handleSort(th.dataset.sort));
  });

  document.getElementById('table-body').addEventListener('click', (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    const id = Number(btn.dataset.id);
    const report = state.reports.find((r) => r.id === id);
    if (!report) return;

    if (btn.dataset.action === 'preview') Modals.openPreview(report);
    if (btn.dataset.action === 'download') window.open(report.pdf_link, '_blank', 'noopener');
  });

  document.getElementById('header-add-pdf-btn').addEventListener('click', () => Modals.openAdd());

  Modals.bindStaticEvents({ onSubmitAdd: handleAddSubmit });

  loadSources();
  loadStats();
  loadReports();
}

document.addEventListener('DOMContentLoaded', init);
