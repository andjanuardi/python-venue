import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import Footer from '../components/Footer'
import MovieCard from '../components/MovieCard'
import MovieDetailModal from '../components/MovieDetailModal'
import useMovieStore from '../store/movieStore'

const CATEGORIES = [
  { id: 1, label: 'Series' },
  { id: 2, label: 'Movies' },
  { id: 3, label: 'Anime' },
  { id: 119, label: 'Trending' },
  { id: 120, label: 'New Releases' },
  { id: 165, label: 'Popular' },
]

export default function BrowsePage() {
  const { browseData, fetchBrowse, loading, detail, fetchDetail, clearDetail } = useMovieStore()
  const [activeCat, setActiveCat] = useState(2)
  const [selectedMovie, setSelectedMovie] = useState(null)

  useEffect(() => {
    fetchBrowse(activeCat)
  }, [activeCat])

  const openDetail = async (movie) => {
    await fetchDetail(movie.id)
    setSelectedMovie(movie)
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="min-h-screen bg-netflix-black pt-24"
    >
      <div className="px-8 lg:px-16">
        <h1 className="text-2xl md:text-3xl font-bold mb-6">Browse</h1>

        <div className="flex flex-wrap gap-2 mb-8">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCat(cat.id)}
              className={`px-5 py-2 rounded-full text-sm font-medium transition-all ${
                activeCat === cat.id
                  ? 'bg-netflix-red text-white'
                  : 'bg-netflix-dark text-netflix-gray-light border border-netflix-border hover:bg-netflix-light'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {Array.from({ length: 18 }).map((_, i) => (
              <div key={i} className="skeleton aspect-[2/3] rounded-md" />
            ))}
          </div>
        ) : browseData?.items?.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-netflix-gray-light text-lg">No movies in this category</p>
          </div>
        ) : (
          <>
            {browseData && (
              <p className="text-sm text-netflix-gray mb-4">
                {browseData.title} &middot; {browseData.items?.length || 0} titles
              </p>
            )}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {browseData?.items?.map((movie, i) => (
                <div key={movie.id} onClick={() => openDetail(movie)}>
                  <MovieCard movie={movie} index={i} />
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      <div className="mt-12">
        <Footer />
      </div>

      {selectedMovie && detail && (
        <MovieDetailModal
          movie={detail}
          onClose={() => { setSelectedMovie(null); clearDetail() }}
        />
      )}
    </motion.div>
  )
}
