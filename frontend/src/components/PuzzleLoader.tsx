import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Trash2, Pencil } from "lucide-react";

interface Venue {
  name: string;
  image: string;
  id?: string;
  desc?: string;
}

interface PuzzleLoaderProps {
  cityImage: string;
  venues: Venue[];
  phase: "searching" | "shortlisting" | "confirming" | "finalizing" | "complete";
  onConfirm?: (selectedVenues: Venue[]) => Promise<void>;
}

export const PuzzleLoader = ({ cityImage, venues, phase, onConfirm }: PuzzleLoaderProps) => {
  const [activeVenue, setActiveVenue] = useState<number | null>(null);
  const [editableVenues, setEditableVenues] = useState<Venue[]>([]);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editValue, setEditValue] = useState("");
  const [isConfirming, setIsConfirming] = useState(false);
  const [revealedPieces, setRevealedPieces] = useState<number[]>([]);
  const [closed, setClosed] = useState(false);

  const ROWS = 4;
  const COLS = 4;
  const TOTAL_PIECES = ROWS * COLS;

  // Reveal puzzle pieces one by one
  useEffect(() => {
    if (phase === "searching" || phase === "shortlisting") {
      setRevealedPieces([]);
      let currentPiece = 0;
      
      const interval = setInterval(() => {
        if (currentPiece < TOTAL_PIECES) {
          setRevealedPieces(prev => [...prev, currentPiece]);
          currentPiece++;
        } else {
          clearInterval(interval);
        }
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [phase]);

  useEffect(() => {
    if (phase === "confirming") {
      setEditableVenues(venues);
    }
  }, [phase, venues]);

  useEffect(() => {
    if ((phase === "shortlisting" || phase === "finalizing") && venues.length > 0) {
      let index = 0;
      const interval = setInterval(() => {
        setActiveVenue(index);
        index = (index + 1) % venues.length;
      }, 1500);
      return () => clearInterval(interval);
    }
  }, [phase, venues]);

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
    setClosed(true);
    setIsConfirming(true);    
    // Continue revealing remaining puzzle pieces
    const remainingPieces = Array.from({ length: TOTAL_PIECES }, (_, i) => i).filter(
      i => !revealedPieces.includes(i)
    );
    
    let pieceIndex = 0;
    const revealInterval = setInterval(() => {
      if (pieceIndex < remainingPieces.length) {
        setRevealedPieces(prev => [...prev, remainingPieces[pieceIndex]]);
        pieceIndex++;
      } else {
        clearInterval(revealInterval);
      }
    }, 5000);
    
    // Call onConfirm callback to update phase and close dialog
    if (onConfirm) {
      await onConfirm(editableVenues);
    }
    
    let data: any = null;
    try {

      const response = await fetch("http://127.0.0.1:8000/itin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          city: localStorage.getItem("tripData") ? JSON.parse(localStorage.getItem("tripData") || '{}').location : '', 
          places: editableVenues.map(v => v.name) 
        }),
      });

      data = await response.json();
      console.log("DATA:", data);

      // Get the places data from localStorage with proper error handling
      let placesData;
      try {
        const placesString = localStorage.getItem("places");
        placesData = placesString ? JSON.parse(placesString) : { confirmed_places: [] };
      } catch (e) {
        console.error("Error parsing places data:", e);
        placesData = { confirmed_places: [] };
      }

      // Create a mapping of place names to their tags
      const placeTagsMap = (placesData.confirmed_places || []).reduce((map, place) => {
        map[place.name] = place.tag ? [place.tag] : [];
        return map;
      }, {});

      // Get trip data
      let tripData;
      try {
        const tripString = localStorage.getItem("tripData");
        tripData = tripString ? JSON.parse(tripString) : {};
      } catch (e) {
        console.error("Error parsing trip data:", e);
        tripData = {};
      }

      // Update itinerary items with correct tags from places
      const itineraryWithCorrectTags = (data?.final?.itinerary || []).map(item => {
        // If this item's name matches a place, use that place's tag
        if (placeTagsMap[item.name]) {
          return {
            ...item,
            tags: placeTagsMap[item.name]
          };
        }
        // Otherwise keep existing tags (for restaurants, etc.)
        return item;
      });

      // Save to localStorage
      localStorage.setItem("itineraryData", JSON.stringify({
        itinerary: itineraryWithCorrectTags,
        images: data?.final?.images || [],
        videos: data?.final?.videos || [],
        coordinates: data?.final?.coordinates || {},
        tags: tripData.tags || [],
      }));

      // Redirect to results page after successful API response
      window.location.href = "/results";
      
    } catch (error) {
      console.error("Error fetching itinerary:", error);
      // Still redirect even on error, or handle error UI here
      window.location.href = "/results";
    } finally {
      setIsConfirming(false);
    }
  };

  // Generate puzzle pieces
  const renderPuzzlePieces = () => {
    const pieces = [];
    
    for (let i = 0; i < TOTAL_PIECES; i++) {
      const row = Math.floor(i / COLS);
      const col = i % COLS;
      const isRevealed = revealedPieces.includes(i);
      
      pieces.push(
        <motion.div
          key={i}
          className="absolute overflow-hidden"
          style={{
            width: `${100 / COLS}%`,
            height: `${100 / ROWS}%`,
            top: `${(row * 100) / ROWS}%`,
            left: `${(col * 100) / COLS}%`,
          }}
          initial={{ opacity: 0, scale: 0.8, rotateY: -90 }}
          animate={isRevealed ? {
            opacity: 1,
            scale: 1,
            rotateY: 0,
          } : {
            opacity: 0,
            scale: 0.8,
            rotateY: -90,
          }}
          transition={{
            duration: 0.6,
            ease: "easeOut",
          }}
        >
          <div
            className="w-full h-full"
            style={{
              backgroundImage: `url(${cityImage})`,
              backgroundSize: `${COLS * 100}% ${ROWS * 100}%`,
              backgroundPosition: `${(col * 100) / (COLS - 1)}% ${(row * 100) / (ROWS - 1)}%`,
            }}
          />
          {/* Piece border for visual effect */}
          {isRevealed && (
            <div className="absolute inset-0 border border-white/30 pointer-events-none" />
          )}
        </motion.div>
      );
    }
    
    return pieces;
  };

  return (
    <div className="relative flex flex-col items-center justify-center min-h-screen w-full p-4 md:p-8 bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Puzzle Container - Takes most of the screen */}
      <div className="relative w-full max-w-2xl aspect-square">
        <div className="relative w-full h-full rounded-2xl shadow-2xl overflow-hidden bg-gradient-to-br from-gray-800 to-gray-900">
          {renderPuzzlePieces()}
        </div>

        {/* Thought Bubbles */}
        <AnimatePresence mode="wait">
          {(phase === "shortlisting" || phase === "finalizing") && activeVenue !== null && (
            <motion.div
              key={`bubble-${activeVenue}`}
              className="absolute w-32 md:w-40 lg:w-48 p-3 bg-white rounded-xl shadow-xl border-2 border-blue-200 z-10"
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
                className="w-full h-20 md:h-24 lg:h-28 object-cover rounded-lg mb-2"
              />
              <p className="text-xs md:text-sm font-medium text-center truncate text-gray-800">
                {venues[activeVenue].name}
              </p>
              <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-white rotate-45 border-r-2 border-b-2 border-blue-200" />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Status Text */}
      <motion.div
        className="mt-8 text-center max-w-2xl"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        {phase === "searching" && (
          <div className="space-y-2">
            <motion.div
              className="text-2xl md:text-3xl font-semibold text-gray-800"
              animate={{ opacity: [1, 0.5, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              Searching 1,000+ websites...
            </motion.div>
            <p className="text-base md:text-lg text-gray-600">
              Finding the best spots for your adventure
            </p>
            <div className="mt-4">
              <div className="text-sm text-gray-500">
                Pieces revealed: {revealedPieces.length} / {TOTAL_PIECES}
              </div>
            </div>
          </div>
        )}
        {phase === "shortlisting" && (
          <div className="space-y-2">
            <motion.div
              className="text-2xl md:text-3xl font-semibold text-blue-600"
              animate={{ opacity: [1, 0.7, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
            >
              Curating your perfect itinerary...
            </motion.div>
            <p className="text-base md:text-lg text-gray-600">
              Optimizing routes for the best experience
            </p>
          </div>
        )}
        {phase === "finalizing" && (
          <div className="space-y-2">
            <motion.div
              className="text-2xl md:text-3xl font-semibold text-blue-600"
              animate={{ opacity: [1, 0.7, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
            >
              Finalizing your adventure...
            </motion.div>
            <p className="text-base md:text-lg text-gray-600">
              Creating the perfect day plan
            </p>
          </div>
        )}
      </motion.div>

      {/* Confirmation Modal */}
      <AnimatePresence>
        {phase === "confirming" && closed==false && (
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
                className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden border border-gray-200"
                initial={{ scale: 0.9, y: 20 }}
                animate={{ scale: 1, y: 0 }}
                exit={{ scale: 0.9, y: 20 }}
                transition={{ type: "spring", damping: 25, stiffness: 300 }}
              >
                {/* Header */}
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-2xl font-bold text-gray-800">
                    Review Your Destinations
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Edit or remove any destinations before we finalize your itinerary
                  </p>
                </div>

                {/* Venue List */}
                <div className="p-6 overflow-y-auto max-h-96">
                  <div className="space-y-3">
                    {editableVenues.map((venue, index) => (
                      <motion.div
                        key={venue.id || index}
                        className="flex items-center gap-4 p-4 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors"
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
                              className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-800"
                              autoFocus
                            />
                          ) : (
                            <>
                              <h3 className="font-semibold text-gray-800 truncate">
                                {venue.name}
                              </h3>
                              {venue.desc && (
                                <p className="text-xs text-gray-600 line-clamp-2 mt-1">
                                  {venue.desc}
                                </p>
                              )}
                            </>
                          )}
                        </div>

                        <div className="flex gap-2 flex-shrink-0">
                          {editingIndex === index ? (
                            <button
                              onClick={() => handleSaveEdit(index)}
                              className="p-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                              title="Save"
                            >
                              <X className="w-4 h-4 rotate-45" />
                            </button>
                          ) : (
                            <button
                              onClick={() => handleEditVenue(index)}
                              className="p-2 rounded-lg bg-gray-200 text-gray-700 hover:bg-gray-300 transition-colors"
                              title="Edit name"
                            >
                              <Pencil className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={() => handleRemoveVenue(index)}
                            className="p-2 rounded-lg bg-red-100 text-red-600 hover:bg-red-200 transition-colors"
                            title="Remove"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </motion.div>
                    ))}
                  </div>

                  {editableVenues.length === 0 && (
                    <div className="text-center py-12 text-gray-600">
                      <p>No destinations selected</p>
                      <p className="text-sm mt-2">Add at least one destination to continue</p>
                    </div>
                  )}
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-gray-200 flex justify-between items-center">
                  <p className="text-sm text-gray-600">
                    {editableVenues.length} {editableVenues.length === 1 ? "destination" : "destinations"} selected
                  </p>
                  <button
                    onClick={handleConfirm}
                    disabled={editableVenues.length === 0 || isConfirming}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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

// Demo component to show how it works
export default function App() {
  const [phase, setPhase] = useState<"searching" | "shortlisting" | "confirming" | "finalizing" | "complete">("searching");
  
  const sampleVenues = [
    {
      id: "1",
      name: "Eiffel Tower",
      image: "https://images.unsplash.com/photo-1511739001486-6bfe10ce785f?w=400",
      desc: "Iconic iron lattice tower in Paris"
    },
    {
      id: "2",
      name: "Louvre Museum",
      image: "https://images.unsplash.com/photo-1499856871958-5b9627545d1a?w=400",
      desc: "World's largest art museum"
    },
    {
      id: "3",
      name: "Arc de Triomphe",
      image: "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=400",
      desc: "Famous monument in Paris"
    },
    {
      id: "4",
      name: "Notre-Dame",
      image: "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=400",
      desc: "Historic Catholic cathedral"
    }
  ];

  useEffect(() => {
    const timer1 = setTimeout(() => setPhase("shortlisting"), 5000);
    const timer2 = setTimeout(() => setPhase("confirming"), 11000);
    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
    };
  }, []);

  const handleConfirm = async (selectedVenues: any[]) => {
    console.log("Confirmed venues:", selectedVenues);
    setPhase("finalizing");
    // The API call and redirect now happen in PuzzleLoader's handleConfirm
  };

  return (
    <PuzzleLoader
      cityImage="https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800"
      venues={sampleVenues}
      phase={phase}
      onConfirm={handleConfirm}
    />
  );
}