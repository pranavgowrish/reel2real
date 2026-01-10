import { Slider } from "@/components/ui/slider";
import { DollarSign } from "lucide-react";

interface BudgetSliderProps {
  value: number[];
  onChange: (value: number[]) => void;
}

const budgetLabels = ["Budget", "Moderate", "Comfortable", "Luxury", "No Limit"];

export const BudgetSlider = ({ value, onChange }: BudgetSliderProps) => {
  const budgetIndex = Math.floor(value[0] / 25);
  
  return (
    <div className="w-full space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-muted-foreground">Budget Level</label>
        <div className="flex items-center gap-1">
          {[...Array(budgetIndex + 1)].map((_, i) => (
            <DollarSign key={i} className="h-4 w-4 text-primary" />
          ))}
          <span className="ml-2 font-semibold text-foreground">{budgetLabels[budgetIndex]}</span>
        </div>
      </div>
      <Slider
        value={value}
        onValueChange={onChange}
        max={100}
        step={25}
        className="w-full"
      />
      <div className="flex justify-between text-xs text-muted-foreground">
        {budgetLabels.map((label, i) => (
          <span key={label} className={value[0] >= i * 25 ? "text-primary font-medium" : ""}>
            {label}
          </span>
        ))}
      </div>
    </div>
  );
};
