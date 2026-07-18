import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { HiSearch, HiX, HiRefresh, HiPlus } from 'react-icons/hi'
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
  const [movieCount, setMovieCount] = useState(0)
  const [scanData, setScanData] = useState(null)
  const [scanning, setScanning] = useState(false)
  const [showScanPopup, setShowScanPopup] = useState(false)
  const [showAddPopup, setShowAddPopup] = useState(false)
  const [addId, setAddId] = useState('')
  const [addMsg, setAddMsg] = useState('')
  const [addOk, setAddOk] = useState(false)
  const [loadingAdd, setLoadingAdd] = useState(false)

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

  useEffect(() => {
    if (!scanning) return
    const poll = async () => {
      try {
        const r = await fetch('/api/scan/status')
        const d = await r.json()
        setScanData(d)
        if (!d.running) {
          setScanning(false)
          setTimeout(() => { setShowScanPopup(false); setScanData(null) }, 3000)
        }
      } catch {}
    }
    const id = setInterval(poll, 1500)
    return () => clearInterval(id)
  }, [scanning])

  useEffect(() => {
    fetch('/api/movies/count').then(r => r.json()).then(d => setMovieCount(d.count)).catch(() => {})
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

  const handleAddById = async (e) => {
    e.preventDefault()
    if (!addId.trim()) return
    setLoadingAdd(true)
    setAddMsg('')
    try {
      const r = await fetch(`/api/movies/add/${addId.trim()}`, { method: 'POST' })
      const data = await r.json()
      setAddOk(r.ok)
      setAddMsg(r.ok ? `\u2713 ${data.data.title}` : data.error)
      if (r.ok) {
        setMovieCount(c => c + 1)
        setTimeout(() => { setShowAddPopup(false); setAddId('') }, 1200)
      }
    } catch {
      setAddOk(false)
      setAddMsg('Network error')
    }
    setLoadingAdd(false)
    setTimeout(() => setAddMsg(''), 4000)
  }

  const handleScan = async () => {
    setShowScanPopup(true)
    setScanData({ running: true, total: 0, done: 0, new: 0, errors: 0 })
    setScanning(true)
    try {
      const r = await fetch('/api/scan')
      setScanData(await r.json())
    } catch {}
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
          {movieCount > 0 && (
            <span className="hidden sm:inline text-xs text-netflix-gray-light whitespace-nowrap">{movieCount.toLocaleString()} movies</span>
          )}

          <div className="relative">
            <button
              onClick={() => setShowAddPopup(!showAddPopup)}
              className="p-2 hover:bg-white/10 rounded-full transition-colors"
              title="Add by ID"
            >
              <HiPlus size={22} className="text-white" />
            </button>
            <AnimatePresence>
              {showAddPopup && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="absolute top-full right-0 mt-2 w-48 bg-netflix-dark border border-netflix-border rounded-lg shadow-2xl p-4 z-50"
                >
                  <form onSubmit={handleAddById} className="flex flex-col gap-2">
                    <input
                      type="number"
                      placeholder="Movie ID"
                      value={addId}
                      onChange={e => setAddId(e.target.value)}
                      autoFocus
                      className="w-full bg-netflix-light rounded px-3 py-1.5 text-sm text-white placeholder-netflix-gray focus:outline-none focus:border-white/50"
                    />
                    <button
                      type="submit"
                      disabled={loadingAdd}
                      className="w-full py-1.5 bg-netflix-red hover:bg-red-700 rounded text-sm font-medium transition-colors disabled:opacity-50"
                    >
                      {loadingAdd ? 'Adding...' : 'Add Movie'}
                    </button>
                  </form>
                  {addMsg && (
                    <p className={`text-xs mt-2 text-center ${addOk ? 'text-green-400' : 'text-red-400'}`}>
                      {addMsg}
                    </p>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="relative">
            <button
              onClick={handleScan}
              className="p-2 hover:bg-white/10 rounded-full transition-colors relative"
              title={scanning ? 'Scanning...' : 'Scan movies'}
            >
              <motion.div
                animate={scanning ? { rotate: 360 } : {}}
                transition={scanning ? { repeat: Infinity, duration: 2, ease: 'linear' } : {}}
                className="flex"
              >
                <HiRefresh size={20} className={scanning ? 'text-netflix-red' : 'text-white'} />
              </motion.div>
              {scanning && scanData?.total > 0 && (
                <span className="absolute -bottom-0.5 -right-0.5 text-[10px] bg-netflix-red text-white rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1 font-medium leading-none">
                  {scanData.done}/{scanData.total}
                </span>
              )}
            </button>

            <AnimatePresence>
              {showScanPopup && scanData && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="absolute top-full right-0 mt-2 w-56 bg-netflix-dark border border-netflix-border rounded-lg shadow-2xl p-4 z-50"
                >
                  <p className="text-sm font-medium mb-2">
                    {scanData.running ? 'Scanning...' : 'Scan Complete'}
                  </p>
                  {scanData.total > 0 && (
                    <>
                      <div className="h-1.5 bg-netflix-light rounded-full overflow-hidden mb-2">
                        <motion.div
                          className="h-full bg-netflix-red rounded-full"
                          animate={{ width: `${Math.round((scanData.done / scanData.total) * 100)}%` }}
                          transition={{ duration: 0.3 }}
                        />
                      </div>
                      <div className="flex justify-between text-xs text-netflix-gray-light">
                        <span>{scanData.done}/{scanData.total}</span>
                        <span>New: {scanData.new}</span>
                        <span>Errors: {scanData.errors}</span>
                      </div>
                    </>
                  )}
                  {!scanData.running && scanData.done > 0 && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-green-400 text-xs mt-2 text-center"
                    >
                      ✓ {scanData.new} movies added
                    </motion.p>
                  )}
                  {!scanData.running && scanData.total === 0 && !scanning && (
                    <p className="text-netflix-gray-light text-xs mt-1 text-center">No new data to scan</p>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

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
