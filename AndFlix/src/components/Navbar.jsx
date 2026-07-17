import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { HiSearch, HiX } from 'react-icons/hi'
import { useNavigate, useLocation } from 'react-router-dom'
import { searchMovies } from '../api/client'

const NAV_LINKS = [
  { label: 'Home', path: '/' },
  { label: 'Browse', path: '/browse' },
  { label: 'My List', path: '/mylist' },
]

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const inputRef = useRef(null)
  const dropdownRef = useRef(null)
  const debounceRef = useRef(null)
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 50)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    if (searchOpen && inputRef.current) inputRef.current.focus()
  }, [searchOpen])

  useEffect(() => {
    const close = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setSearchOpen(false)
        setQuery('')
        setResults([])
      }
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])

  const doSearch = useCallback((q) => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (!q || q.length < 2) {
      setResults([])
      setLoading(false)
      return
    }
    setLoading(true)
    debounceRef.current = setTimeout(async () => {
      try {
        const data = await searchMovies(q)
        setResults(data.results || [])
      } catch {
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 300)
  }, [])

  const handleQuery = (val) => {
    setQuery(val)
    doSearch(val)
  }

  const goToMovie = (id) => {
    navigate(`/watch/${id}`)
    setSearchOpen(false)
    setQuery('')
    setResults([])
  }

  return (
    <motion.nav
      initial={{ y: -80 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className={`fixed top-0 left-0 right-0 z-50 transition-colors duration-300 ${
        scrolled ? 'bg-netflix-black/95 backdrop-blur-sm' : 'bg-gradient-to-b from-black/80 to-transparent'
      }`}
    >
      <div className="flex items-center justify-between px-8 lg:px-16 h-16">
        <div className="flex items-center gap-8">
          <a
            onClick={() => navigate('/')}
            className="text-netflix-red text-3xl font-bold tracking-tight cursor-pointer hover:text-netflix-red-hover transition-colors"
          >
            AndFlix
          </a>
          <div className="hidden md:flex items-center gap-5">
            {NAV_LINKS.map((link) => (
              <a
                key={link.path}
                onClick={() => navigate(link.path)}
                className={`text-sm font-medium cursor-pointer transition-colors ${
                  location.pathname === link.path
                    ? 'text-white'
                    : 'text-netflix-gray-light hover:text-white'
                }`}
              >
                {link.label}
              </a>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-4 relative" ref={dropdownRef}>
          <AnimatePresence>
            {searchOpen && (
              <motion.div
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: 280, opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="overflow-hidden"
              >
                <div className="relative">
                  <HiSearch size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-netflix-gray" />
                  <input
                    ref={inputRef}
                    type="text"
                    value={query}
                    onChange={(e) => handleQuery(e.target.value)}
                    placeholder="Search movies..."
                    className="w-full bg-netflix-dark border border-netflix-border rounded pl-9 pr-8 py-2 text-sm text-white placeholder-netflix-gray focus:outline-none focus:border-white/50"
                  />
                  <button
                    onClick={() => { setSearchOpen(false); setQuery(''); setResults([]) }}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-netflix-gray hover:text-white"
                  >
                    <HiX size={16} />
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {!searchOpen && (
            <button
              onClick={() => setSearchOpen(true)}
              className="text-white hover:text-netflix-gray-light transition-colors"
            >
              <HiSearch size={22} />
            </button>
          )}

          <AnimatePresence>
            {searchOpen && query.length >= 2 && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="absolute top-full right-0 mt-2 w-80 bg-netflix-dark border border-netflix-border rounded-lg shadow-2xl overflow-hidden max-h-[400px] overflow-y-auto"
              >
                {loading ? (
                  <div className="p-4 text-center text-netflix-gray text-sm">Searching...</div>
                ) : results.length === 0 ? (
                  <div className="p-4 text-center text-netflix-gray text-sm">No results found</div>
                ) : (
                  results.map((m) => (
                    <div
                      key={m.id}
                      onClick={() => goToMovie(m.id)}
                      className="flex items-center gap-3 p-3 hover:bg-netflix-light cursor-pointer transition-colors"
                    >
                      {m.cover ? (
                        <img src={m.cover} alt={m.title} className="w-10 h-14 object-cover rounded flex-shrink-0" />
                      ) : (
                        <div className="w-10 h-14 bg-netflix-light rounded flex-shrink-0" />
                      )}
                      <div className="min-w-0">
                        <p className="text-sm text-white truncate">{m.title}</p>
                        <div className="flex items-center gap-2 text-xs text-netflix-gray-light">
                          {m.score > 0 && <span className="text-green-400">{m.score.toFixed(1)}</span>}
                          {m.year && <span>{m.year}</span>}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.nav>
  )
}
