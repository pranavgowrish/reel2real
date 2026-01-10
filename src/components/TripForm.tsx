import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { LocationSearch } from "./LocationSearch";
import { VibeChip } from "./VibeChip";
import { BudgetSlider } from "./BudgetSlider";
import { Button } from "@/components/ui/button";
import {
  Compass,
  Palmtree,
  Heart,
  Sparkles,
  Users,
  Camera,
  Music,
  Utensils,
  ArrowRight,
  Minus,
  Plus,
} from "lucide-react";

const vibes = [
  { id: "adventurous", label: "Adventurous", icon: Compass },
  { id: "chill", label: "Chill & Relaxed", icon: Palmtree },
  { id: "romantic", label: "Romantic", icon: Heart },
  { id: "cultural", label: "Cultural", icon: Sparkles },
  { id: "family", label: "Family Fun", icon: Users },
  { id: "instagram", label: "Instagram-worthy", icon: Camera },
  { id: "nightlife", label: "Nightlife", icon: Music },
  { id: "foodie", label: "Foodie", icon: Utensils },
];

export const TripForm = () => {
  const navigate = useNavigate();
  const [location, setLocation] = useState("");
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedVibes, setSelectedVibes] = useState<string[]>([]);
  const [days, setDays] = useState(3);
  const [budget, setBudget] = useState([50]);

  const handleSearchSubmit = () => {
    if (location.trim()) {
      setIsExpanded(true);
    }
  };

  const toggleVibe = (vibeId: string) => {
    setSelectedVibes((prev) =>
      prev.includes(vibeId)
        ? prev.filter((v) => v !== vibeId)
        : [...prev, vibeId]
    );
  };

  const handlePlanTrip = () => {
    const tripData = {
      location,
      vibes: selectedVibes,
      days,
      budget: budget[0],
    };
    // Store in sessionStorage for the loading page
    sessionStorage.setItem("tripData", JSON.stringify(tripData));
    navigate("/loading");
  };

  return (
    <motion.div
      layout
      className="w-full max-w-2xl mx-auto"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <motion.div
        layout
        className={`bg-card/80 backdrop-blur-xl rounded-3xl border-2 border-border shadow-2xl p-6 md:p-8 transition-all duration-500 ${
          isExpanded ? "max-w-3xl" : ""
        }`}
      >
        <LocationSearch
          value={location}
          onChange={setLocation}
          onSubmit={handleSearchSubmit}
          placeholder="Where do you want to explore?"
        />

        <AnimatePresence>
          {!isExpanded && location.trim() && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="mt-4"
            >
              <Button
                onClick={handleSearchSubmit}
                size="lg"
                className="w-full rounded-xl text-lg py-6 bg-gradient-to-r from-primary to-accent hover:opacity-90 transition-opacity"
              >
                Let's Go <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </motion.div>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.4 }}
              className="space-y-8 mt-8"
            >
              {/* Vibes Section */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-foreground">
                  What's your vibe?
                </h3>
                <div className="flex flex-wrap gap-2">
                  {vibes.map((vibe) => (
                    <VibeChip
                      key={vibe.id}
                      label={vibe.label}
                      icon={vibe.icon}
                      selected={selectedVibes.includes(vibe.id)}
                      onClick={() => toggleVibe(vibe.id)}
                    />
                  ))}
                </div>
              </div>

              {/* Days Section */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-foreground">
                  How many days?
                </h3>
                <div className="flex items-center justify-center gap-6">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setDays(Math.max(1, days - 1))}
                    className="h-12 w-12 rounded-full"
                  >
                    <Minus className="h-5 w-5" />
                  </Button>
                  <div className="text-center">
                    <span className="text-5xl font-bold text-primary">{days}</span>
                    <p className="text-muted-foreground">
                      {days === 1 ? "day" : "days"}
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setDays(Math.min(14, days + 1))}
                    className="h-12 w-12 rounded-full"
                  >
                    <Plus className="h-5 w-5" />
                  </Button>
                </div>
              </div>

              {/* Budget Section */}
              <div className="space-y-4">
                <BudgetSlider value={budget} onChange={setBudget} />
              </div>

              {/* Submit Button */}
              <Button
                onClick={handlePlanTrip}
                size="lg"
                disabled={selectedVibes.length === 0}
                className="w-full rounded-xl text-lg py-6 bg-gradient-to-r from-primary to-accent hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                Create My Adventure <Sparkles className="ml-2 h-5 w-5" />
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </motion.div>
  );
};
