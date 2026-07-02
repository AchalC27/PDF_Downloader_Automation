const Api = {
  async getReports(params) {
    const qs = new URLSearchParams(params).toString();
    const res = await fetch(`/api/reports?${qs}`);
    return res.json();
  },

  async getSources() {
    const res = await fetch('/api/sources');
    return res.json();
  },

  async getStats() {
    const res = await fetch('/api/stats');
    return res.json();
  },

  async addReport(payload) {
    const res = await fetch('/api/reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    return { ok: res.ok && data.ok, data };
  },

  exportCsvUrl(params) {
    const qs = new URLSearchParams(params).toString();
    return `/api/export.csv?${qs}`;
  },

  async downloadZip(ids) {
    const res = await fetch('/api/download-zip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids }),
    });
    if (!res.ok) {
      let message = 'Could not build the download.';
      try {
        const data = await res.json();
        message = data.error || message;
        if (data.failures) console.error('PDF download failures:', data.failures);
      } catch (e) { /* ignore non-JSON error body */ }
      throw new Error(message);
    }
    return res.blob();
  },
};
