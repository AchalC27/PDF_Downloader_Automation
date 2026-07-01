const state = {
  reports: [],
  total: 0,
  search: '',
  source: 'All Sources',
  startDate: '',
  endDate: '',
  sortField: 'date',
  sortOrder: 'desc',
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
    '<tr><td colspan="5" class="loading-row">Loading catalog…</td></tr>';

  const res = await Api.getReports(currentFilterParams());
  if (res.ok) {
    state.reports = res.reports;
  } else {
    state.reports = [];
    showToast('Could not load PDFs — check the database connection.');
  }
  Render.table(state.reports, state.total);
  Render.sortIcons(state.sortField, state.sortOrder);
  bindEmptyStateReset();
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
  document.getElementById('date-picker-start').value = '';
  document.getElementById('date-picker-end').value = '';

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
  document.getElementById('date-picker-start').value = state.startDate;
  document.getElementById('date-picker-end').value = state.endDate;

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

function exportCsv() {
  window.open(Api.exportCsvUrl(currentFilterParams()), '_blank');
  showToast('Catalog export started — check your downloads.');
}

function init() {
  document.getElementById('footer-year').textContent = new Date().getFullYear();
  document.getElementById('live-date').textContent =
    new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) + ' UTC';

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

  document.getElementById('date-picker-start').addEventListener('change', (e) => {
    state.startDate = e.target.value;
    updateResetVisibility();
    loadReports();
  });

  document.getElementById('date-picker-end').addEventListener('change', (e) => {
    state.endDate = e.target.value;
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
