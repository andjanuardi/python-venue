import { useEffect, useState } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { HiChevronLeft, HiPlay } from 'react-icons/hi'
import VideoPlayer from '../components/VideoPlayer'
import EpisodeSelector from '../components/EpisodeSelector'
import useMovieStore from '../store/movieStore'
import useWatchlistStore from '../store/watchlistStore'

export default function WatchPage() {
  const { id } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const episodeParam = searchParams.get('episode')

  const { detail, fetchDetail, loading } = useMovieStore()
  const { items: watchlist } = useWatchlistStore()

  const [showPlayer, setShowPlayer] = useState(false)
  const [selectedEpisode, setSelectedEpisode] = useState(null)
  const [activeEpisode, setActiveEpisode] = useState(null)

  useEffect(() => {
    fetchDetail(id)
  }, [id])

  useEffect(() => {
    if (detail?.episodeVo?.length) {
      if (episodeParam) {
        const ep = detail.episodeVo.find((e) => e.id === parseInt(episodeParam))
        if (ep) {
          setSelectedEpisode(ep)
          setActiveEpisode(ep)
        }
      } else {
        setSelectedEpisode(detail.episodeVo[0])
        setActiveEpisode(detail.episodeVo[0])
      }
    }
  }, [detail, episodeParam])

  if (loading || !detail) {
    return (
      <div className="min-h-screen bg-netflix-black pt-16 px-8 lg:px-16">
        <div className="skeleton h-8 w-64 mb-6" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 skeleton aspect-video rounded-lg" />
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="skeleton h-16 rounded" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  const episodes = detail.episodeVo || []

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="min-h-screen bg-netflix-black"
    >
      <div className="px-8 lg:px-16 pt-20 pb-8">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-netflix-gray-light hover:text-white transition-colors mb-4"
        >
          <HiChevronLeft size={22} />
          <span>Back</span>
        </button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            {!showPlayer ? (
              <div className="relative aspect-video bg-netflix-darker rounded-lg overflow-hidden group cursor-pointer" onClick={() => setShowPlayer(true)}>
                {detail.coverH || detail.cover ? (
                  <img
                    src={detail.coverH || detail.cover}
                    alt={detail.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-netflix-gray">
                    No Preview
                  </div>
                )}
                <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="w-16 h-16 bg-netflix-red rounded-full flex items-center justify-center">
                    <HiPlay size={32} className="ml-1" />
                  </div>
                </div>
                <div className="absolute bottom-4 left-4">
                  <p className="text-lg font-semibold drop-shadow-lg">{detail.title}</p>
                  {activeEpisode && (
                    <p className="text-sm text-netflix-gray-light">
                      Ep. {activeEpisode.seriesNo} — {activeEpisode.name}
                    </p>
                  )}
                </div>
              </div>
            ) : (
              activeEpisode && (
                <VideoPlayer
                  movieId={id}
                  episodeId={activeEpisode.id}
                  onClose={() => setShowPlayer(false)}
                  subtitles={activeEpisode.subtitle_url ? [
                    ...(activeEpisode.subtitle_url.id ? [{ url: activeEpisode.subtitle_url.id, language: 'Bahasa Indonesia', languageAbbr: 'id' }] : []),
                    ...(activeEpisode.subtitle_url.en ? [{ url: activeEpisode.subtitle_url.en, language: 'English', languageAbbr: 'en' }] : []),
                  ] : undefined}
                />
              )
            )}

            <div className="mt-6">
              <h1 className="text-2xl font-bold">{detail.title}</h1>
              {detail.score > 0 && (
                <span className="text-green-400 font-semibold text-sm mr-3">
                  {detail.score.toFixed(1)}
                </span>
              )}
              {detail.year && (
                <span className="text-netflix-gray-light text-sm mr-3">{detail.year}</span>
              )}
              {detail.type && (
                <span className="text-netflix-gray-light text-sm">{detail.type}</span>
              )}
              <p className="text-netflix-gray-light text-sm mt-3 leading-relaxed">
                {detail.intro || 'No description available.'}
              </p>
              {detail.tags?.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-4">
                  {detail.tags.map((t) => (
                    <span key={t} className="px-3 py-1 bg-netflix-light rounded-full text-xs text-netflix-gray-light">
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div>
            <h2 className="text-lg font-semibold mb-4">
              Episodes ({episodes.length})
            </h2>
            <EpisodeSelector
              episodes={episodes}
              movieId={parseInt(id)}
            />
          </div>
        </div>
      </div>
    </motion.div>
  )
}
