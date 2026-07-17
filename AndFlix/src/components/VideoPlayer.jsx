import { useEffect, useRef, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { HiX, HiMenuAlt4, HiChevronDown } from 'react-icons/hi'
import useMovieStore from '../store/movieStore'

export default function VideoPlayer({ movieId, episodeId, onClose, subtitles }) {
  const videoRef = useRef(null)
  const playerRef = useRef(null)
  const containerRef = useRef(null)
  const { detail, fetchDetail } = useMovieStore()
  const [playData, setPlayData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showControls, setShowControls] = useState(true)
  const [subMenuOpen, setSubMenuOpen] = useState(false)
  const [activeSub, setActiveSub] = useState(null)
  const hideTimer = useRef(null)

  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [])

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const res = await fetch(`/api/movies/${movieId}/play?episodeId=${episodeId}&quality=GROOT_SD`)
        const data = await res.json()
        if (data.mediaUrl) {
          setPlayData(data)
        } else {
          setError('Stream URL not available')
        }
      } catch (e) {
        setError(e.message)
      }
      setLoading(false)
    }
    load()
  }, [movieId, episodeId])

  useEffect(() => {
    if (subtitles?.length && !activeSub) {
      setActiveSub(subtitles[0])
    }
  }, [subtitles])

  useEffect(() => {
    if (playData?.subtitles?.length && !subtitles && !activeSub) {
      setActiveSub(playData.subtitles[0])
    }
  }, [playData])

  const subtitlesSource = subtitles || playData?.subtitles || []

  const handleMouseMove = useCallback(() => {
    setShowControls(true)
    clearTimeout(hideTimer.current)
    hideTimer.current = setTimeout(() => setShowControls(false), 3000)
  }, [])

  useEffect(() => {
    return () => clearTimeout(hideTimer.current)
  }, [])

  const selectSub = (sub) => {
    setActiveSub(sub)
    setSubMenuOpen(false)
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-black"
      ref={containerRef}
      onMouseMove={handleMouseMove}
    >
      <AnimatePresence>
        {showControls && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="absolute top-0 left-0 right-0 z-20 bg-gradient-to-b from-black/80 to-transparent px-6 py-4"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-white/10 rounded-full transition-colors"
                >
                  <HiX size={24} />
                </button>
                <span className="text-lg font-semibold">
                  {detail?.title || `Movie #${movieId}`}
                </span>
                {episodeId && detail?.episodeVo && (
                  <span className="text-sm text-netflix-gray-light">
                    — Ep.{' '}
                    {detail.episodeVo.find((e) => e.id === episodeId)?.seriesNo || ''}
                  </span>
                )}
              </div>

              <div className="relative">
                <button
                  onClick={() => setSubMenuOpen(!subMenuOpen)}
                  className="flex items-center gap-2 px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded transition-colors text-sm"
                >
                  <HiMenuAlt4 size={18} />
                  <span>{activeSub?.language || 'Subtitles'}</span>
                  <HiChevronDown size={14} className={`transition-transform ${subMenuOpen ? 'rotate-180' : ''}`} />
                </button>
                <AnimatePresence>
                  {subMenuOpen && subtitlesSource.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="absolute right-0 top-12 w-56 bg-netflix-dark border border-netflix-border rounded-lg overflow-hidden shadow-xl"
                    >
                      <div className="p-2">
                        <button
                          onClick={() => { setActiveSub(null); setSubMenuOpen(false) }}
                          className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                            !activeSub ? 'bg-netflix-red/20 text-netflix-red' : 'hover:bg-netflix-light'
                          }`}
                        >
                          Off
                        </button>
                        {subtitlesSource.map((sub, i) => (
                          <button
                            key={i}
                            onClick={() => selectSub(sub)}
                            className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                              activeSub?.url === sub.url
                                ? 'bg-netflix-red/20 text-netflix-red'
                                : 'hover:bg-netflix-light'
                            }`}
                          >
                            <span className="block">{sub.language}</span>
                            <span className="block text-xs text-netflix-gray">
                              {sub.languageAbbr}
                            </span>
                          </button>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="w-full h-full flex items-center justify-center">
        {loading ? (
          <div className="flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-4 border-netflix-red border-t-transparent rounded-full animate-spin" />
            <p className="text-netflix-gray-light text-sm">Loading stream...</p>
          </div>
        ) : error ? (
          <div className="text-center">
            <p className="text-netflix-gray-light mb-4">{error}</p>
            <button onClick={onClose} className="netflix-btn-primary">
              Back
            </button>
          </div>
        ) : playData?.mediaUrl ? (
          <video
            ref={videoRef}
            className="w-full h-full"
            controls
            autoPlay
            playsInline
          >
            <source src={playData.mediaUrl} />
            {activeSub && activeSub.url && (
              <track
                kind="subtitles"
                src={activeSub.url}
                srcLang={activeSub.languageAbbr || 'en'}
                label={activeSub.language || 'Subtitles'}
                default
              />
            )}
          </video>
        ) : (
          <p className="text-netflix-gray-light">No media available</p>
        )}
      </div>

      <AnimatePresence>
        {showControls && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="absolute bottom-0 left-0 right-0 z-20 bg-gradient-to-t from-black/80 to-transparent px-6 py-4"
          >
            <div className="flex items-center gap-3 text-sm text-netflix-gray-light">
              {playData?.currentDefinition && (
                <span className="px-2 py-0.5 bg-white/10 rounded text-xs uppercase">
                  {playData.currentDefinition.replace('GROOT_', '')}
                </span>
              )}
              {playData?.totalDuration && (
                <span>
                  {Math.floor(playData.totalDuration / 60)}m
                </span>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
