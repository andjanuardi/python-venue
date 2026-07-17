import { create } from 'zustand'
import * as api from '../api/client'

const useMovieStore = create((set) => ({
  homeSections: [],
  browseData: null,
  detail: null,
  loading: false,
  error: null,

  fetchHome: async () => {
    set({ loading: true, error: null })
    try {
      const result = await api.getHome()
      set({ homeSections: result.sections || [], loading: false })
      return result
    } catch (e) {
      set({ error: e.message, loading: false })
      return null
    }
  },

  fetchBrowse: async (pageId) => {
    set({ loading: true, error: null, browseData: null })
    try {
      const result = await api.browseMovies(pageId)
      set({ browseData: result, loading: false })
      return result
    } catch (e) {
      set({ error: e.message, loading: false })
      return null
    }
  },

  fetchDetail: async (id) => {
    set({ loading: true, error: null })
    try {
      const result = await api.getMovieDetail(id)
      if (result?.data) {
        set({ detail: result.data, loading: false })
        return result.data
      }
      set({ loading: false })
      return null
    } catch (e) {
      set({ error: e.message, loading: false })
      return null
    }
  },

  clearDetail: () => set({ detail: null }),
}))

export default useMovieStore
