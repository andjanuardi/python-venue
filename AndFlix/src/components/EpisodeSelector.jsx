import { useState } from 'react'
import { motion } from 'framer-motion'
import { HiPlay } from 'react-icons/hi'
import { useNavigate } from 'react-router-dom'

export default function EpisodeSelector({ episodes, movieId }) {
  const navigate = useNavigate()
  const [selected, setSelected] = useState(0)

  if (!episodes?.length) return null

  const QUALITY_LABELS = {
    GROOT_HD: 'HD',
    GROOT_SD: 'SD',
    GROOT_LD: 'LD',
    GROOT_FD: 'FD',
  }

  return (
    <div className="space-y-2 max-h-64 overflow-y-auto pr-2">
      {episodes.map((ep, i) => {
        const bestDef = ep.definitionList?.[0]?.code
        return (
          <motion.div
            key={ep.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.03 }}
            className={`flex items-center gap-4 p-3 rounded-md cursor-pointer transition-colors ${
              selected === i
                ? 'bg-netflix-light/50 border border-netflix-red/50'
                : 'bg-netflix-darker hover:bg-netflix-light/30 border border-transparent'
            }`}
            onClick={() => setSelected(i)}
            onDoubleClick={() => navigate(`/watch/${movieId}?episode=${ep.id}`)}
          >
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-netflix-light text-sm font-bold text-netflix-gray-light shrink-0">
              {ep.seriesNo || i + 1}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">
                {ep.name || `Episode ${ep.seriesNo || i + 1}`}
              </p>
              <div className="flex items-center gap-2 mt-0.5">
                {ep.viewable !== false && (
                  <span className="text-xs text-green-400">Available</span>
                )}
                {bestDef && (
                  <span className="text-[10px] px-1.5 py-0.5 bg-netflix-light rounded text-netflix-gray-light uppercase">
                    {QUALITY_LABELS[bestDef] || bestDef}
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation()
                navigate(`/watch/${movieId}?episode=${ep.id}`)
              }}
              className="p-2 hover:bg-white/10 rounded-full transition-colors"
            >
              <HiPlay size={18} className="text-netflix-gray-light" />
            </button>
          </motion.div>
        )
      })}
    </div>
  )
}
