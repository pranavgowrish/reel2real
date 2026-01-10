import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { PuzzleLoader } from "@/components/PuzzleLoader";
import { Logo } from "@/components/Logo";

// Mock city images based on location
const cityImages: Record<string, string> = {
  "san diego": "https://images.unsplash.com/photo-1538097304804-2a1b932466a9?w=800&q=80",
  "new york": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=800&q=80",
  "los angeles": "https://images.unsplash.com/photo-1580655653885-65763b2597d0?w=800&q=80",
  "miami": "https://images.unsplash.com/photo-1533106497176-45ae19e68ba2?w=800&q=80",
  "paris": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800&q=80",
  "tokyo": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=800&q=80",
  "london": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800&q=80",
  "default": "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=800&q=80",
};

// FIX API: Replace mockVenues with real data from Flask API response
// The API should return venue data to show in the shortlisting phase animation
const mockVenues = [
  { name: "Sunset Cliffs", image: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=200&q=80" },
  { name: "La Jolla Cove", image: "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=200&q=80" },
  { name: "Gaslamp Quarter", image: "https://images.unsplash.com/photo-1514565131-fce0801e5785?w=200&q=80" },
  { name: "Balboa Park", image: "https://images.unsplash.com/photo-1558642452-9d2a7deb7f62?w=200&q=80" },
  { name: "USS Midway", image: "https://images.unsplash.com/photo-1569289804428-a123b89a1a5c?w=200&q=80" },
  { name: "Torrey Pines", image: "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=200&q=80" },
];

const Loading = () => {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<"searching" | "shortlisting" | "complete">("searching");
  const [tripData, setTripData] = useState<any>(null);

  useEffect(() => {
    // Get trip data from session storage
    const data = sessionStorage.getItem("tripData");
    if (data) {
      setTripData(JSON.parse(data));
    } else {
      // No data, redirect to home
      navigate("/");
      return;
    }

    // Simulate loading phases
    // Phase 1: Searching (3 seconds)
    const timer1 = setTimeout(() => {
      setPhase("shortlisting");
    }, 3000);

    // Phase 2: Shortlisting (4 seconds)
    const timer2 = setTimeout(() => {
      setPhase("complete");
    }, 7000);

    // Navigate to results
    const timer3 = setTimeout(() => {
      navigate("/results");
    }, 8000);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, [navigate]);

  const getCityImage = () => {
    if (!tripData?.location) return cityImages.default;
    const location = tripData.location.toLowerCase();
    for (const [city, image] of Object.entries(cityImages)) {
      if (location.includes(city)) return image;
    }
    return cityImages.default;
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      {/* Logo */}
      <div className="mb-8">
        <Logo className="scale-125" />
      </div>

      {/* Location */}
      {tripData && (
        <h2 className="text-2xl font-semibold text-foreground mb-8 text-center">
          Planning your trip to{" "}
          <span className="text-primary">{tripData.location}</span>
        </h2>
      )}

      {/* Puzzle Loader */}
      <PuzzleLoader
        cityImage={getCityImage()}
        venues={mockVenues}
        phase={phase}
      />
    </div>
  );
};

export default Loading;
