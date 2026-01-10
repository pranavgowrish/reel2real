import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

interface PuzzleLoaderProps {
  cityImage: string;
  venues: Array<{ name: string; image: string }>;
  phase: "searching" | "shortlisting" | "complete";
}

export const PuzzleLoader = ({ cityImage, venues, phase }: PuzzleLoaderProps) => {
  const [filledPieces, setFilledPieces] = useState<number[]>([]);
  const [activeVenue, setActiveVenue] = useState<number | null>(null);
  const totalPieces = 9; // 3x3 grid

  useEffect(() => {
    if (phase === "searching" || phase === "shortlisting") {
      const interval = setInterval(() => {
        setFilledPieces((prev) => {
          if (prev.length >= totalPieces) return prev;
          const remaining = Array.from({ length: totalPieces }, (_, i) => i).filter(
            (i) => !prev.includes(i)
          );
          if (remaining.length === 0) return prev;
          const randomIndex = remaining[Math.floor(Math.random() * remaining.length)];
          return [...prev, randomIndex];
        });
      }, 400);
      return () => clearInterval(interval);
    }
  }, [phase]);

  useEffect(() => {
    if (phase === "shortlisting" && venues.length > 0) {
      let index = 0;
      const interval = setInterval(() => {
        setActiveVenue(index);
        index = (index + 1) % venues.length;
      }, 1500);
      return () => clearInterval(interval);
    }
  }, [phase, venues]);

  const getPiecePosition = (index: number) => {
    const row = Math.floor(index / 3);
    const col = index % 3;
    return { row, col };
  };

  const bubblePositions = [
    { top: "-10%", left: "50%", transform: "translateX(-50%)" }, // top center
    { top: "8%", left: "-18%", transform: "translateX(0)" }, // top left
    { top: "8%", right: "-18%", transform: "translateX(0)" }, // top right
    { top: "50%", left: "-18%", transform: "translateY(-50%)" }, // middle left
    { top: "50%", right: "-18%", transform: "translateY(-50%)" }, // middle right
    { bottom: "-10%", left: "50%", transform: "translateX(-50%)" }, // bottom center
    { bottom: "10%", left: "-15%" }, // bottom left
    { bottom: "10%", right: "-15%" }, // bottom right
  ];

  return (
    <div className="relative flex flex-col items-center justify-center">
      {/* Puzzle Container */}
      <div className="relative w-72 h-72 md:w-96 md:h-96">
        <div className="grid grid-cols-3 gap-1 w-full h-full rounded-2xl overflow-hidden shadow-2xl">
          {Array.from({ length: totalPieces }).map((_, index) => {
            const { row, col } = getPiecePosition(index);
            const isFilled = filledPieces.includes(index);

            return (
              <motion.div
                key={index}
                className="relative overflow-hidden"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{
                  opacity: isFilled ? 1 : 0.2,
                  scale: isFilled ? 1 : 0.95,
                }}
                transition={{ duration: 0.5, ease: "easeOut" }}
              >
                <div
                  className="w-full h-full bg-cover bg-no-repeat"
                  style={{
                    backgroundImage: `url(${cityImage})`,
                    backgroundPosition: `${col * 50}% ${row * 50}%`,
                    backgroundSize: "300%",
                    filter: isFilled ? "none" : "grayscale(100%)",
                  }}
                />
                {!isFilled && (
                  <div className="absolute inset-0 bg-muted/60 backdrop-blur-sm" />
                )}
              </motion.div>
            );
          })}
        </div>

        {/* Thought Bubbles - Only show active bubble */}
        <AnimatePresence mode="wait">
          {phase === "shortlisting" && activeVenue !== null && (
            <motion.div
              key={`bubble-${activeVenue}`}
              className="absolute w-28 md:w-36 p-2 bg-card rounded-xl shadow-xl border-2 border-primary/20"
              style={{
                ...bubblePositions[activeVenue % bubblePositions.length],
              }}
              initial={{ opacity: 0, scale: 0.3, y: -20 }}
              animate={{
                opacity: 1,
                scale: 1,
                y: [0, -8, 0],
              }}
              exit={{ opacity: 0, scale: 0.3, y: 20 }}
              transition={{
                initial: { duration: 0.5, ease: "easeOut" },
                animate: {
                  y: {
                    duration: 3,
                    repeat: Infinity,
                    ease: "easeInOut",
                  },
                  opacity: { duration: 0.5 },
                  scale: { duration: 0.5 },
                },
                exit: { duration: 0.4, ease: "easeIn" },
              }}
            >
              <img
                src={venues[activeVenue].image}
                alt={venues[activeVenue].name}
                className="w-full h-16 md:h-20 object-cover rounded-lg mb-1"
              />
              <p className="text-xs font-medium text-center truncate text-foreground">
                {venues[activeVenue].name}
              </p>
              {/* Bubble tail */}
              <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-card rotate-45 border-r-2 border-b-2 border-primary/20" />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Status Text */}
      <motion.div
        className="mt-8 text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        {phase === "searching" && (
          <div className="space-y-2">
            <motion.div
              className="text-xl font-semibold text-foreground"
              animate={{ opacity: [1, 0.5, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              Searching 1,000+ websites...
            </motion.div>
            <p className="text-muted-foreground">
              Finding the best spots for your adventure
            </p>
          </div>
        )}
        {phase === "shortlisting" && (
          <div className="space-y-2">
            <motion.div
              className="text-xl font-semibold text-primary"
              animate={{ opacity: [1, 0.7, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
            >
              Curating your perfect itinerary...
            </motion.div>
            <p className="text-muted-foreground">
              Optimizing routes for the best experience
            </p>
          </div>
        )}
      </motion.div>
    </div>
  );
};
