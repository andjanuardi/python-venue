const BASE = '/api'

async function fetchJSON(url, options = {}) {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error || `HTTP ${res.status}`)
  }
  return res.json()
}

export const browseMovies = (pageId) => fetchJSON(`/movie/browse/${pageId}`)

export const getHome = () => fetchJSON('/home')

export const getMovieDetail = (id) => fetchJSON(`/movies/${id}`)

export const getPlayInfo = (movieId, episodeId, quality = 'GROOT_SD') =>
  fetchJSON(`/movies/${movieId}/play?episodeId=${episodeId}&quality=${quality}`)

export const searchMovies = (query) =>
  fetchJSON(`/search?q=${encodeURIComponent(query)}`)
