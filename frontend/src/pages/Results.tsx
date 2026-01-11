import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
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
  checkin: string;
  checkout: string;
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
  const [hotelData, setHotelData] = useState<any>(null);

  const handleHotel = async () => {
    try {
      const itineraryDataStr = localStorage.getItem("itineraryData");
      const itineraryDataObj = itineraryDataStr ? JSON.parse(itineraryDataStr) : null;
      const response = await fetch(
        "http://127.0.0.1:8000/hotel",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            checkin: tripData?.checkin,
            checkout: tripData?.checkout,
            adults: tripData?.days,
            address: itineraryDataObj?.last_location?.address || "",
          }),
        }
      );

      const data = await response.json();
      console.log("DATA:", data);
      const itineraryData = JSON.parse(localStorage.getItem('itineraryData'));

// Get the last location address
const lastLocationAddress = itineraryData.last_location.address;
console.log(lastLocationAddress); 
      // Store the API response
      localStorage.setItem("hotel", JSON.stringify(data));
      setHotelData(data);
      console.log("Hotel data set:", hotelData);
    } catch (error) {
      console.error("Error fetching hotel:", error);
      navigate("/error");
    }
  };

  useEffect(() => {
    try {
      const storedTripData = localStorage.getItem("tripData");
      if (storedTripData) {
        setTripData(JSON.parse(storedTripData));
      }

      const storedItineraryData = localStorage.getItem("itineraryData");
      if (storedItineraryData) {
        setItineraryData(JSON.parse(storedItineraryData));
      } else {
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

  const itineraryItems = itineraryData?.itinerary || [];

  const itemAddresses = itineraryItems.map((i) => i.address);

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

          <div className="flex items-center gap-2">
            <Button 
              className="bg-primary hover:bg-primary/90"
              onClick={handleHotel}
            >
              Let Us find the best Hotel for your trip!
            </Button>
            <Button variant="outline" size="icon">
              <Share2 className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon">
              <Download className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

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

      <main className="container mx-auto px-4 pb-12">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
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

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="lg:col-span-5 order-1 lg:order-2"
          >
            <div className="space-y-3">
              {itineraryData.itinerary && itineraryData.itinerary.length > 0 ? (
                <>
                  {hotelData && (
                    <>
                    <ItineraryCard
                      item={{
                        id: "0",
                        name: hotelData.name || "Hotel Check-in",
                        time: "8:00 AM",
                        duration: "Check-in",
                        address: hotelData.address || "",
                        openingHours: "24 hours",
                        tags: ["Hotel"],
                        websiteUrl: hotelData.link || null,
                        isMeal: undefined,
                      }}
                      index={0}
                      isLast={false}
                    />
                    </>
                  )}

                  {itineraryData.itinerary.map((item, index) => (
                    <ItineraryCard
                      key={item.id}
                      item={item}
                      index={hotelData ? index + 1 : index}
                      isLast={
                        !hotelData &&
                        index === itineraryData.itinerary.length - 1
                      }
                    />
                  ))}

                  {hotelData && (
                    <ItineraryCard
                      item={{
                        id: String(itineraryData.itinerary.length + 1),
                        name: hotelData.name || "Hotel",
                        time: "EOD",
                        duration: "Check-out",
                        address: hotelData.address || "",
                        openingHours: "24 hours",
                        tags: ["Hotel"],
                        websiteUrl: hotelData.link || null,
                        isMeal: undefined,
                      }}
                      index={itineraryData.itinerary.length + 1}
                      isLast={true}
                    />
                  )}
                </>
              ) : (
                <div className="text-center py-12">
                  <p className="text-muted-foreground">
                    No itinerary items found
                  </p>
                </div>
              )}
            </div>
          </motion.div>

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