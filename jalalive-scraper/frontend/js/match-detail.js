// ─── Match Detail ─────────────────────────────────────────
async function renderMatchDetail(params) {
  const { id } = params;
  const app = document.getElementById('app');

  app.innerHTML = `
    <div class="fade-in">
      <div class="mb-6">
        <a href="/matches" onclick="return navigate(event, '/matches')"
           class="text-sm text-gray-400 hover:text-white transition-colors">
          <i class="fas fa-arrow-left mr-1"></i> Back to Matches
        </a>
      </div>
      <div id="match-detail-content">
        <div class="text-gray-500 text-sm py-8 text-center">
          <i class="fas fa-spinner fa-spin mr-2"></i>Loading...
        </div>
      </div>
    </div>
  `;

  try {
    const matches = await apiFetch('/api/v1/matches?limit=200');
    const match = matches.find(m => m.match_id === id);

    if (!match) {
      document.getElementById('match-detail-content').innerHTML =
        '<div class="text-gray-500 text-sm py-8 text-center">Match not found.</div>';
      return;
    }

    let streams = [];
    try {
      streams = await apiFetch(`/api/v1/matches/${id}/streams`);
    } catch (_) {}

    const hasScore = match.home_score !== null && match.away_score !== null;

    document.getElementById('match-detail-content').innerHTML = `
      <!-- Score card -->
      <div class="card text-center mb-6">
        <div class="text-xs text-gray-500 mb-3">${leagueBadge(match.league)} ${statusBadge(match.status)}</div>
        <div class="flex items-center justify-center space-x-8 py-6">
          <div class="flex-1 text-right">
            <div class="text-2xl font-bold">${match.home_team}</div>
          </div>
          <div class="flex items-center space-x-3">
            ${hasScore
              ? `<span class="score-display text-emerald-400">${match.home_score}</span>
                 <span class="score-divider">:</span>
                 <span class="score-display text-emerald-400">${match.away_score}</span>`
              : `<span class="text-gray-500 text-lg">vs</span>`}
          </div>
          <div class="flex-1 text-left">
            <div class="text-2xl font-bold">${match.away_team}</div>
          </div>
        </div>
        <div class="text-sm text-gray-500">
          ${match.date ? formatDate(match.date) + ' ' : ''}${match.time || ''}
        </div>
      </div>

      <!-- Stream links -->
      <div class="card mb-6">
        <h3 class="text-sm font-medium text-gray-400 uppercase tracking-wider mb-4">
          <i class="fas fa-video mr-2"></i>Stream Links
        </h3>
        ${streams.length === 0
          ? '<div class="text-gray-500 text-sm py-2">No stream links available.</div>'
          : streams.map(s => `
            <a href="${s.url}" target="_blank" rel="noopener"
               class="flex items-center justify-between p-3 rounded-lg bg-gray-800/50 hover:bg-gray-800 transition-colors mb-2">
              <div class="flex items-center space-x-3">
                <i class="fas fa-external-link-alt text-emerald-400 text-xs"></i>
                <span class="text-sm">${s.label || s.type || 'Stream'}</span>
              </div>
              <span class="text-xs text-gray-500">${s.type}</span>
            </a>
          `).join('')}
      </div>

      <!-- Match info -->
      <div class="card">
        <h3 class="text-sm font-medium text-gray-400 uppercase tracking-wider mb-4">
          <i class="fas fa-info-circle mr-2"></i>Match Info
        </h3>
        <div class="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span class="text-gray-500">Match ID</span>
            <div class="font-mono text-xs mt-0.5 text-gray-400">${match.match_id}</div>
          </div>
          <div>
            <span class="text-gray-500">Source</span>
            <div class="mt-0.5">${match.domain}</div>
          </div>
          <div>
            <span class="text-gray-500">Scraped</span>
            <div class="mt-0.5">${timeAgo(match.scraped_at)}</div>
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    document.getElementById('match-detail-content').innerHTML =
      `<div class="text-red-400 text-sm py-8 text-center">Error: ${err.message}</div>`;
    showToast('Failed to load match: ' + err.message, 'error');
  }
}
