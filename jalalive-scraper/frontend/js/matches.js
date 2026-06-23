// ─── Matches List ─────────────────────────────────────────
async function renderMatches() {
  const app = document.getElementById('app');
  app.innerHTML = `
    <div class="fade-in">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold">Matches</h1>
          <p class="text-gray-400 text-sm mt-1">Football match schedules &amp; scores</p>
        </div>
        <div class="flex items-center space-x-3">
          <select id="filter-league" onchange="loadMatches()" class="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
            <option value="">All Leagues</option>
          </select>
          <button onclick="loadMatches()" class="btn-secondary btn-sm">
            <i class="fas fa-redo"></i>
          </button>
        </div>
      </div>

      <div id="matches-content" class="table-container">
        <div class="text-gray-500 text-sm py-8 text-center">
          <i class="fas fa-spinner fa-spin mr-2"></i>Loading...
        </div>
      </div>
    </div>
  `;

  await loadMatches();
}

async function loadMatches() {
  const filterLeague = document.getElementById('filter-league');
  const leagueParam = filterLeague ? filterLeague.value : '';

  try {
    const matches = await apiFetch(`/api/v1/matches?limit=100${leagueParam ? '&league=' + encodeURIComponent(leagueParam) : ''}`);

    // Populate league filter
    if (filterLeague) {
      const leagues = [...new Set(matches.map(m => m.league).filter(Boolean))];
      const currentVal = filterLeague.value;
      filterLeague.innerHTML = '<option value="">All Leagues</option>' +
        leagues.map(l => `<option value="${l}" ${l === currentVal ? 'selected' : ''}>${l}</option>`).join('');
    }

    const container = document.getElementById('matches-content');
    if (matches.length === 0) {
      container.innerHTML = '<div class="text-gray-500 text-sm py-8 text-center">No matches found.</div>';
      return;
    }

    container.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Status</th>
            <th>Home</th>
            <th>Score</th>
            <th>Away</th>
            <th>Time</th>
            <th>League</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          ${matches.map(m => `
            <tr class="cursor-pointer" onclick="navigate(event, '/matches/${m.match_id}')">
              <td>${statusBadge(m.status)}</td>
              <td class="font-medium">${m.home_team}</td>
              <td class="text-center">
                ${m.home_score !== null && m.away_score !== null
                  ? `<span class="font-bold font-mono text-lg">${m.home_score} - ${m.away_score}</span>`
                  : '<span class="text-gray-600">-</span>'}
              </td>
              <td class="font-medium">${m.away_team}</td>
              <td class="text-gray-400">${m.time || '-'}</td>
              <td>${leagueBadge(m.league)}</td>
              <td class="text-right">
                <i class="fas fa-chevron-right text-gray-600 text-xs"></i>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (err) {
    showToast('Failed to load matches: ' + err.message, 'error');
  }
}
