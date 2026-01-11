import { useState, useEffect, useRef } from "react";
import { Input } from "@/components/ui/input";
import { MapPin, Search, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LocationSearchProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  placeholder?: string;
}

const searchLocations = async (query: string): Promise<string[]> => {
  if (query.length < 3) return [];

  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
        query
      )}&limit=20&addressdetails=1&featuretype=city`,
      {
        headers: {
          "User-Agent": "LocationSearchApp/1.0",
        },
      }
    );

    if (!response.ok) {
      throw new Error("Search failed");
    }

    const data = await response.json();

    const filtered = data.filter((item: any) => {
      const type = item.type;
      const placeClass = item.class;

      return (
        type === "city" ||
        type === "town" ||
        type === "village" ||
        type === "administrative" ||
        (placeClass === "place" &&
          ["city", "town", "village"].includes(type)) ||
        (placeClass === "boundary" && type === "administrative")
      );
    });

    return filtered.slice(0, 5).map((item: any) => {
      const address = item.address || {};
      const parts = [];

      const city =
        address.city || address.town || address.village || item.name;
      if (city) parts.push(city);

      const state =
        address.state || address.region || address.province || address.county;
      if (state && state !== city) parts.push(state);

      if (address.country) parts.push(address.country);

      return parts.join(", ");
    });
  } catch (error) {
    console.error("Location search error:", error);
    return [];
  }
};

export const LocationSearch = ({
  value,
  onChange,
  onSubmit,
  placeholder,
}: LocationSearchProps) => {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [justSelected, setJustSelected] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (justSelected) return;

    if (value.length > 2) {
      setIsLoading(true);

      const timer = setTimeout(async () => {
        const results = await searchLocations(value);
        setSuggestions(results);
        setShowSuggestions(results.length > 0);
        setIsLoading(false);
      }, 400);

      return () => clearTimeout(timer);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
      setIsLoading(false);
    }
  }, [value, justSelected]);

  const handleSelect = (city: string) => {
    setJustSelected(true);
    onChange(city);
    setShowSuggestions(false);
    setSuggestions([]);
    inputRef.current?.blur();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && value.trim()) {
      setShowSuggestions(false);
      onSubmit();
    }
  };

  return (
    <div className="relative w-full">
      {/* Location pill */}
      <div className="flex justify-center mb-4">
        <div className="flex items-center gap-2 font-semibold px-4 py-2 rounded-full text-base bg-primary text-primary-foreground">
          <MapPin className="h-5 w-5" />
          Location
        </div>
      </div>

      {/* Input */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-6 w-6 text-muted-foreground" />

        {isLoading && (
          <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 h-6 w-6 text-muted-foreground animate-spin" />
        )}

        <Input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => {
            if (justSelected) setJustSelected(false);
            onChange(e.target.value);
          }}
          onKeyDown={handleKeyDown}
          onFocus={() =>
            value.length > 2 &&
            suggestions.length > 0 &&
            !justSelected &&
            setShowSuggestions(true)
          }
          placeholder={placeholder || "Search any location worldwide..."}
          className="
            pl-14 pr-14
            py-7
            text-xl
            rounded-2xl
            bg-card
            border-2 border-border
            focus:border-primary
            transition-all
          "
        />
      </div>

      {/* Suggestions */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-50 w-full mt-3 bg-card rounded-2xl border-2 border-border shadow-xl overflow-hidden">
          {suggestions.map((city, index) => (
            <button
              key={city}
              onClick={() => handleSelect(city)}
              className={cn(
                "w-full px-5 py-4 text-left flex items-center gap-3 text-lg hover:bg-accent transition-colors",
                index !== suggestions.length - 1 &&
                  "border-b border-border"
              )}
            >
              <MapPin className="h-5 w-5 text-primary" />
              <span>{city}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
