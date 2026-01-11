import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Trash2, Pencil } from "lucide-react";

interface Venue {
  name: string;
  image: string;
  id?: string;
}

interface PuzzleLoaderProps {
  cityImage: string;
  venues: Venue[];
  phase: "searching" | "shortlisting" | "confirming" | "finalizing" | "complete";
  onConfirm?: (selectedVenues: Venue[]) => Promise<void>;
}

export const PuzzleLoader = ({ cityImage, venues, phase, onConfirm }: PuzzleLoaderProps) => {
  const [filledPieces, setFilledPieces] = useState<number[]>([]);
  const [activeVenue, setActiveVenue] = useState<number | null>(null);
  const [editableVenues, setEditableVenues] = useState<Venue[]>([]);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editValue, setEditValue] = useState("");
  const [isConfirming, setIsConfirming] = useState(false);
  const totalPieces = 9;

  useEffect(() => {
    if (phase === "confirming") {
      setEditableVenues(venues);
    }
  }, [phase, venues]);

  useEffect(() => {
    if (phase === "searching" || phase === "shortlisting" || phase === "finalizing") {
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
    { top: "-10%", left: "50%", transform: "translateX(-50%)" },
    { top: "8%", left: "-18%", transform: "translateX(0)" },
    { top: "8%", right: "-18%", transform: "translateX(0)" },
    { top: "50%", left: "-18%", transform: "translateY(-50%)" },
    { top: "50%", right: "-18%", transform: "translateY(-50%)" },
    { bottom: "-10%", left: "50%", transform: "translateX(-50%)" },
    { bottom: "10%", left: "-15%" },
    { bottom: "10%", right: "-15%" },
  ];

  const handleRemoveVenue = (index: number) => {
    setEditableVenues(prev => prev.filter((_, i) => i !== index));
  };

  const handleEditVenue = (index: number) => {
    setEditingIndex(index);
    setEditValue(editableVenues[index].name);
  };

  const handleSaveEdit = (index: number) => {
    if (editValue.trim()) {
      setEditableVenues(prev =>
        prev.map((venue, i) => (i === index ? { ...venue, name: editValue.trim() } : venue))
      );
    }
    setEditingIndex(null);
    setEditValue("");
  };

  const handleConfirm = async () => {
    setIsConfirming(true);
    try {
      const response = await fetch(
        "https://knight-s-code.onrender.com/api/generate-itinerary",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ selectedVenues: editableVenues }),
        },
      );

      const data = await response.json();
      console.log("DATA:", data);

      // Store the API response
      localStorage.setItem("itineraryData", JSON.stringify(data));
      
      // Navigate to results page
      //navigate("/result");
    } catch (error) {
      console.error("Error fetching itinerary:", error);
      //API hereeee
      if (onConfirm) {
        await onConfirm(editableVenues);
      }
    }
  };

  return (
    <div className="relative flex flex-col items-center justify-center min-h-screen p-4">
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

        {/* Thought Bubbles */}
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
                default: { duration: 0.5, ease: "easeOut" },
                y: {
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut",
                },
                opacity: { duration: 0.5 },
                scale: { duration: 0.5 },
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
        {phase === "finalizing" && (
          <div className="space-y-2">
            <motion.div
              className="text-xl font-semibold text-primary"
              animate={{ opacity: [1, 0.7, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
            >
              Finalizing your adventure...
            </motion.div>
            <p className="text-muted-foreground">
              Creating the perfect day plan
            </p>
          </div>
        )}
      </motion.div>

      {/* Confirmation Modal */}
      <AnimatePresence>
        {phase === "confirming" && (
          <>
            {/* Backdrop */}
            <motion.div
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            />

            {/* Modal */}
            <motion.div
              className="fixed inset-0 flex items-center justify-center z-50 p-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <motion.div
                className="bg-card rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden border border-border"
                initial={{ scale: 0.9, y: 20 }}
                animate={{ scale: 1, y: 0 }}
                exit={{ scale: 0.9, y: 20 }}
                transition={{ type: "spring", damping: 25, stiffness: 300 }}
              >
                {/* Header */}
                <div className="p-6 border-b border-border">
                  <h2 className="text-2xl font-bold text-foreground">
                    Review Your Destinations
                  </h2>
                  <p className="text-sm text-muted-foreground mt-1">
                    Edit or remove any destinations before we finalize your itinerary
                  </p>
                </div>

                {/* Venue List */}
                <div className="p-6 overflow-y-auto max-h-96">
                  <div className="space-y-3">
                    {editableVenues.map((venue, index) => (
                      <motion.div
                        key={venue.id || index}
                        className="flex items-center gap-4 p-4 rounded-xl bg-muted/50 hover:bg-muted transition-colors"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <img
                          src={venue.image}
                          alt={venue.name}
                          className="w-20 h-20 object-cover rounded-lg flex-shrink-0"
                        />
                        
                        <div className="flex-1 min-w-0">
                          {editingIndex === index ? (
                            <input
                              type="text"
                              value={editValue}
                              onChange={(e) => setEditValue(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === "Enter") handleSaveEdit(index);
                                if (e.key === "Escape") {
                                  setEditingIndex(null);
                                  setEditValue("");
                                }
                              }}
                              className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-foreground"
                              autoFocus
                            />
                          ) : (
                            <h3 className="font-semibold text-foreground truncate">
                              {venue.name}
                            </h3>
                          )}
                        </div>

                        <div className="flex gap-2 flex-shrink-0">
                          {editingIndex === index ? (
                            <button
                              onClick={() => handleSaveEdit(index)}
                              className="p-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                              title="Save"
                            >
                              <X className="w-4 h-4 rotate-45" />
                            </button>
                          ) : (
                            <button
                              onClick={() => handleEditVenue(index)}
                              className="p-2 rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors"
                              title="Edit name"
                            >
                              <Pencil className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={() => handleRemoveVenue(index)}
                            className="p-2 rounded-lg bg-destructive/10 text-destructive hover:bg-destructive/20 transition-colors"
                            title="Remove"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </motion.div>
                    ))}
                  </div>

                  {editableVenues.length === 0 && (
                    <div className="text-center py-12 text-muted-foreground">
                      <p>No destinations selected</p>
                      <p className="text-sm mt-2">Add at least one destination to continue</p>
                    </div>
                  )}
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-border flex justify-between items-center">
                  <p className="text-sm text-muted-foreground">
                    {editableVenues.length} {editableVenues.length === 1 ? "destination" : "destinations"} selected
                  </p>
                  <button
                    onClick={handleConfirm}
                    disabled={editableVenues.length === 0 || isConfirming}
                    className="px-6 py-3 bg-primary text-primary-foreground rounded-lg font-semibold hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isConfirming ? "Confirming..." : "Confirm & Continue"}
                  </button>
                </div>
              </motion.div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};