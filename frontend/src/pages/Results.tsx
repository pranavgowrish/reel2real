import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Logo } from "@/components/Logo";
import { ItineraryCard } from "@/components/ItineraryCard";
import { MediaSidebar } from "@/components/MediaSidebar";
import { MapEmbed } from "@/components/MapEmbed";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Share2, Download } from "lucide-react";

interface ItineraryItem {
  id: string;
  name: string;
  time: string;
  duration: string;
  address: string;
  openingHours: string;
  tags: string[];
  websiteUrl: string | null;
  isMeal?: "lunch" | "dinner";
  lat?: number;
  lon?: number;
}

interface ImageData {
  url: string;
  caption: string;
}

interface VideoData {
  youtubeId: string;
  title: string;
}

interface Coordinates {
  lat: number;
  lng: number;
  address?: string;
}

interface CoordinatesData {
  origin: Coordinates;
  destination: Coordinates;
  waypoints: Coordinates[];
}

interface TripData {
  location: string;
  vibes: string[];
  days: number;
  budget: number;
}

interface ItineraryData {
  itinerary: ItineraryItem[];
  images: ImageData[];
  videos: VideoData[];
  coordinates: CoordinatesData;
}

const Results = () => {
  const navigate = useNavigate();
  const [tripData, setTripData] = useState<TripData | null>(null);
  const [itineraryData, setItineraryData] = useState<ItineraryData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    try {
      // Get trip data (location, vibes, days, budget)
      const storedTripData = localStorage.getItem("tripData");
      if (storedTripData) {
        setTripData(JSON.parse(storedTripData));
      }

      // Get itinerary data (itinerary items, images, videos, coordinates)
      const storedItineraryData = localStorage.getItem("itineraryData");
      if (storedItineraryData) {
        setItineraryData(JSON.parse(storedItineraryData));
      } else {
        // If no itinerary data, redirect back to home
        console.error("No itinerary data found");
        navigate("/");
      }
    } catch (error) {
      console.error("Error loading data from localStorage:", error);
      navigate("/");
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  // -- build coords with addresses for MapEmbed
  const itineraryItems = itineraryData?.itinerary || [];

  // Simple list of addresses
  const itemAddresses = itineraryItems.map((i) => i.address); // array of strings

  // Helper: find address by coords (tolerance for floats)
  const findAddressByCoords = (lat: number, lng: number) => {
    const tol = 1e-5;
    const match = itineraryItems.find(
      (it) =>
        typeof it.lat === "number" &&
        typeof it.lon === "number" &&
        Math.abs(it.lat - lat) < tol &&
        Math.abs(it.lon - lng) < tol
    );
    return match?.address ?? "";
  };

  // Build coords with addresses for MapEmbed
  const originWithAddress = itineraryData?.coordinates.origin
    ? {
        ...itineraryData.coordinates.origin,
        address:
          itineraryData.coordinates.origin.address ??
          findAddressByCoords(
            itineraryData.coordinates.origin.lat,
            itineraryData.coordinates.origin.lng
          ),
      }
    : undefined;

  const destinationWithAddress = itineraryData?.coordinates.destination
    ? {
        ...itineraryData.coordinates.destination,
        address:
          itineraryData.coordinates.destination.address ??
          findAddressByCoords(
            itineraryData.coordinates.destination.lat,
            itineraryData.coordinates.destination.lng
          ),
      }
    : undefined;

  const waypointsWithAddress = (itineraryData?.coordinates.waypoints || []).map(
    (wp) => ({
      ...wp,
      address: wp.address ?? findAddressByCoords(wp.lat, wp.lng),
    })
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading your itinerary...</p>
        </div>
      </div>
    );
  }

  if (!itineraryData) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground">No itinerary found</p>
          <Button onClick={() => navigate("/")} className="mt-4">
            Plan a New Trip
          </Button>
        </div>
      </div>
    );
  }

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

      {/* Page Header */}
      <div className="container mx-auto px-4 py-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
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
            {tripData?.budget && ` • $${tripData.budget} budget`}
          </p>
        </motion.div>
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
              <MediaSidebar
                images={itineraryData.images || []}
                videos={itineraryData.videos || []}
              />
            </div>
          </motion.aside>

          {/* Center - Itinerary */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="lg:col-span-5 order-1 lg:order-2"
          >
            <div className="space-y-3">
              {itineraryData.itinerary && itineraryData.itinerary.length > 0 ? (
                itineraryData.itinerary.map((item, index) => (
                  <ItineraryCard
                    key={item.id}
                    item={item}
                    index={index}
                    isLast={index === itineraryData.itinerary.length - 1}
                  />
                ))
              ) : (
                <div className="text-center py-12">
                  <p className="text-muted-foreground">No itinerary items found</p>
                </div>
              )}
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
              {itineraryData.coordinates && originWithAddress && destinationWithAddress ? (
                <MapEmbed
                  origin={originWithAddress}
                  destination={destinationWithAddress}
                  waypoints={waypointsWithAddress}
                />
              ) : (
                <div className="bg-card rounded-lg border border-border p-8 text-center">
                  <p className="text-muted-foreground">Map data unavailable</p>
                </div>
              )}
            </div>
          </motion.aside>
        </div>
      </main>
    </div>
  );
};

export default Results;