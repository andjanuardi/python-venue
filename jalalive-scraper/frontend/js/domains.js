// ─── Domains ──────────────────────────────────────────────
async function renderDomains() {
  const app = document.getElementById('app');
  app.innerHTML = `
    <div class="fade-in">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold">Domains</h1>
          <p class="text-gray-400 text-sm mt-1">Mirror domain pool status</p>
        </div>
        <div class="flex items-center space-x-3">
          <select id="filter-domain-status" onchange="loadDomains()" class="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="dead">Dead</option>
            <option value="untested">Untested</option>
            <option value="rate_limited">Rate Limited</option>
          </select>
          <button onclick="loadDomains()" class="btn-secondary btn-sm">
            <i class="fas fa-redo"></i>
          </button>
        </div>
      </div>
      <div id="domains-content" class="table-container">
        <div class="text-gray-500 text-sm py-8 text-center">
          <i class="fas fa-spinner fa-spin mr-2"></i>Loading...
        </div>
      </div>
    </div>
  `;

  await loadDomains();
}

async function loadDomains() {
  const filterEl = document.getElementById('filter-domain-status');
  const statusParam = filterEl ? filterEl.value : '';

  try {
    const domains = await apiFetch(`/api/v1/domains${statusParam ? '?status=' + statusParam : ''}`);
    const container = document.getElementById('domains-content');

    if (domains.length === 0) {
      container.innerHTML = '<div class="text-gray-500 text-sm py-8 text-center">No domains found.</div>';
      return;
    }

    const statusColors = {
      active: 'bg-green-900/50 text-green-400 border-green-800',
      dead: 'bg-red-900/50 text-red-400 border-red-800',
      untested: 'bg-gray-800 text-gray-400',
      rate_limited: 'bg-yellow-900/50 text-yellow-400 border-yellow-800',
    };

    container.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Status</th>
            <th>Domain</th>
            <th>Label</th>
            <th>Type</th>
            <th>Parser</th>
            <th>Last Check</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>
          ${domains.map(d => `
            <tr>
              <td>
                <span class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-medium border
                  ${statusColors[d.status] || 'bg-gray-800 text-gray-400'}">
                  <span class="w-1.5 h-1.5 rounded-full ${d.status === 'active' ? 'bg-green-500' : d.status === 'dead' ? 'bg-red-500' : 'bg-gray-500'}"></span>
                  <span>${d.status}</span>
                </span>
              </td>
              <td class="font-mono text-xs max-w-xs truncate">
                <a href="${d.url}" target="_blank" rel="noopener" class="text-emerald-400 hover:text-emerald-300">
                  ${d.url}
                  <i class="fas fa-external-link-alt text-xs ml-1"></i>
                </a>
              </td>
              <td>${d.label || '-'}</td>
              <td><span class="text-xs caps">${d.type || '-'}</span></td>
              <td class="font-mono text-xs text-gray-500">${d.parser || 'generic'}</td>
              <td class="text-xs text-gray-500">${d.last_check ? timeAgo(d.last_check) : '-'}</td>
              <td class="text-xs text-gray-500 max-w-xs truncate">${d.notes || ''}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (err) {
    document.getElementById('domains-content').innerHTML =
      `<div class="text-red-400 text-sm py-8 text-center">Error: ${err.message}</div>`;
    showToast('Failed to load domains: ' + err.message, 'error');
  }
}
