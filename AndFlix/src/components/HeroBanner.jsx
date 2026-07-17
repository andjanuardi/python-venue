import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { HiPlay, HiPlus, HiCheck } from "react-icons/hi";
import { useNavigate } from "react-router-dom";
import useWatchlistStore from "../store/watchlistStore";

export default function HeroBanner({ movies = [] }) {
  const navigate = useNavigate();
  const { isInList, toggle } = useWatchlistStore();
  const [currentIdx, setCurrentIdx] = useState(0);
  const [imgLoaded, setImgLoaded] = useState(false);

  const topMovies = movies.filter((m) => m.cover).slice(0, 5);
  const movie = topMovies[currentIdx];

  const rotate = useCallback(() => {
    setCurrentIdx((prev) => (prev + 1) % topMovies.length);
    setImgLoaded(false);
  }, [topMovies.length]);

  useEffect(() => {
    if (topMovies.length <= 1) return;
    const timer = setInterval(rotate, 8000);
    return () => clearInterval(timer);
  }, [rotate, topMovies.length]);

  useEffect(() => {
    setImgLoaded(false);
  }, [currentIdx]);

  if (!movie) return null;

  const inList = isInList(movie.id);
  const coverUrl = movie.coverH || movie.cover || "";

  const scoreColor =
    movie.score >= 8
      ? "text-green-400"
      : movie.score >= 6
        ? "text-yellow-400"
        : "text-netflix-gray-light";

  return (
    <div className="relative h-[80vh] min-h-[500px] w-full overflow-hidden">
      <AnimatePresence mode="wait">
        <motion.div
          key={movie.id}
          initial={{ opacity: 0, scale: 1.05 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1 }}
          className="absolute inset-0"
        >
          {coverUrl && (
            <img
              src={coverUrl}
              alt={movie.title}
              onLoad={() => setImgLoaded(true)}
              className={`w-full h-full object-cover transition-opacity duration-700 ${
                imgLoaded ? "opacity-100" : "opacity-0"
              }`}
            />
          )}
          <div className="absolute inset-0 bg-gradient-to-r from-netflix-black via-netflix-black/60 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-t from-netflix-black via-netflix-black/30 to-transparent" />
        </motion.div>
      </AnimatePresence>

      <motion.div
        key={`content-${movie.id}`}
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
        className="relative z-10 flex flex-col justify-end h-full pb-24 px-8 lg:px-16 max-w-2xl"
      >
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-4 drop-shadow-lg"
        >
          {movie.title}
        </motion.h1>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="flex items-center gap-3 text-sm text-netflix-gray-light mb-4"
        >
          {movie.score > 0 && (
            <span
              className={`inline-flex items-center gap-1.5 font-bold ${scoreColor}`}
            >
              <span className="w-8 h-8 rounded-full border-2 border-current flex items-center justify-center text-xs">
                {movie.score.toFixed(0)}
              </span>
              {movie.score.toFixed(1)}
            </span>
          )}
          {movie.year && <span>{movie.year}</span>}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="flex items-center gap-3"
        >
          <button
            onClick={() => navigate(`/watch/${movie.id}`)}
            className="netflix-btn-primary text-lg"
          >
            <HiPlay size={24} />
            Play
          </button>
          <button
            onClick={() => toggle(movie)}
            className="netflix-btn-secondary border border-white/30"
          >
            {inList ? <HiCheck size={22} /> : <HiPlus size={22} />}
            My List
          </button>
        </motion.div>
      </motion.div>

      {topMovies.length > 1 && (
        <div className="absolute bottom-24 right-8 lg:right-16 z-10 flex items-center gap-2">
          {topMovies.map((m, i) => (
            <button
              key={m.id}
              onClick={() => {
                setCurrentIdx(i);
                setImgLoaded(false);
              }}
              className={`transition-all duration-300 ${
                i === currentIdx
                  ? "w-8 h-1 bg-white rounded-full"
                  : "w-4 h-1 bg-white/30 hover:bg-white/50 rounded-full"
              }`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
