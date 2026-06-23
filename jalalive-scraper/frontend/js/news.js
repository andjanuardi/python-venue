// ─── News ─────────────────────────────────────────────────
async function renderNews() {
  const app = document.getElementById('app');
  app.innerHTML = `
    <div class="fade-in">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold">News</h1>
          <p class="text-gray-400 text-sm mt-1">Latest football articles</p>
        </div>
        <button onclick="loadNews()" class="btn-secondary btn-sm">
          <i class="fas fa-redo"></i>
        </button>
      </div>
      <div id="news-content" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div class="col-span-full text-gray-500 text-sm py-8 text-center">
          <i class="fas fa-spinner fa-spin mr-2"></i>Loading...
        </div>
      </div>
    </div>
  `;

  await loadNews();
}

async function loadNews() {
  try {
    const articles = await apiFetch('/api/v1/news?limit=50');
    const container = document.getElementById('news-content');

    if (articles.length === 0) {
      container.innerHTML = '<div class="col-span-full text-gray-500 text-sm py-8 text-center">No news articles found.</div>';
      return;
    }

    container.innerHTML = articles.map(a => `
      <a href="${a.url}" target="_blank" rel="noopener" class="card card-hover flex flex-col">
        ${a.thumbnail
          ? `<div class="w-full h-40 bg-gray-800 rounded-lg mb-3 overflow-hidden">
               <img src="${a.thumbnail}" alt="${a.title}" class="w-full h-full object-cover" loading="lazy"
                    onerror="this.parentElement.innerHTML='<div class=\\'w-full h-full flex items-center justify-center text-gray-600\\'><i class=\\'fas fa-newspaper text-2xl\\'></i></div>'">
             </div>`
          : `<div class="w-full h-28 bg-gray-800 rounded-lg mb-3 flex items-center justify-center">
               <i class="fas fa-newspaper text-2xl text-gray-700"></i>
             </div>`}
        <div class="flex-1">
          <h3 class="font-medium text-sm leading-snug">${truncate(a.title, 100)}</h3>
          <p class="text-xs text-gray-500 mt-2">${truncate(a.excerpt, 120) || ''}</p>
        </div>
        <div class="flex items-center justify-between mt-3 pt-3 border-t border-gray-800 text-xs text-gray-500">
          <span>${formatDate(a.date) || timeAgo(a.scraped_at)}</span>
          <span class="text-gray-600">${a.source.replace('https://', '')}</span>
        </div>
      </a>
    `).join('');
  } catch (err) {
    document.getElementById('news-content').innerHTML =
      `<div class="col-span-full text-red-400 text-sm py-8 text-center">Error: ${err.message}</div>`;
    showToast('Failed to load news: ' + err.message, 'error');
  }
}
