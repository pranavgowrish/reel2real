import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { LocationSearch } from "./LocationSearch";
import { VibeChip } from "./VibeChip";
import { BudgetSlider } from "./BudgetSlider";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from "@/components/ui/popover";
import { DateRange } from "react-day-picker";
import { format } from "date-fns";
import {
  Compass,
  Palmtree,
  Sparkles,
  Music,
  Utensils,
  ArrowRight,
  Minus,
  Plus,
  Calendar as CalendarIcon,
  Users,
} from "lucide-react";

/* -------------------- Helpers -------------------- */
function getNextWeekend(): DateRange {
  const today = new Date();
  const day = today.getDay(); // 0 = Sun, 6 = Sat

  // Always choose the *next* Saturday
  const daysUntilSaturday = (6 - day + 7) % 7 || 7;

  const saturday = new Date(today);
  saturday.setDate(today.getDate() + daysUntilSaturday);

  const sunday = new Date(saturday);
  sunday.setDate(saturday.getDate() + 1);

  return { from: saturday, to: sunday };
}

/* -------------------- Data -------------------- */
const vibes = [
  { id: "adventurous", label: "Adventurous", icon: Compass },
  { id: "chill", label: "Chill & Relaxed", icon: Palmtree },
  { id: "cultural", label: "Cultural", icon: Sparkles },
  { id: "nightlife", label: "Nightlife", icon: Music },
  { id: "foodie", label: "Foodie", icon: Utensils },
];

/* -------------------- Component -------------------- */
export const TripForm = () => {
  const navigate = useNavigate();

  const [location, setLocation] = useState("");
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedVibes, setSelectedVibes] = useState<string[]>([]);
  const [budget, setBudget] = useState([50]);

  // ✅ Correct naming
  const [people, setPeople] = useState(2);

  // ✅ Default = next weekend
  const [dateRange, setDateRange] = useState<DateRange>(() => getNextWeekend());

  const handleSearchSubmit = () => {
    if (location.trim()) setIsExpanded(true);
  };

  const toggleVibe = (vibeId: string) => {
    setSelectedVibes((prev) =>
      prev.includes(vibeId)
        ? prev.filter((v) => v !== vibeId)
        : [...prev, vibeId]
    );
  };

  const handlePlanTrip = async () => {
    const tripData = {
      location,
      vibes: selectedVibes,
      people,
      checkin: dateRange?.from,
      checkout: dateRange?.to,
      budget: budget[0],
    };

    localStorage.clear();
    localStorage.setItem("tripData", JSON.stringify(tripData));
    navigate("/loading");

    try {
      const response = await fetch("http://127.0.0.1:8000/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          city: location,
          vibe: selectedVibes[0],
          budget: budget[0],
          people,
          startDate: dateRange?.from,
          endDate: dateRange?.to,
        }),
      });

      const data = await response.json();
      localStorage.setItem("places", JSON.stringify(data.result));
    } catch (error) {
      console.error("Error fetching itinerary:", error);
      navigate("/error");
    }
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
        className={`bg-card/80 backdrop-blur-xl rounded-3xl border-2 border-border shadow-2xl p-6 md:p-10 transition-all duration-500 ${
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
            <motion.div className="mt-4">
              <Button
                onClick={handleSearchSubmit}
                size="lg"
                className="w-full rounded-xl text-lg py-6 bg-gradient-to-r from-primary to-accent"
              >
                Let’s Go <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </motion.div>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {isExpanded && (
            <motion.div className="space-y-8 mt-8">
              {/* Vibes */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">What’s your vibe?</h3>
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

              {/* Dates + People */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Dates */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">When are you going?</h3>

                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className="w-full justify-start text-left font-normal rounded-xl"
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {dateRange?.from && dateRange?.to ? (
                          <>
                            {format(dateRange.from, "MMM d, yyyy")} –{" "}
                            {format(dateRange.to, "MMM d, yyyy")}
                          </>
                        ) : (
                          <span className="text-muted-foreground">
                            Pick your travel dates
                          </span>
                        )}
                      </Button>
                    </PopoverTrigger>

                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="range"
                        selected={dateRange}
                        onSelect={setDateRange}
                        defaultMonth={dateRange?.from}
                        disabled={(date) => date < new Date()}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>

                {/* People */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold flex items-center gap-2">
                    <Users className="h-5 w-5" />
                    How many people?
                  </h3>

                  <div className="flex items-center justify-center gap-6">
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => setPeople(Math.max(1, people - 1))}
                      className="h-12 w-12 rounded-full"
                    >
                      <Minus className="h-5 w-5" />
                    </Button>

                    <div className="text-center">
                      <span className="text-5xl font-bold text-primary">
                        {people}
                      </span>
                      <p className="text-muted-foreground">
                        {people === 1 ? "person" : "people"}
                      </p>
                    </div>

                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => setPeople(Math.min(12, people + 1))}
                      className="h-12 w-12 rounded-full"
                    >
                      <Plus className="h-5 w-5" />
                    </Button>
                  </div>
                </div>
              </div>

              {/* Budget */}
              <BudgetSlider value={budget} onChange={setBudget} />

              {/* Submit */}
              <Button
                onClick={handlePlanTrip}
                size="lg"
                disabled={
                  selectedVibes.length === 0 ||
                  !dateRange?.from ||
                  !dateRange?.to
                }
                className="w-full rounded-xl text-lg py-6 bg-gradient-to-r from-primary to-accent disabled:opacity-50"
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
