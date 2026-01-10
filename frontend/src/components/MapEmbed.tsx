import { MapPin, Navigation } from "lucide-react";

interface MapEmbedProps {
  origin: { lat: number; lng: number };
  destination: { lat: number; lng: number };
  waypoints: Array<{ lat: number; lng: number }>;
}

export const MapEmbed = ({ origin, destination, waypoints }: MapEmbedProps) => {
  const waypointsStr = waypoints.map((wp) => `${wp.lat},${wp.lng}`).join("|");
  
  const mapUrl = `https://www.google.com/maps/embed/v1/directions?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&origin=${origin.lat},${origin.lng}&destination=${destination.lat},${destination.lng}&waypoints=${waypointsStr}&mode=driving`;

  const directionsUrl = `https://www.google.com/maps/dir/?api=1&origin=${origin.lat},${origin.lng}&destination=${destination.lat},${destination.lng}&waypoints=${waypointsStr}&travelmode=driving`;

  return (
    <div className="space-y-3">
      <div className="rounded-2xl overflow-hidden shadow-xl border-2 border-border">
        <iframe
          src={mapUrl}
          className="w-full h-80 md:h-[500px]"
          style={{ border: 0 }}
          allowFullScreen
          loading="lazy"
          referrerPolicy="no-referrer-when-downgrade"
          title="Trip Route Map"
        />
      </div>

      <a
        href={directionsUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center justify-center gap-2 w-full py-3 bg-primary text-primary-foreground rounded-xl font-medium hover:opacity-90 transition-opacity"
      >
        <MapPin className="h-4 w-4" />
        Open in Google Maps
      </a>
    </div>
  );
};
