// ─── Router ───────────────────────────────────────────────
const API_BASE = '';

let currentRoute = '/';

const routes = {
  '/': renderDashboard,
  '/matches': renderMatches,
  '/news': renderNews,
  '/domains': renderDomains,
};

function matchRoute(path) {
  const detailMatch = path.match(/^\/matches\/(.+)$/);
  if (detailMatch) {
    return { handler: renderMatchDetail, params: { id: detailMatch[1] } };
  }
  const handler = routes[path];
  if (handler) return { handler, params: {} };
  return { handler: renderDashboard, params: {} };
}

async function navigate(event, path) {
  if (event) event.preventDefault();
  const url = new URL(window.location.origin + path);
  window.history.pushState({}, '', url);
  await handleRoute();
  // Close mobile menu
  const menu = document.getElementById('mobile-menu');
  if (menu) menu.classList.add('hidden');
  return false;
}

async function handleRoute() {
  const path = window.location.pathname;
  currentRoute = path;
  const { handler, params } = matchRoute(path);
  updateActiveNav(path);
  await handler(params);
}

function updateActiveNav(path) {
  document.querySelectorAll('.nav-link').forEach(el => {
    const route = el.dataset.route;
    el.classList.toggle('active', route === path || (route !== '/' && path.startsWith(route)));
  });
}

function toggleMobileMenu() {
  document.getElementById('mobile-menu').classList.toggle('hidden');
}

// ─── Fetch helper ─────────────────────────────────────────
async function apiFetch(path) {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`${resp.status}: ${text.slice(0, 100)}`);
  }
  return resp.json();
}

// ─── Toast ────────────────────────────────────────────────
function showToast(message, type = 'info') {
  const colors = {
    info: 'bg-blue-600',
    success: 'bg-emerald-600',
    error: 'bg-red-600',
    warning: 'bg-yellow-600',
  };
  const el = document.createElement('div');
  el.className = `fixed top-4 right-4 ${colors[type] || colors.info} text-white px-4 py-3 rounded-lg shadow-lg z-50 fade-in text-sm max-w-sm`;
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

// ─── Helpers ──────────────────────────────────────────────
function formatUptime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}h ${m}m ${s}s`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

function formatDate(dateStr) {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('id-ID', {
    day: 'numeric', month: 'short', year: 'numeric',
  });
}

function leagueBadge(league) {
  if (!league) return '';
  const colors = {
    'GRUP A': 'bg-purple-900/50 text-purple-400 border-purple-800',
    'GRUP B': 'bg-purple-900/50 text-purple-400 border-purple-800',
    'GRUP C': 'bg-purple-900/50 text-purple-400 border-purple-800',
    'GRUP D': 'bg-purple-900/50 text-purple-400 border-purple-800',
  };
  const cls = colors[league] || 'bg-gray-800 text-gray-400';
  return `<span class="inline-flex px-2 py-0.5 rounded-full text-xs font-medium border ${cls}">${league}</span>`;
}

function statusBadge(status) {
  if (!status) return '<span class="badge-upcoming"><i class="far fa-clock text-xs"></i><span>Upcoming</span></span>';
  if (status === 'live' || status === 'LIVE') return '<span class="badge-live"><span class="pulse"></span><span>LIVE</span></span>';
  if (['ft', 'full time', 'selesai'].includes(status.toLowerCase())) return '<span class="badge-finished"><i class="fas fa-check text-xs"></i><span>FT</span></span>';
  if (['halftime', 'ht'].includes(status.toLowerCase())) return '<span class="badge-live"><span class="pulse"></span><span>HT</span></span>';
  return `<span class="badge-upcoming"><i class="far fa-clock text-xs"></i><span>${status}</span></span>`;
}

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return 'just now';
  if (min < 60) return `${min}m ago`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function truncate(str, n = 100) {
  if (!str || str.length <= n) return str || '';
  return str.slice(0, n) + '...';
}

// ─── Init on popstate ─────────────────────────────────────
window.addEventListener('popstate', handleRoute);

// Start
document.addEventListener('DOMContentLoaded', handleRoute);
