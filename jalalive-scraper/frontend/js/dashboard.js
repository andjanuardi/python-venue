// ─── Dashboard ────────────────────────────────────────────
async function renderDashboard() {
  const app = document.getElementById('app');

  app.innerHTML = `
    <div class="fade-in">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold">Dashboard</h1>
          <p class="text-gray-400 text-sm mt-1">Overview of JalaLive scraper status</p>
        </div>
        <div class="flex items-center space-x-3">
          <button onclick="triggerScrape()" class="btn-primary">
            <i class="fas fa-sync-alt"></i>
            <span>Scrape Now</span>
          </button>
          <button onclick="refreshDashboard()" class="btn-secondary">
            <i class="fas fa-redo"></i>
          </button>
        </div>
      </div>

      <!-- Stats grid -->
      <div id="stats-grid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        ${'...'.repeat(4).split('').map(() => `
          <div class="card animate-pulse">
            <div class="h-4 bg-gray-800 rounded w-24 mb-3"></div>
            <div class="h-8 bg-gray-800 rounded w-16 mb-2"></div>
            <div class="h-3 bg-gray-800 rounded w-32"></div>
          </div>
        `).join('')}
      </div>

      <!-- Charts row -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div class="card">
          <h3 class="text-sm font-medium text-gray-400 uppercase tracking-wider mb-4">
            <i class="fas fa-chart-bar mr-2"></i>Matches by League
          </h3>
          <canvas id="leagueChart" height="200"></canvas>
        </div>
        <div class="card">
          <h3 class="text-sm font-medium text-gray-400 uppercase tracking-wider mb-4">
            <i class="fas fa-globe mr-2"></i>Domain Status
          </h3>
          <canvas id="domainChart" height="200"></canvas>
        </div>
      </div>

      <!-- Recent info row -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="card">
          <h3 class="text-sm font-medium text-gray-400 uppercase tracking-wider mb-4">
            <i class="fas fa-bolt mr-2"></i>Recent Matches
          </h3>
          <div id="recent-matches" class="space-y-2">
            <div class="text-gray-500 text-sm py-4 text-center">Loading...</div>
          </div>
        </div>
        <div class="card">
          <h3 class="text-sm font-medium text-gray-400 uppercase tracking-wider mb-4">
            <i class="fas fa-newspaper mr-2"></i>Latest News
          </h3>
          <div id="latest-news" class="space-y-2">
            <div class="text-gray-500 text-sm py-4 text-center">Loading...</div>
          </div>
        </div>
      </div>
    </div>
  `;

  await refreshDashboard();

  // Auto-refresh every 30s
  if (window._dashboardInterval) clearInterval(window._dashboardInterval);
  window._dashboardInterval = setInterval(refreshDashboard, 30000);
}

async function refreshDashboard() {
  try {
    const health = await apiFetch('/health');

    // Stats
    document.getElementById('stats-grid').innerHTML = `
      <div class="card card-hover">
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs font-medium text-gray-400 uppercase">Matches</span>
          <i class="fas fa-futbol text-emerald-400"></i>
        </div>
        <div class="text-3xl font-bold">${health.total_matches}</div>
        <div class="text-xs text-gray-500 mt-1">in database</div>
      </div>
      <div class="card card-hover">
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs font-medium text-gray-400 uppercase">Domains</span>
          <i class="fas fa-server text-blue-400"></i>
        </div>
        <div class="text-3xl font-bold">${health.active_domains}</div>
        <div class="text-xs text-gray-500 mt-1">active</div>
      </div>
      <div class="card card-hover">
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs font-medium text-gray-400 uppercase">News</span>
          <i class="fas fa-newspaper text-yellow-400"></i>
        </div>
        <div class="text-3xl font-bold">${health.total_news || 0}</div>
        <div class="text-xs text-gray-500 mt-1">articles</div>
      </div>
      <div class="card card-hover">
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs font-medium text-gray-400 uppercase">Uptime</span>
          <i class="fas fa-clock text-purple-400"></i>
        </div>
        <div class="text-3xl font-bold font-mono text-sm">${formatUptime(health.uptime_seconds)}</div>
        <div class="text-xs text-gray-500 mt-1">server running</div>
      </div>
    `;

    // Update connection status
    const statusEl = document.getElementById('connection-status');
    if (health.status === 'ok') {
      statusEl.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-green-500"></span><span class="text-gray-400">Connected</span>';
    }

    // Charts
    drawLeagueChart();
    drawDomainChart();

    // Recent matches
    try {
      const matches = await apiFetch('/api/v1/matches?limit=5');
      const container = document.getElementById('recent-matches');
      if (matches.length === 0) {
        container.innerHTML = '<div class="text-gray-500 text-sm py-4 text-center">No matches yet. Run a scrape.</div>';
      } else {
        container.innerHTML = matches.map(m => `
          <a href="/matches/${m.match_id}" onclick="return navigate(event, '/matches/${m.match_id}')"
             class="flex items-center justify-between p-3 rounded-lg bg-gray-800/50 hover:bg-gray-800 transition-colors">
            <div class="flex items-center space-x-3">
              ${statusBadge(m.status)}
              <div>
                <span class="font-medium">${m.home_team}</span>
                <span class="text-gray-500 mx-1">vs</span>
                <span class="font-medium">${m.away_team}</span>
              </div>
            </div>
            <div class="text-xs text-gray-500">
              ${m.time || ''} ${m.league ? leagueBadge(m.league) : ''}
            </div>
          </a>
        `).join('');
      }
    } catch (_) {}

    // Latest news
    try {
      const news = await apiFetch('/api/v1/news?limit=3');
      const container = document.getElementById('latest-news');
      if (news.length === 0) {
        container.innerHTML = '<div class="text-gray-500 text-sm py-4 text-center">No news yet.</div>';
      } else {
        container.innerHTML = news.map(n => `
          <a href="${n.url}" target="_blank" rel="noopener"
             class="block p-3 rounded-lg bg-gray-800/50 hover:bg-gray-800 transition-colors">
            <div class="text-sm font-medium">${truncate(n.title, 60)}</div>
            <div class="text-xs text-gray-500 mt-1 flex items-center space-x-2">
              <span>${formatDate(n.date)}</span>
              <span>${leagueBadge(n.source)}</span>
            </div>
          </a>
        `).join('');
      }
    } catch (_) {}

  } catch (err) {
    showToast('Failed to load dashboard: ' + err.message, 'error');
  }
}

async function triggerScrape() {
  const btn = event.target.closest('button');
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Scraping...</span>';
  try {
    const result = await fetch('/scrape', { method: 'POST' });
    if (!result.ok) throw new Error((await result.text()).slice(0, 100));
    const data = await result.json();
    showToast(`Scrape completed in ${data.duration_seconds}s`, 'success');
    await refreshDashboard();
  } catch (err) {
    showToast('Scrape failed: ' + err.message, 'error');
  }
  btn.disabled = false;
  btn.innerHTML = '<i class="fas fa-sync-alt"></i><span>Scrape Now</span>';
}

// Charts
let _leagueChart = null;
let _domainChart = null;

async function drawLeagueChart() {
  try {
    const matches = await apiFetch('/api/v1/matches?limit=200');
    const leagues = {};
    matches.forEach(m => {
      const key = m.league || 'Unknown';
      leagues[key] = (leagues[key] || 0) + 1;
    });
    const labels = Object.keys(leagues);
    const data = Object.values(leagues);

    if (_leagueChart) _leagueChart.destroy();
    const ctx = document.getElementById('leagueChart');
    if (!ctx) return;
    _leagueChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: ['#34d399', '#60a5fa', '#f472b6', '#fbbf24', '#a78bfa', '#f87171'],
          borderWidth: 0,
        }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#9ca3af', padding: 12, font: { size: 11 } },
          },
        },
      },
    });
  } catch (_) {}
}

async function drawDomainChart() {
  try {
    const domains = await apiFetch('/api/v1/domains');
    const active = domains.filter(d => d.status === 'active').length;
    const dead = domains.filter(d => d.status === 'dead').length;
    const untested = domains.filter(d => d.status === 'untested').length;

    if (_domainChart) _domainChart.destroy();
    const ctx = document.getElementById('domainChart');
    if (!ctx) return;
    _domainChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Active', 'Dead', 'Untested'],
        datasets: [{
          data: [active, dead, untested],
          backgroundColor: ['#34d399', '#f87171', '#6b7280'],
          borderWidth: 0,
        }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#9ca3af', padding: 12, font: { size: 11 } },
          },
        },
      },
    });
  } catch (_) {}
}
