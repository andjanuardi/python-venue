import { useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import HeroBanner from "../components/HeroBanner";
import MovieRow from "../components/MovieRow";
import Footer from "../components/Footer";
import useMovieStore from "../store/movieStore";

export default function HomePage() {
  const { homeSections, fetchHome, loading } = useMovieStore();

  useEffect(() => {
    window.scrollTo(0, 0);
    if (!homeSections.length) fetchHome();
  }, []);

  const allItems = useMemo(
    () => homeSections.flatMap((s) => s.items || []),
    [homeSections],
  );

  const top10 = useMemo(
    () =>
      [...allItems]
        .sort((a, b) => (b.score || 0) - (a.score || 0))
        .slice(0, 10),
    [allItems],
  );

  if (loading && !homeSections.length) {
    return (
      <div className="min-h-screen bg-netflix-black pt-16 px-8 lg:px-16">
        <div className="skeleton h-[70vh] w-full rounded-lg mb-8" />
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="mb-8">
            <div className="skeleton h-5 w-40 mb-3" />
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5, 6].map((j) => (
                <div
                  key={j}
                  className="skeleton w-[160px] aspect-[2/3] rounded-md flex-shrink-0"
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-screen bg-netflix-black"
    >
      <HeroBanner movies={allItems} />

      <div className="relative z-10 -mt-24 space-y-4 py-8">
        {homeSections.map((section, i) => (
          <MovieRow key={i} title={section.title} movies={section.items} />
        ))}

        {top10.length > 0 && <MovieRow title="Top 10" movies={top10} />}
      </div>

      <Footer />
    </motion.div>
  );
}
