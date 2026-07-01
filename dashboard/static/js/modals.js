const Modals = {
  openPreview(report) {
    document.getElementById('preview-ref').textContent = `RECORD ID #${report.id}`;
    document.getElementById('preview-title').textContent = report.pdf_name;
    document.getElementById('preview-doc-refblock').innerHTML =
      `Ref: STORE_PDF/${report.id}<br>Source: ${escapeHtml(report.source)}`;
    document.getElementById('meta-date').textContent = report.upload_date;
    document.getElementById('meta-source').textContent = report.source;
    document.getElementById('meta-category').textContent = report.category || '—';
    document.getElementById('meta-id').textContent = `#${report.id}`;
    document.getElementById('preview-doc-title').textContent = report.pdf_name;

    const link = document.getElementById('preview-link');
    link.href = report.pdf_link;
    link.textContent = report.pdf_link;

    document.getElementById('download-preview-pdf-btn').onclick = () => {
      window.open(report.pdf_link, '_blank', 'noopener');
    };

    document.getElementById('preview-modal-overlay').classList.remove('hidden');
  },

  closePreview() {
    document.getElementById('preview-modal-overlay').classList.add('hidden');
  },

  openAdd() {
    document.getElementById('add-modal-overlay').classList.remove('hidden');
    document.getElementById('report-name-input').value = '';
    document.getElementById('report-source-input').value = '';
    document.getElementById('report-category-input').value = '';
    document.getElementById('report-link-input').value = '';
    document.getElementById('report-date-input').value = new Date().toISOString().slice(0, 10);
    ['err-name', 'err-source', 'err-link'].forEach((id) => { document.getElementById(id).textContent = ''; });
    ['report-name-input', 'report-source-input', 'report-link-input'].forEach((id) => {
      document.getElementById(id).classList.remove('invalid');
    });
  },

  closeAdd() {
    document.getElementById('add-modal-overlay').classList.add('hidden');
  },

  bindStaticEvents({ onSubmitAdd }) {
    document.getElementById('close-preview-btn').onclick = () => Modals.closePreview();
    document.getElementById('preview-modal-overlay').addEventListener('click', (e) => {
      if (e.target.id === 'preview-modal-overlay') Modals.closePreview();
    });

    document.getElementById('close-add-modal-btn').onclick = () => Modals.closeAdd();
    document.getElementById('cancel-add-btn').onclick = () => Modals.closeAdd();
    document.getElementById('add-modal-overlay').addEventListener('click', (e) => {
      if (e.target.id === 'add-modal-overlay') Modals.closeAdd();
    });

    document.getElementById('submit-add-btn').onclick = onSubmitAdd;
  },
};
