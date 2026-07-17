import { useRef, useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { HiChevronLeft, HiChevronRight, HiOutlineArrowRight } from 'react-icons/hi'
import { useNavigate } from 'react-router-dom'
import MovieCard from './MovieCard'

export default function MovieRow({ title, movies, seeAllPath = '/browse' }) {
  const rowRef = useRef(null)
  const [showLeft, setShowLeft] = useState(false)
  const [showRight, setShowRight] = useState(true)
  const navigate = useNavigate()

  const scroll = (dir) => {
    const container = rowRef.current
    if (!container) return
    const scrollAmount = container.clientWidth * 0.75
    container.scrollBy({
      left: dir === 'left' ? -scrollAmount : scrollAmount,
      behavior: 'smooth',
    })
  }

  useEffect(() => {
    const container = rowRef.current
    if (!container) return
    const onScroll = () => {
      setShowLeft(container.scrollLeft > 10)
      setShowRight(container.scrollLeft < container.scrollWidth - container.clientWidth - 10)
    }
    container.addEventListener('scroll', onScroll)
    onScroll()
    return () => container.removeEventListener('scroll', onScroll)
  }, [movies])

  if (!movies?.length) return null

  return (
    <motion.section
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true, margin: '-50px' }}
      className="relative mb-6 group/row"
    >
      <div className="flex items-center justify-between px-8 lg:px-16 mb-2">
        <h2 className="text-base md:text-lg font-semibold text-white">
          {title}
        </h2>
        <button
          onClick={() => navigate(seeAllPath)}
          className="flex items-center gap-1 text-xs text-netflix-gray-light hover:text-white transition-colors opacity-0 group-hover/row:opacity-100"
        >
          See All <HiOutlineArrowRight size={14} />
        </button>
      </div>

      <div className="relative">
        {showLeft && (
          <button
            onClick={() => scroll('left')}
            className="absolute left-0 top-0 bottom-0 z-10 w-10 bg-black/60 opacity-0 group-hover/row:opacity-100 hover:bg-black/80 transition-opacity flex items-center justify-center"
          >
            <HiChevronLeft size={28} />
          </button>
        )}

        <div
          ref={rowRef}
          className="flex gap-2 overflow-x-auto px-8 lg:px-16 scrollbar-hide py-1"
        >
          {movies.slice(0, 10).map((movie, i) => (
            <MovieCard key={movie.id} movie={movie} index={i} />
          ))}

          <div
            className="flex-shrink-0 w-[140px] sm:w-[160px] md:w-[180px] cursor-pointer group/more"
            onClick={() => navigate(seeAllPath)}
          >
            <div className="relative overflow-hidden rounded-md aspect-[2/3] bg-netflix-dark border border-netflix-border hover:border-white/20 transition-colors">
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
                <div className="w-14 h-14 rounded-full border-2 border-netflix-gray-light group-hover/more:border-white group-hover/more:scale-110 transition-all flex items-center justify-center">
                  <HiOutlineArrowRight size={28} className="text-netflix-gray-light group-hover/more:text-white transition-colors" />
                </div>
                <span className="text-xs text-netflix-gray-light group-hover/more:text-white transition-colors font-medium">
                  See All
                </span>
              </div>
            </div>
            <div className="mt-2 px-0.5">
              <h3 className="text-[13px] font-medium text-netflix-gray-light truncate">
                More like this
              </h3>
            </div>
          </div>
        </div>

        {showRight && (
          <button
            onClick={() => scroll('right')}
            className="absolute right-0 top-0 bottom-0 z-10 w-10 bg-black/60 opacity-0 group-hover/row:opacity-100 hover:bg-black/80 transition-opacity flex items-center justify-center"
          >
            <HiChevronRight size={28} />
          </button>
        )}
      </div>
    </motion.section>
  )
}
