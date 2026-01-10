import { Film, MapPin } from "lucide-react";

export const Logo = ({ className = "" }: { className?: string }) => {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="relative">
        <Film className="h-8 w-8 text-primary" />
        <MapPin className="h-4 w-4 text-accent-foreground absolute -bottom-1 -right-1" />
      </div>
      <div className="flex flex-col leading-none">
        <span className="text-2xl font-bold tracking-tight">
          <span className="text-primary">Reel</span>
          <span className="text-accent-foreground">2</span>
          <span className="text-foreground">Real</span>
        </span>
      </div>
    </div>
  );
};
