import { useState } from "react";
import { motion } from "framer-motion";
import { HiPlay, HiPlus, HiCheck } from "react-icons/hi";
import { useNavigate } from "react-router-dom";
import useWatchlistStore from "../store/watchlistStore";

export default function MovieCard({ movie, index = 0 }) {
  const [hovered, setHovered] = useState(false);
  const [imgLoaded, setImgLoaded] = useState(false);
  const navigate = useNavigate();
  const { isInList, toggle } = useWatchlistStore();
  const inList = isInList(movie.id);
  const isHD = movie.score >= 8.0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      className="relative flex-shrink-0 w-[140px] sm:w-[160px] md:w-[180px] cursor-pointer group"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={() => navigate(`/watch/${movie.id}`)}
    >
      <motion.div
        animate={{
          scale: hovered ? 1.08 : 1,
          zIndex: hovered ? 10 : 1,
        }}
        transition={{ duration: 0.2 }}
        className="relative"
      >
        <div className="relative overflow-hidden rounded-md aspect-[2/3] bg-netflix-dark">
          {movie.cover ? (
            <img
              src={movie.cover}
              alt={movie.title}
              loading="lazy"
              onLoad={() => setImgLoaded(true)}
              className={`w-full h-full object-cover transition-all duration-300 group-hover:scale-105 ${
                imgLoaded ? "opacity-100" : "opacity-0"
              }`}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-netflix-gray text-xs">
              No Image
            </div>
          )}

          {isHD && (
            <div className="absolute top-1.5 left-1.5 bg-netflix-red/90 text-white text-[9px] font-bold px-1.5 py-0.5 rounded tracking-wider">
              HD
            </div>
          )}

          <motion.div
            initial={false}
            animate={{ opacity: hovered ? 1 : 0 }}
            transition={{ duration: 0.15 }}
            className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent"
          />

          <motion.div
            initial={false}
            animate={{ opacity: hovered ? 1 : 0 }}
            transition={{ duration: 0.15 }}
            className="absolute inset-0 flex items-center justify-center"
          >
            <motion.div
              animate={{ scale: hovered ? 1 : 0.5 }}
              transition={{ duration: 0.15 }}
              className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center"
            >
              <HiPlay size={28} className="text-white ml-0.5" />
            </motion.div>
          </motion.div>
        </div>

        <div className="mt-2 px-0.5">
          <h3 className="text-[13px] font-medium text-white truncate leading-tight">
            {movie.title}
          </h3>
          <div className="flex items-center gap-2 mt-1 text-xs text-netflix-gray-light">
            {movie.score > 0 && (
              <span className="text-green-400 font-semibold">
                {movie.score.toFixed(1)}
              </span>
            )}
            {movie.year && <span>{movie.year}</span>}
          </div>

          <motion.div
            initial={false}
            animate={{
              opacity: hovered ? 1 : 0,
              height: hovered ? "auto" : 0,
            }}
            transition={{ duration: 0.15 }}
            className="overflow-hidden absolute top-4 right-3"
          >
            <div className="flex items-center gap-1.5 mt-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  toggle(movie);
                }}
                className="p-1.5 rounded-full border border-white/40 hover:border-white hover:bg-white/10 transition-colors"
              >
                {inList ? (
                  <HiCheck size={12} className="text-white" />
                ) : (
                  <HiPlus size={12} className="text-white" />
                )}
              </button>
            </div>
          </motion.div>
        </div>
      </motion.div>
    </motion.div>
  );
}
