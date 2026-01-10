import { motion } from "framer-motion";
import { Clock, ExternalLink, Utensils, Coffee, Star, DollarSign, TrendingUp } from "lucide-react";
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
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
      className="relative"
    >
      {/* Timeline connector */}
      {!isLast && (
        <div className="absolute left-6 top-16 bottom-0 w-0.5 bg-gradient-to-b from-primary/50 to-primary/10" />
      )}

      <div className="flex gap-4">
        {/* Time indicator */}
        <div className="flex flex-col items-center">
          <div
            className={cn(
              "w-12 h-12 rounded-full flex items-center justify-center text-sm font-bold shadow-lg",
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
          <span className="text-xs text-muted-foreground mt-1 font-medium">
            {item.time}
          </span>
        </div>

        {/* Card content */}
        <div className="flex-1 bg-card rounded-2xl border border-border shadow-md hover:shadow-lg transition-shadow p-4 mb-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h4 className="font-semibold text-foreground truncate">
                  {item.name}
                </h4>
                {item.isMeal && (
                  <Badge variant="secondary" className="text-xs shrink-0">
                    {item.isMeal === "lunch" ? "🍽️ Lunch Break" : "🌙 Dinner Break"}
                  </Badge>
                )}
              </div>
              <p className="text-sm text-muted-foreground mb-2">{item.address}</p>

              {/* Tags */}
              {item.tags && item.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {item.tags.map((tag) => (
                    <span
                      key={tag}
                      className={cn(
                        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border",
                        tagColors[tag] || "bg-muted text-muted-foreground border-border"
                      )}
                    >
                      {tagIcons[tag]}
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              {/* Opening hours */}
              {item.openingHours && (
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  <span>{item.openingHours}</span>
                </div>
              )}
            </div>

            {/* Website button */}
            {item.websiteUrl && (
              <Button
                size="sm"
                variant="outline"
                className="shrink-0"
                onClick={() => window.open(item.websiteUrl, "_blank")}
              >
                <ExternalLink className="h-4 w-4 mr-1" />
                Visit
              </Button>
            )}
          </div>

          {/* Duration indicator */}
          <div className="mt-3 pt-3 border-t border-border/50 flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            <span>Suggested duration: {item.duration}</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
