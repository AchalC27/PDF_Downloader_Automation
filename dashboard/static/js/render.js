const SOURCE_COLOR_MAP = {
  NSE: ['var(--blue-50)', 'var(--blue-700)', 'var(--blue-200)'],
  BSE: ['var(--orange-badge-50)', 'var(--orange-badge-700)', 'var(--orange-badge-200)'],
  CDSL: ['var(--purple-50)', 'var(--purple-700)', 'var(--purple-200)'],
  AMFI: ['var(--yellow-50)', 'var(--yellow-700)', 'var(--yellow-200)'],
  ARCL: ['var(--emerald-50)', 'var(--emerald-700)', 'var(--emerald-200)'],
  CKYC: ['var(--indigo-50)', 'var(--indigo-700)', 'var(--indigo-200)'],
  MCX: ['var(--red-50)', 'var(--red-700)', 'var(--red-100)'],
  APMI: ['var(--teal-50)', 'var(--teal-700)', 'var(--teal-200)'],
  PFRDA: ['var(--pink-50)', 'var(--pink-700)', 'var(--pink-200)'],
  NSDL: ['var(--cyan-50)', 'var(--cyan-700)', 'var(--cyan-200)'],
  SEBI: ['var(--violet-50)', 'var(--violet-700)', 'var(--violet-200)'],
  IRDAI: ['var(--lime-50)', 'var(--lime-700)', 'var(--lime-200)'],
};
const FALLBACK_PALETTE = Object.values(SOURCE_COLOR_MAP);

function sourceBadgeStyle(source) {
  const key = (source || '').toUpperCase();
  if (SOURCE_COLOR_MAP[key]) return SOURCE_COLOR_MAP[key];
  let hash = 0;
  for (let i = 0; i < key.length; i++) hash = (hash * 31 + key.charCodeAt(i)) % FALLBACK_PALETTE.length;
  return FALLBACK_PALETTE[Math.abs(hash)];
}

function formatDatePretty(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr + 'T00:00:00');
  if (isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function escapeHtml(str) {
  return String(str ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

const Render = {
  sources(selectEl, sources, selected) {
    const options = ['All Sources', ...sources];
    selectEl.innerHTML = options.map((s) => (
      `<option value="${escapeHtml(s)}" ${s === selected ? 'selected' : ''}>${s === 'All Sources' ? '📁 All Sources (Departments)' : escapeHtml(s)}</option>`
    )).join('');
  },

  kpis(stats) {
    document.getElementById('kpi-total').textContent = stats.total ?? 0;
    document.getElementById('kpi-sources').textContent = stats.total_sources ?? 0;
    document.getElementById('kpi-today').textContent = stats.today ?? 0;
    document.getElementById('kpi-week').textContent = stats.this_week ?? 0;
  },

  sortIcons(sortField, sortOrder) {
    document.querySelectorAll('.th-sort').forEach((th) => {
      const icon = th.querySelector('.sort-icon');
      icon.className = 'sort-icon';
      if (th.dataset.sort === sortField) {
        icon.classList.add(sortOrder === 'asc' ? 'asc' : 'desc');
      }
    });
  },

  table(reports, total, selectedIds = new Set()) {
    const tbody = document.getElementById('table-body');
    document.getElementById('result-count-badge').textContent =
      `${reports.length} ${reports.length === 1 ? 'Report' : 'Reports'}`;
    document.getElementById('footer-showing').textContent = reports.length;
    document.getElementById('footer-total').textContent = total;

    if (!reports.length) {
      tbody.innerHTML = `
        <tr><td colspan="6" class="empty-state">
          <div class="empty-state-inner">
            <div class="empty-icon">
              <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 12h10M4 18h6"/></svg>
            </div>
            <h4>No PDF Records Found</h4>
            <p>There are no documents matching your selected filters. Try widening your date range or selecting "All Sources".</p>
            <button class="btn btn-navy" id="empty-state-reset-btn" style="margin-top:16px;">Clear Active Filters</button>
          </div>
        </td></tr>`;
      return;
    }

    tbody.innerHTML = reports.map((r, idx) => {
      const [bg, fg, border] = sourceBadgeStyle(r.source);
      const checked = selectedIds.has(r.id) ? 'checked' : '';
      return `
      <tr class="${idx % 2 === 0 ? '' : 'row-alt'}" data-id="${r.id}">
        <td class="td-select"><input type="checkbox" class="row-checkbox" data-id="${r.id}" ${checked}></td>
        <td class="td-sr">${idx + 1}</td>
        <td>
          <div class="doc-cell">
            <div class="doc-icon">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>
            </div>
            <div>
              <button class="doc-title" data-action="preview" data-id="${r.id}">${escapeHtml(r.pdf_name)}</button>
              <div class="doc-meta">
                ${r.category ? `<span>${escapeHtml(r.category)}</span><span>•</span>` : ''}
                <span>ID #${r.id}</span>
              </div>
            </div>
          </div>
        </td>
        <td><span class="badge" style="background:${bg};color:${fg};border-color:${border};">${escapeHtml(r.source)}</span></td>
        <td>
          <div class="date-primary">${formatDatePretty(r.upload_date)}</div>
          <div class="date-secondary">${escapeHtml(r.upload_date)}</div>
        </td>
        <td>
          <div class="row-actions">
            <button class="icon-action" title="Quick View" data-action="preview" data-id="${r.id}">
              <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><path d="M15 3h6v6M10 14L21 3"/></svg>
            </button>
            <button class="icon-action icon-action-download" title="Open Source PDF" data-action="download" data-id="${r.id}">
              <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5M12 15V3"/></svg>
            </button>
          </div>
        </td>
      </tr>`;
    }).join('');
  },
};
