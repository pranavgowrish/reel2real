import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { PuzzleLoader } from "@/components/PuzzleLoader";

// Popular website logos for searching animation
const searchLogos = [
  {
    name: "Instagram",
    logo: "https://upload.wikimedia.org/wikipedia/commons/a/a5/Instagram_icon.png",
  },
  {
    name: "YouTube",
    logo: "https://upload.wikimedia.org/wikipedia/commons/0/09/YouTube_full-color_icon_%282017%29.svg",
  },
  {
    name: "Booking.com",
    logo: "https://upload.wikimedia.org/wikipedia/commons/b/be/Booking.com_logo.svg",
  },
  {
    name: "Airbnb",
    logo: "https://upload.wikimedia.org/wikipedia/commons/6/69/Airbnb_Logo_B%C3%A9lo.svg",
  },
  {
    name: "Expedia",
    logo: "https://upload.wikimedia.org/wikipedia/commons/5/5b/Expedia_2012_logo.svg",
  },
  {
    name: "Google",
    logo: "https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg",
  },
  {
    name: "Yelp",
    logo: "https://upload.wikimedia.org/wikipedia/commons/a/ad/Yelp_Logo.svg",
  },
  {
    name: "DuckDuckGo",
    logo: "https://upload.wikimedia.org/wikipedia/en/8/88/DuckDuckGo_logo.svg",
  },
  {
    name: "OpenStreetMap",
    logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Openstreetmap_logo.svg/1024px-Openstreetmap_logo.svg.png",
  },
];

const SearchingAnimation = () => {
  const [visibleLogos, setVisibleLogos] = useState<number[]>([]);

  useEffect(() => {
    const interval = setInterval(() => {
      // Randomly show 1-2 logos at a time
      const count = Math.floor(Math.random() * 2) + 1;
      const indices = Array.from({ length: count }, () => 
        Math.floor(Math.random() * searchLogos.length)
      );
      setVisibleLogos(indices);
    }, 1200);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative w-full max-w-6xl h-[600px] mb-8">
      {/* Empty puzzle placeholder */}
      <div className="absolute inset-0 grid grid-cols-3 gap-3 opacity-20">
        {Array.from({ length: 9 }).map((_, i) => (
          <div key={i} className="bg-muted rounded-lg border-2 border-dashed border-muted-foreground/30" />
        ))}
      </div>

      {/* Animated logos */}
      {searchLogos.map((logo, index) => {
        const isVisible = visibleLogos.includes(index);
        const row = Math.floor(index / 3);
        const col = index % 3;
        const top = row * 33.33 + Math.random() * 20 - 10;
        const left = col * 33.33 + Math.random() * 20 - 10;

return (
          <div
            key={index}
            className={`absolute transition-all duration-700 ${
              isVisible ? 'opacity-100 scale-100' : 'opacity-0 scale-50'
            }`}
            style={{
              top: `${top}%`,
              left: `${left}%`,
            }}
          >
            <img src={logo.logo} alt={logo.name} className="w-24 h-24 object-contain" />
          </div>
        );
      })}

      {/* Searching text */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-3xl font-semibold text-muted-foreground animate-pulse">
          Searching the web...
        </div>
      </div>
    </div>
  );
};

const Loading = () => {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<"searching" | "shortlisting" | "confirming" | "complete">("searching");
  const [tripData, setTripData] = useState<any>(null);
  const [venues, setVenues] = useState<any[]>([]);
  const [cityImage, setCityImage] = useState<string>("");
  const [dataLoaded, setDataLoaded] = useState(false);

  useEffect(() => {
    // Get trip data from localStorage
    const data = localStorage.getItem("tripData");
    
    if (!data) {
      // No data, redirect to home
      navigate("/");
      return;
    }

    const parsedTripData = JSON.parse(data);
    setTripData(parsedTripData);

    // Poll for places data to appear in localStorage
    const checkInterval = setInterval(() => {
      const placesData = localStorage.getItem("places");
      
      if (placesData) {
        clearInterval(checkInterval);
        
        try {
          const parsed = JSON.parse(placesData);
          
          // Extract JSON from the result string (it's wrapped in ```json```)
          let placesResult = parsed.result || parsed;
          
          // Remove markdown code fences if present
          if (typeof placesResult === 'string') {
            placesResult = placesResult.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
            placesResult = JSON.parse(placesResult);
          }
          
          // Get confirmed places
          const confirmedPlaces = placesResult.confirmed_places || [];
          
          // Transform to venue format for PuzzleLoader
          const venueList = confirmedPlaces.map((place: any) => ({
            name: place.name,
            image: place.image,
            desc: place.desc
          }));
          
          setVenues(venueList);
          
          // Pick a random image from the venues for the main puzzle
          if (venueList.length > 0) {
            const randomIndex = Math.floor(Math.random() * venueList.length);
            setCityImage(venueList[randomIndex].image);
          }
          
          setDataLoaded(true);
          
          // Start the phase transitions once data is loaded
          setTimeout(() => setPhase("shortlisting"), 1000);
          setTimeout(() => setPhase("confirming"), 5000);
          // Don't auto-navigate - let PuzzleLoader handle it after user confirms
          
        } catch (error) {
          console.error("Error parsing places data:", error);
        }
      }
    }, 500); // Check every 500ms

    // Cleanup interval on unmount
    return () => {
      clearInterval(checkInterval);
    };
  }, [navigate]);

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      {/* Logo */}
      <div className="mb-8 justify-center items-center flex ">
        <img src="public/logo2.png" alt="Logo" className="size-4/12  items-center justify-between" />
      </div>

      {/* Location */}
      {tripData && (
        <h2 className="text-2xl font-semibold text-foreground mb-8 text-center">
          Planning your trip to{" "}
          <span className="text-primary">{tripData.location}</span>
        </h2>
      )}

      {/* Show searching animation until data is loaded */}
      {!dataLoaded ? (
        <SearchingAnimation />
      ) : (
        <PuzzleLoader cityImage={cityImage} venues={venues} phase={phase} />
      )}
    </div>
  );
};

export default Loading;