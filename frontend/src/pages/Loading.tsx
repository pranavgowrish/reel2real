import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { PuzzleLoader } from "@/components/PuzzleLoader";
import heroImage from "@/assets/hero-travel.jpg";

const searchLogos = [
  { name: "Instagram", logo: "https://upload.wikimedia.org/wikipedia/commons/a/a5/Instagram_icon.png" },
  { name: "YouTube", logo: "https://upload.wikimedia.org/wikipedia/commons/0/09/YouTube_full-color_icon_%282017%29.svg" },
  { name: "Booking.com", logo: "https://upload.wikimedia.org/wikipedia/commons/b/be/Booking.com_logo.svg" },
  { name: "Airbnb", logo: "https://upload.wikimedia.org/wikipedia/commons/6/69/Airbnb_Logo_B%C3%A9lo.svg" },
  { name: "Expedia", logo: "https://upload.wikimedia.org/wikipedia/commons/5/5b/Expedia_2012_logo.svg" },
  { name: "Google", logo: "https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg" },
  { name: "Yelp", logo: "https://upload.wikimedia.org/wikipedia/commons/a/ad/Yelp_Logo.svg" },
  { name: "DuckDuckGo", logo: "https://upload.wikimedia.org/wikipedia/en/8/88/DuckDuckGo_logo.svg" },
];

const SearchingAnimation = () => {
  const [visibleLogos, setVisibleLogos] = useState<number[]>([]);
  const [dots, setDots] = useState("");

  useEffect(() => {
    // Animate dots
    const dotsInterval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? "" : prev + ".");
    }, 500);

    const interval = setInterval(() => {
      // Randomly show 1-2 logos at a time
      const count = Math.floor(Math.random() * 2) + 1;
      const indices = Array.from({ length: count }, () => 
        Math.floor(Math.random() * searchLogos.length)
      );
      setVisibleLogos(indices);
    }, 1200);

    return () => {
      clearInterval(interval);
      clearInterval(dotsInterval);
    };
  }, []);

  return (
    <div className="relative w-full max-w-6xl h-[600px] mb-8">
      {/* Background gradient glow */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-120 h-120 bg-primary/40 rounded-full blur-10xl animate-pulse" />
      </div>

      {/* Animated logos - original logic */}
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
            {/* Enhanced logo styling */}
            <div className="relative bg-white/90 backdrop-blur-sm p-4 rounded-2xl shadow-lg border border-primary/20 hover:shadow-xl hover:border-primary/40 transition-all">
              <img 
                src={logo.logo} 
                alt={logo.name} 
                className="w-20 h-20 object-contain" 
              />
            </div>
          </div>
        );
      })}

      {/* Enhanced searching text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-6 pointer-events-none">
        {/* Main text with gradient */}
        <motion.div
          animate={{ opacity: [0.6, 1, 0.6] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          className="text-center"
        >
          <h3 className="text-4xl font-bold bg-gradient-to-r from-primary via-accent-foreground to-primary bg-clip-text text-transparent mb-2">
            Crawling and Researching{dots}
          </h3>
          <p className="text-sm text-muted-foreground">
            Analyzing thousands of sources to find your perfect activities
          </p>
        </motion.div>

        {/* Progress bar */}
        <div className="w-64 h-2 bg-muted rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-primary to-accent-foreground"
            animate={{ x: ["-100%", "100%"] }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          />
        </div>

        {/* Stats counter */}
        <motion.div 
          className="flex gap-8 text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <div>
            <div className="text-2xl font-bold text-primary">8+</div>
            <div className="text-xs text-muted-foreground">Sources</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-primary">1000s</div>
            <div className="text-xs text-muted-foreground">Activities</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-primary">AI</div>
            <div className="text-xs text-muted-foreground">Powered</div>
          </div>
        </motion.div>
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
    const data = localStorage.getItem("tripData");
    
    if (!data) {
      navigate("/");
      return;
    }

    const parsedTripData = JSON.parse(data);
    setTripData(parsedTripData);

    const checkInterval = setInterval(() => {
      const placesData = localStorage.getItem("places");
      
      if (placesData) {
        clearInterval(checkInterval);
        
        try {
          const parsed = JSON.parse(placesData);
          
          let placesResult = parsed.result || parsed;
          
          if (typeof placesResult === 'string') {
            placesResult = placesResult.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
            placesResult = JSON.parse(placesResult);
          }
          
          const confirmedPlaces = placesResult.confirmed_places || [];
          
          const venueList = confirmedPlaces.map((place: any) => ({
            name: place.name,
            image: place.image,
            desc: place.desc
          }));
          
          setVenues(venueList);
          
          if (venueList.length > 0) {
            const randomIndex = Math.floor(Math.random() * venueList.length);
            setCityImage(venueList[randomIndex].image);
          }
          
          setDataLoaded(true);
          
          setTimeout(() => setPhase("shortlisting"), 1000);
          setTimeout(() => setPhase("confirming"), 5000);
          
        } catch (error) {
          console.error("Error parsing places data:", error);
        }
      }
    }, 500);

    return () => {
      clearInterval(checkInterval);
    };
  }, [navigate]);

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Background Image with Overlay */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: `url(${heroImage})` }}
      >
        <div className="absolute inset-0 bg-gradient-to-b from-background/90 via-background/70 to-background/95" />
      </div>

      {/* Content */}
      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center p-4">
        {/* Logo with animation */}
        <motion.div 
          className="mb-8 flex justify-center items-center"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <img src="logo2.png" alt="Logo" className="w-1/3 max-w-xs" />
        </motion.div>

        {/* Location with gradient */}
        {tripData && (
          <motion.h2 
            className="text-2xl font-semibold text-foreground mb-12 text-center"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            Planning your trip to{" "}
            <span className="bg-gradient-to-r from-primary via-accent-foreground to-primary bg-clip-text text-transparent font-bold">
              {tripData.location}
            </span>
          </motion.h2>
        )}

        {/* Show searching animation until data is loaded */}
        {!dataLoaded ? (
          <SearchingAnimation />
        ) : (
          <PuzzleLoader cityImage={cityImage} venues={venues} phase={phase} />
        )}
      </div>
    </div>
  );
};

export default Loading;