import { create } from 'zustand'

const STORAGE_KEY = 'andflix_watchlist'

const loadWatchlist = () => {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    return data ? JSON.parse(data) : []
  } catch {
    return []
  }
}

const saveWatchlist = (items) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
  } catch {}
}

const useWatchlistStore = create((set, get) => ({
  items: loadWatchlist(),

  add: (movie) => {
    const exists = get().items.find((m) => m.id === movie.id)
    if (exists) return
    const item = {
      id: movie.id,
      title: movie.title,
      cover: movie.cover || movie.coverH || '',
      score: movie.score,
      year: movie.year,
      addedAt: Date.now(),
    }
    const items = [item, ...get().items]
    set({ items })
    saveWatchlist(items)
  },

  remove: (id) => {
    const items = get().items.filter((m) => m.id !== id)
    set({ items })
    saveWatchlist(items)
  },

  isInList: (id) => get().items.some((m) => m.id === id),

  toggle: (movie) => {
    if (get().isInList(movie.id)) {
      get().remove(movie.id)
    } else {
      get().add(movie)
    }
  },
}))

export default useWatchlistStore
