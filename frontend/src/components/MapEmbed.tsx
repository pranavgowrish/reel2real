import { MapPin } from "lucide-react";
import { useEffect, useState } from "react";

interface MapEmbedProps {
  origin: { lat: number; lng: number; address?: string };
  destination: { lat: number; lng: number; address?: string };
  waypoints: Array<{ lat: number; lng: number; address?: string }>;
}

export const MapEmbed = ({ origin, destination, waypoints }: MapEmbedProps) => {
  const [displayOrigin, setDisplayOrigin] = useState(origin);
  const [displayDestination, setDisplayDestination] = useState(destination);
  const [displayWaypoints, setDisplayWaypoints] = useState(waypoints);

  useEffect(() => {
    const hotelData = localStorage.getItem('hotel');
    if (hotelData) {
      try {
        const hotel = JSON.parse(hotelData);
        if (hotel.name) {
          // Add hotel name to origin address
          setDisplayOrigin({
            ...origin,
            address: origin.address 
              ? `${hotel.name}, ${origin.address}` 
              : hotel.name
          });
          
          // Move current destination to waypoints and make hotel the new destination
          setDisplayWaypoints([
            ...waypoints,
            destination // Add original destination as last waypoint
          ]);

          // Hotel becomes the final destination
          setDisplayDestination({
            lat: origin.lat, // Use hotel coordinates if available
            lng: origin.lng,
            address: hotel.name
          });
        }
      } catch (error) {
        console.error('Error parsing hotel data:', error);
      }
    }
  }, [origin, destination, waypoints]);

  const originStr = displayOrigin.address 
    ? encodeURIComponent(displayOrigin.address)
    : `${displayOrigin.lat},${displayOrigin.lng}`;
  
  const destinationStr = displayDestination.address
    ? encodeURIComponent(displayDestination.address)
    : `${displayDestination.lat},${displayDestination.lng}`;
  
  const waypointsStr = displayWaypoints
    .map((wp) => wp.address ? encodeURIComponent(wp.address) : `${wp.lat},${wp.lng}`)
    .join("|");
  
  const mapUrl = `https://www.google.com/maps/embed/v1/directions?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&origin=${originStr}&destination=${destinationStr}&waypoints=${waypointsStr}&mode=driving`;

  const directionsUrl = `https://www.google.com/maps/dir/?api=1&origin=${originStr}&destination=${destinationStr}&waypoints=${waypointsStr}&travelmode=driving`;

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