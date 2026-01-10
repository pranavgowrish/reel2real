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

// Function to search locations using OpenStreetMap Nominatim
const searchLocations = async (query: string): Promise<string[]> => {
  if (query.length < 3) return [];
  
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=20&addressdetails=1&featuretype=city`,
      {
        headers: {
          'User-Agent': 'LocationSearchApp/1.0'
        }
      }
    );
    
    if (!response.ok) {
      throw new Error('Search failed');
    }
    
    const data = await response.json();
    
    // Filter to only show cities and towns
    const filtered = data.filter((item: any) => {
      const type = item.type;
      const placeClass = item.class;
      
      // Only include cities, towns, and administrative areas
      return (
        type === 'city' ||
        type === 'town' ||
        type === 'village' ||
        type === 'administrative' ||
        (placeClass === 'place' && ['city', 'town', 'village'].includes(type)) ||
        (placeClass === 'boundary' && type === 'administrative')
      );
    });
    
    // Format results to show City, State, Country
    const formatted = filtered.slice(0, 5).map((item: any) => {
      const address = item.address || {};
      const parts = [];
      
      // Add city/town name
      const cityName = address.city || address.town || address.village || item.name;
      if (cityName) parts.push(cityName);
      
      // Add state/region
      const state = address.state || address.region || address.province || address.county;
      if (state && state !== cityName) parts.push(state);
      
      // Add country
      if (address.country) parts.push(address.country);
      
      return parts.length > 0 ? parts.join(', ') : item.display_name;
    });
    
    return formatted;
  } catch (error) {
    console.error('Location search error:', error);
    return [];
  }
};

export const LocationSearch = ({ value, onChange, onSubmit, placeholder }: LocationSearchProps) => {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [justSelected, setJustSelected] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Don't search if user just selected a location
    if (justSelected) {
      return;
    }

    if (value.length > 2) {
      setIsLoading(true);
      
      // Debounce the search to avoid too many requests
      const timer = setTimeout(async () => {
        const results = await searchLocations(value);
        setSuggestions(results);
        setShowSuggestions(results.length > 0);
        setIsLoading(false);
      }, 400);
      
      return () => {
        clearTimeout(timer);
        setIsLoading(false);
      };
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

  const handleInputChange = (newValue: string) => {
    // Reset the justSelected flag when user starts typing again
    if (justSelected && newValue !== value) {
      setJustSelected(false);
    }
    onChange(newValue);
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
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-sm bg-primary text-primary-foreground">
          <MapPin className="h-4 w-4" />
          Location
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
        {isLoading && (
          <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground animate-spin" />
        )}
        <Input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => value.length > 2 && suggestions.length > 0 && !justSelected && setShowSuggestions(true)}
          placeholder={placeholder || "Search any location worldwide..."}
          className="pl-12 pr-12 py-6 text-lg rounded-2xl bg-card border-2 border-border focus:border-primary transition-all"
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