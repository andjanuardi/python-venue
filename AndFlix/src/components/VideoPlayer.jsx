import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { HiX } from 'react-icons/hi'
import useMovieStore from '../store/movieStore'
import Player from 'xgplayer'
import 'xgplayer/dist/index.min.css'
import HlsJsPlugin from 'xgplayer-hls.js'

const uid = () => Math.random().toString(36).slice(2, 9)

export default function VideoPlayer({ movieId, episodeId, onClose, subtitles }) {
  const containerId = useRef(`player-${uid()}`)
  const playerRef = useRef(null)
  const initRef = useRef(false)
  const { detail } = useMovieStore()
  const [playData, setPlayData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

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
        if (data.mediaUrl) setPlayData(data)
        else setError('Stream URL not available')
      } catch (e) {
        setError(e.message)
      }
      setLoading(false)
    }
    load()
  }, [movieId, episodeId])

  useEffect(() => {
    if (!playData?.mediaUrl || initRef.current) return
    initRef.current = true

    const allSubs = subtitles || playData?.subtitles || []

    const player = new Player({
      id: containerId.current,
      url: playData.mediaUrl,
      autoplay: true,
      playsinline: true,
      volume: 0.5,
      plugins: [HlsJsPlugin],
      hlsJsPlugin: {},
      texttrack: {
        list: allSubs.map(s => ({
          label: s.language,
          language: s.languageAbbr,
          url: s.url,
        })),
      },
      definition: {
        position: 'controlsRight',
        list: (playData?.qualities || []).map(q => ({
          name: q.name,
          url: q.url,
        })),
      },
    })

    player.on('error', (err) => {
      setError(err?.message || 'Playback error')
    })

    player.on('canplay', () => {
      const tt = player.plugins?.texttrack
      if (tt && tt.config?.list?.length > 0) {
        tt.renderItemList()
        tt.show()
      }
    })

    playerRef.current = player

    return () => {
      player.destroy()
      playerRef.current = null
      initRef.current = false
    }
  }, [playData, subtitles])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-black"
    >
      <div className="absolute top-0 left-0 right-0 z-20 flex items-center gap-3 p-4 bg-gradient-to-b from-black/60 to-transparent pointer-events-none">
        <button
          onClick={onClose}
          className="pointer-events-auto p-2 hover:bg-white/10 rounded-full transition-colors"
        >
          <HiX size={24} />
        </button>
        <span className="text-lg font-semibold text-white drop-shadow-lg">
          {detail?.title || `Movie #${movieId}`}
        </span>
      </div>

      <div className="w-full h-full flex items-center justify-center">
        {loading ? (
          <div className="w-12 h-12 border-4 border-netflix-red border-t-transparent rounded-full animate-spin" />
        ) : error ? (
          <div className="text-center text-netflix-gray-light">
            <p className="mb-4">{error}</p>
            <button onClick={onClose} className="netflix-btn-primary">Back</button>
          </div>
        ) : playData?.mediaUrl ? (
          <div id={containerId.current} className="w-full h-full" />
        ) : null}
      </div>
    </motion.div>
  )
}
