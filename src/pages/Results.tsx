import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Logo } from "@/components/Logo";
import { ItineraryCard } from "@/components/ItineraryCard";
import { MediaSidebar } from "@/components/MediaSidebar";
import { MapEmbed } from "@/components/MapEmbed";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Share2, Download, Film, Navigation } from "lucide-react";

// Mock itinerary data
const mockItinerary = [
  {
    id: "1",
    name: "Sunrise at Sunset Cliffs",
    time: "8:00 AM",
    duration: "1 hour",
    address: "Sunset Cliffs Natural Park, San Diego",
    openingHours: "Open 24 hours",
    tags: ["Most Popular", "Hidden Gem"],
    websiteUrl: "https://www.sandiego.gov/park-and-recreation/parks/regional/shoreline/sunset",
  },
  {
    id: "2",
    name: "La Jolla Cove Kayaking",
    time: "9:30 AM",
    duration: "2 hours",
    address: "1100 Coast Blvd, La Jolla, CA 92037",
    openingHours: "Tours: 8AM - 4PM",
    tags: ["Trending"],
    websiteUrl: "https://www.lajollakayak.com",
  },
  {
    id: "3",
    name: "Brunch at The Cottage La Jolla",
    time: "12:00 PM",
    duration: "1.5 hours",
    address: "7702 Fay Ave, La Jolla, CA 92037",
    openingHours: "7:30AM - 3PM",
    tags: ["Budget Friendly"],
    isMeal: "lunch" as const,
    websiteUrl: "https://www.cottagelajolla.com",
  },
  {
    id: "4",
    name: "Balboa Park Museums",
    time: "2:00 PM",
    duration: "2.5 hours",
    address: "1549 El Prado, San Diego, CA 92101",
    openingHours: "10AM - 5PM",
    tags: ["Most Popular"],
    websiteUrl: "https://www.balboapark.org",
  },
  {
    id: "5",
    name: "USS Midway Museum",
    time: "5:00 PM",
    duration: "2 hours",
    address: "910 N Harbor Dr, San Diego, CA 92101",
    openingHours: "10AM - 5PM",
    tags: ["Trending", "Most Popular"],
    websiteUrl: "https://www.midway.org",
  },
  {
    id: "6",
    name: "Dinner at Gaslamp Quarter",
    time: "7:30 PM",
    duration: "2 hours",
    address: "Fifth Avenue, San Diego, CA 92101",
    openingHours: "Varies by restaurant",
    isMeal: "dinner" as const,
    websiteUrl: "https://www.gaslamp.org",
  },
  {
    id: "7",
    name: "Rooftop Bar at The Nolen",
    time: "9:30 PM",
    duration: "2 hours",
    address: "453 Sixth Ave, San Diego, CA 92101",
    openingHours: "4PM - 2AM",
    tags: ["Hidden Gem"],
    websiteUrl: "https://www.thenolenrooftop.com",
  },
];

// Mock media
const mockImages = [
  { url: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400&q=80", caption: "Sunset Cliffs" },
  { url: "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&q=80", caption: "La Jolla Cove" },
  { url: "https://images.unsplash.com/photo-1558642452-9d2a7deb7f62?w=400&q=80", caption: "Balboa Park" },
  { url: "https://images.unsplash.com/photo-1569289804428-a123b89a1a5c?w=400&q=80", caption: "USS Midway" },
];

const mockVideos = [
  { youtubeId: "dQw4w9WgXcQ", title: "San Diego Travel Guide" },
  { youtubeId: "9bZkp7q19f0", title: "Top Things To Do" },
];

// Mock coordinates for San Diego locations
const mockCoordinates = {
  origin: { lat: 32.8458529, lng: -117.2575702 },
  destination: { lat: 32.7316772, lng: -117.1465253 },
  waypoints: [
    { lat: 32.7978268, lng: -117.2403183 },
    { lat: 32.7792158, lng: -117.2342029 },
    { lat: 32.7984884, lng: -117.2564953 },
    { lat: 32.7448067, lng: -117.2476067 },
    { lat: 32.8919572, lng: -117.2402554 },
  ],
};

const Results = () => {
  const navigate = useNavigate();
  const [tripData, setTripData] = useState<any>(null);

  useEffect(() => {
    const data = sessionStorage.getItem("tripData");
    if (data) {
      setTripData(JSON.parse(data));
    }
  }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-xl border-b border-border">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Button
            variant="ghost"
            onClick={() => navigate("/")}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            New Trip
          </Button>
          
          <Logo />
          
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon">
              <Share2 className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon">
              <Download className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Reel to Real Header */}
      <div className="container mx-auto px-4 py-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-6"
        >
          <h1 className="text-3xl md:text-4xl font-bold">
            Your{" "}
            <span className="text-primary">
              {tripData?.location || "Dream Trip"}
            </span>{" "}
            Itinerary
          </h1>
          <p className="text-muted-foreground mt-2">
            {tripData?.days || 1} day adventure •{" "}
            {tripData?.vibes?.join(", ") || "Custom"} vibe
          </p>
        </motion.div>

        {/* Column Headers */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-4">
          <div className="lg:col-span-3">
            <div className="flex items-center gap-2 text-lg font-bold">
              <Film className="h-5 w-5 text-primary" />
              <span className="text-primary">Reel</span>
            </div>
          </div>
          <div className="hidden lg:block lg:col-span-5" />
          <div className="lg:col-span-4">
            <div className="flex items-center gap-2 text-lg font-bold">
              <Navigation className="h-5 w-5 text-accent-foreground" />
              <span className="text-foreground">Real</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="container mx-auto px-4 pb-12">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Sidebar - Media */}
          <motion.aside
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="lg:col-span-3 order-2 lg:order-1"
          >
            <div className="sticky top-24">
              <MediaSidebar images={mockImages} videos={mockVideos} />
            </div>
          </motion.aside>

          {/* Center - Itinerary */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="lg:col-span-5 order-1 lg:order-2"
          >
            <div className="bg-card rounded-2xl border border-border p-6 shadow-lg">
              <h2 className="text-xl font-bold mb-6 text-foreground">
                Day 1 Itinerary
              </h2>
              <div className="space-y-2">
                {mockItinerary.map((item, index) => (
                  <ItineraryCard
                    key={item.id}
                    item={item}
                    index={index}
                    isLast={index === mockItinerary.length - 1}
                  />
                ))}
              </div>
            </div>
          </motion.div>

          {/* Right Sidebar - Map */}
          <motion.aside
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
            className="lg:col-span-4 order-3"
          >
            <div className="sticky top-24">
              <MapEmbed
                origin={mockCoordinates.origin}
                destination={mockCoordinates.destination}
                waypoints={mockCoordinates.waypoints}
              />
            </div>
          </motion.aside>
        </div>
      </main>
    </div>
  );
};

export default Results;
