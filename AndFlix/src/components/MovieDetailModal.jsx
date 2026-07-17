import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { HiX, HiPlay, HiPlus, HiCheck } from 'react-icons/hi'
import { useNavigate } from 'react-router-dom'
import useWatchlistStore from '../store/watchlistStore'
import EpisodeSelector from './EpisodeSelector'

export default function MovieDetailModal({ movie, onClose }) {
  const navigate = useNavigate()
  const { isInList, toggle } = useWatchlistStore()

  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [])

  if (!movie) return null

  const inList = isInList(movie.id)
  const episodes = movie.episodeVo || []
  const genre = movie.tags?.[0] || movie.type || ''

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
        className="fixed inset-0 z-50 flex items-start justify-center pt-16 pb-8"
        onClick={onClose}
      >
        <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" />

        <motion.div
          initial={{ opacity: 0, y: 40, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 40, scale: 0.95 }}
          transition={{ duration: 0.3, type: 'spring', damping: 25 }}
          onClick={(e) => e.stopPropagation()}
          className="relative z-10 w-full max-w-4xl mx-4 bg-netflix-dark rounded-lg overflow-hidden max-h-[90vh] overflow-y-auto"
        >
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-20 p-2 bg-black/60 rounded-full hover:bg-black/80 transition-colors"
          >
            <HiX size={20} />
          </button>

          <div className="relative h-[400px]">
            {(movie.coverH || movie.cover) ? (
              <img
                src={movie.coverH || movie.cover}
                alt={movie.title}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full bg-netflix-darker" />
            )}
            <div className="absolute inset-0 bg-gradient-to-t from-netflix-dark via-transparent to-transparent" />
          </div>

          <div className="px-8 pb-8 -mt-20 relative z-10">
            <div className="flex items-center gap-4 mb-4">
              <button
                onClick={() => navigate(`/watch/${movie.id}`)}
                className="netflix-btn-primary"
              >
                <HiPlay size={22} />
                Play
              </button>
              <button
                onClick={() => toggle(movie)}
                className="p-2.5 rounded-full border-2 border-white/40 hover:border-white transition-colors"
              >
                {inList ? <HiCheck size={22} /> : <HiPlus size={22} />}
              </button>
            </div>

            <div className="flex items-center gap-3 text-sm mb-4">
              {movie.year && <span className="text-netflix-gray-light">{movie.year}</span>}
              {movie.score > 0 && (
                <span className="text-green-400 font-semibold">{movie.score.toFixed(1)}</span>
              )}
              {episodes.length > 0 && (
                <span className="text-netflix-gray-light">{episodes.length} Episodes</span>
              )}
              {genre && (
                <span className="px-2 py-0.5 border border-netflix-border rounded text-xs text-netflix-gray-light">
                  {genre}
                </span>
              )}
            </div>

            <p className="text-sm text-netflix-gray-light leading-relaxed mb-6">
              {movie.intro || 'No description available.'}
            </p>

            {movie.tags?.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-6">
                {movie.tags.map((t) => (
                  <span key={t} className="px-3 py-1 bg-netflix-light rounded-full text-xs text-netflix-gray-light">
                    {t}
                  </span>
                ))}
              </div>
            )}

            {episodes.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-3">Episodes</h3>
                <EpisodeSelector episodes={episodes} movieId={movie.id} />
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
