import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { HiTrash } from 'react-icons/hi'
import { useNavigate } from 'react-router-dom'
import MovieDetailModal from '../components/MovieDetailModal'
import Footer from '../components/Footer'
import useWatchlistStore from '../store/watchlistStore'
import useMovieStore from '../store/movieStore'

export default function MyListPage() {
  const { items, remove } = useWatchlistStore()
  const { fetchDetail, detail, setDetail, clearDetail } = useMovieStore()
  const navigate = useNavigate()
  const [selectedMovie, setSelectedMovie] = useState(null)

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
        <h1 className="text-2xl md:text-3xl font-bold mb-8">My List</h1>

        {items.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-20"
          >
            <p className="text-netflix-gray-light text-lg mb-2">Your list is empty</p>
            <p className="text-netflix-gray text-sm mb-6">
              Add movies to your list by clicking the + button
            </p>
            <button
              onClick={() => navigate('/browse')}
              className="netflix-btn-primary"
            >
              Browse Movies
            </button>
          </motion.div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            <AnimatePresence>
              {items.map((movie, i) => (
                <motion.div
                  key={movie.id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ delay: i * 0.03 }}
                  className="relative group cursor-pointer"
                  onClick={() => openDetail(movie)}
                >
                  <div className="relative overflow-hidden rounded-md aspect-[2/3] bg-netflix-dark">
                    {movie.cover ? (
                      <img
                        src={movie.cover}
                        alt={movie.title}
                        loading="lazy"
                        className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-netflix-gray text-sm">
                        No Image
                      </div>
                    )}

                    <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          remove(movie.id)
                        }}
                        className="p-2 bg-black/60 rounded-full hover:bg-netflix-red transition-colors"
                      >
                        <HiTrash size={14} />
                      </button>
                    </div>

                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <span className="text-sm font-semibold">More Info</span>
                    </div>
                  </div>

                  <div className="mt-2">
                    <h3 className="text-sm font-medium truncate">{movie.title}</h3>
                    <div className="flex items-center gap-2 text-xs text-netflix-gray-light mt-0.5">
                      {movie.score > 0 && (
                        <span className="text-green-400 font-semibold">
                          {movie.score.toFixed(1)}
                        </span>
                      )}
                      {movie.year && <span>{movie.year}</span>}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
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
