import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface VibeChipProps {
  label: string;
  icon: LucideIcon;
  selected: boolean;
  onClick: () => void;
}

export const VibeChip = ({ label, icon: Icon, selected, onClick }: VibeChipProps) => {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-2 px-4 py-2 rounded-full border-2 transition-all duration-300",
        "hover:scale-105 hover:shadow-md",
        selected
          ? "bg-primary text-primary-foreground border-primary shadow-lg"
          : "bg-card text-card-foreground border-border hover:border-primary/50"
      )}
    >
      <Icon className="h-4 w-4" />
      <span className="font-medium">{label}</span>
    </button>
  );
};
