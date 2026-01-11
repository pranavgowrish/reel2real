import { motion } from "framer-motion";
import { Clock, ExternalLink, Utensils, Coffee, Star, DollarSign, TrendingUp, Calendar, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ItineraryCardProps {
  item: {
    id: string;
    name: string;
    time: string;
    duration: string;
    address: string;
    openingHours?: string;
    tags?: string[];
    isMeal?: "lunch" | "dinner";
    websiteUrl?: string;
    image?: string;
  };
  index: number;
  isLast: boolean;
}

const tagIcons: Record<string, React.ReactNode> = {
  "Most Popular": <Star className="h-3 w-3" />,
  "Budget Friendly": <DollarSign className="h-3 w-3" />,
  "Trending": <TrendingUp className="h-3 w-3" />,
  "Hidden Gem": <Star className="h-3 w-3" />,
};

const tagColors: Record<string, string> = {
  "Most Popular": "bg-amber-500/10 text-amber-600 border-amber-500/30",
  "Budget Friendly": "bg-emerald-500/10 text-emerald-600 border-emerald-500/30",
  "Trending": "bg-rose-500/10 text-rose-600 border-rose-500/30",
  "Hidden Gem": "bg-violet-500/10 text-violet-600 border-violet-500/30",
};

export const ItineraryCard = ({ item, index, isLast }: ItineraryCardProps) => {
const getPlaceImage = () => {
  if (item.image) return item.image;
  
  try {
    const placesString = localStorage.getItem("places");
    if (placesString) {
      let placesData = JSON.parse(placesString);
      
      if (typeof placesData === 'string') {
        placesData = JSON.parse(placesData);
      }
      
      const confirmedPlaces = placesData.confirmed_places || [];
      
      const place = confirmedPlaces.find((p: any) => 
        p.name && item.name && p.name.toLowerCase().trim() === item.name.toLowerCase().trim()
      );
      
      console.log(`Looking for "${item.name}", found:`, place);
      return place?.image || null;
    }
  } catch (error) {
    console.error("Error fetching place image from localStorage:", error);
  }
  return null;
};

  const placeImage = getPlaceImage();

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
      className="relative"
    >
      {!isLast && (
        <div className="absolute left-6 top-16 bottom-0 w-0.5 bg-gradient-to-b from-primary/50 to-primary/10" />
      )}

      <div className="flex gap-3">
        <div className="flex flex-col items-center flex-shrink-0">
          <div
            className={cn(
              "w-12 h-12 rounded-full flex items-center justify-center text-sm font-bold shadow-md",
              item.isMeal
                ? "bg-gradient-to-br from-accent to-primary text-accent-foreground"
                : "bg-gradient-to-br from-primary to-primary/80 text-primary-foreground"
            )}
          >
            {item.isMeal === "lunch" ? (
              <Coffee className="h-5 w-5" />
            ) : item.isMeal === "dinner" ? (
              <Utensils className="h-5 w-5" />
            ) : (
              <span>{index + 1}</span>
            )}
          </div>
          <span className="text-xs text-muted-foreground mt-2 font-medium">
            {item.time}
          </span>
        </div>

        <div className="flex-1 flex gap-3">
          <div className="flex-1 bg-card/50 rounded-xl border border-border/50 p-3 hover:bg-card hover:shadow-md transition-all duration-200">
            <div className="space-y-3">
              <div>
                <h4 className="font-semibold text-foreground text-sm">
                  {item.name}
                </h4>
              </div>
              <div className="flex items-center gap-3 text-xs text-muted-foreground flex-wrap">
                {item.duration && (
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    <span>{item.duration}</span>
                  </div>
                )}
                {item.openingHours && (
                  <div className="flex items-center gap-1">
                    <MapPin className="h-3 w-3" />
                    <span>{item.openingHours}</span>
                  </div>
                )}
                {item.isMeal && (
                  <Badge variant="secondary" className="text-xs px-2 py-0.5">
                    {item.isMeal === "lunch" ? "🍽️ Lunch" : "🌙 Dinner"}
                  </Badge>
                )}
              </div>
              {item.address && (
                <p className="text-xs text-muted-foreground/80 leading-snug">
                  {item.address}
                </p>
              )}
              {item.tags && item.tags.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {item.tags.map((tag) => (
                    <span
                      key={tag}
                      className={cn(
                        "inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-xs font-medium border",
                        tagColors[tag] || "bg-muted text-muted-foreground border-border"
                      )}
                    >
                      {tagIcons[tag]}
                      {tag}
                    </span>
                  ))}
                </div>
              )}
              <Button
                size="sm"
                className="w-full h-8 text-xs"
                onClick={() => window.open(item.websiteUrl, "_blank")}
              >
                <Calendar className="h-3 w-3 mr-1.5" />
                Reserve
              </Button>
            </div>
          </div>
          {placeImage && (
            <div className="flex-shrink-0 w-28 h-28 rounded-lg overflow-hidden border border-border/50 shadow-md">
              <img
                src={placeImage}
                alt={item.name}
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = "none";
                }}
              />
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};
