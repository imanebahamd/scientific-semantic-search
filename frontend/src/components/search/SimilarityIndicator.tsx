import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface SimilarityIndicatorProps {
  score: number;
  showLabel?: boolean;
}

export const SimilarityIndicator = ({ score, showLabel = true }: SimilarityIndicatorProps) => {
  // Determine color based on score
  const getColor = () => {
    if (score >= 0.9) return 'bg-success';
    if (score >= 0.8) return 'bg-success-light';
    if (score >= 0.7) return 'bg-warning';
    return 'bg-muted-foreground';
  };

  const getTextColor = () => {
    if (score >= 0.9) return 'text-success';
    if (score >= 0.8) return 'text-success-light';
    if (score >= 0.7) return 'text-warning';
    return 'text-muted-foreground';
  };

  const getLabel = () => {
    if (score >= 0.9) return 'Excellent';
    if (score >= 0.8) return 'Très bon';
    if (score >= 0.7) return 'Bon';
    return 'Moyen';
  };

  const percentage = Math.round(score * 100);

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-sm">
              {showLabel && (
                <span className={`font-medium ${getTextColor()}`}>
                  {getLabel()}
                </span>
              )}
              <span className={`font-semibold ${getTextColor()}`}>
                {percentage}%
              </span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className={`h-full ${getColor()} transition-all duration-300 rounded-full`}
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p>Score de similarité: {score.toFixed(3)}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};
