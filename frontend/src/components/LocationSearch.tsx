import { useState, useEffect, useRef } from "react";
import { Input } from "@/components/ui/input";
import { MapPin, Search, Link2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LocationSearchProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  placeholder?: string;
}

const popularCities = [
  "San Diego, California, USA",
  "New York City, New York, USA",
  "Los Angeles, California, USA",
  "Miami, Florida, USA",
  "Las Vegas, Nevada, USA",
  "Chicago, Illinois, USA",
  "San Francisco, California, USA",
  "Seattle, Washington, USA",
  "Austin, Texas, USA",
  "Denver, Colorado, USA",
  "Paris, France",
  "Tokyo, Japan",
  "London, United Kingdom",
  "Barcelona, Spain",
  "Rome, Italy",
  "Bali, Indonesia",
  "Dubai, UAE",
  "Sydney, Australia",
];

export const LocationSearch = ({ value, onChange, onSubmit, placeholder }: LocationSearchProps) => {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isYoutubeMode, setIsYoutubeMode] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (value.length > 1 && !isYoutubeMode) {
      const filtered = popularCities.filter((city) =>
        city.toLowerCase().includes(value.toLowerCase())
      );
      setSuggestions(filtered.slice(0, 5));
      setShowSuggestions(filtered.length > 0);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  }, [value, isYoutubeMode]);

  const handleSelect = (city: string) => {
    onChange(city);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && value.trim()) {
      setShowSuggestions(false);
      onSubmit();
    }
  };

  return (
    <div className="relative w-full">
      <div className="flex gap-2 mb-3">
        <button
          onClick={() => setIsYoutubeMode(false)}
          className={cn(
            "flex items-center gap-2 px-3 py-1.5 rounded-full text-sm transition-all",
            !isYoutubeMode
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-muted-foreground hover:bg-muted/80"
          )}
        >
          <MapPin className="h-4 w-4" />
          Location
        </button>
        <button
          onClick={() => setIsYoutubeMode(true)}
          className={cn(
            "flex items-center gap-2 px-3 py-1.5 rounded-full text-sm transition-all",
            isYoutubeMode
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-muted-foreground hover:bg-muted/80"
          )}
        >
          <Link2 className="h-4 w-4" />
          YouTube Short
        </button>
      </div>

      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
        <Input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => value.length > 1 && setSuggestions.length > 0 && setShowSuggestions(true)}
          placeholder={isYoutubeMode ? "Paste YouTube Short URL..." : placeholder || "Enter city, state, country..."}
          className="pl-12 pr-4 py-6 text-lg rounded-2xl bg-card border-2 border-border focus:border-primary transition-all"
        />
      </div>

      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-card rounded-xl border-2 border-border shadow-xl overflow-hidden">
          {suggestions.map((city, index) => (
            <button
              key={city}
              onClick={() => handleSelect(city)}
              className={cn(
                "w-full px-4 py-3 text-left flex items-center gap-3 hover:bg-accent transition-colors",
                index !== suggestions.length - 1 && "border-b border-border"
              )}
            >
              <MapPin className="h-4 w-4 text-primary" />
              <span>{city}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
