import { useState } from 'react';
import { Filter, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { SearchFilters } from '@/hooks/useSearch';

interface FilterSectionProps {
  onFilterChange: (filters: SearchFilters) => void;
  onClose?: () => void;
  isMobile?: boolean;
}

const CATEGORIES = [
  'Machine Learning',
  'NLP',
  'Computer Vision',
  'Deep Learning',
  'Information Retrieval',
  'Search Systems'
];

const YEARS = [2020, 2021, 2022, 2023, 2024];

export const FilterSection = ({ onFilterChange, onClose, isMobile = false }: FilterSectionProps) => {
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [yearRange, setYearRange] = useState<[number, number]>([2020, 2024]);
  const [minScore, setMinScore] = useState(0);

  const handleCategoryToggle = (category: string) => {
    const newCategories = selectedCategories.includes(category)
      ? selectedCategories.filter(c => c !== category)
      : [...selectedCategories, category];
    
    setSelectedCategories(newCategories);
    applyFilters(newCategories, yearRange, minScore);
  };

  const handleYearRangeChange = (values: number[]) => {
    const newRange: [number, number] = [values[0], values[1]];
    setYearRange(newRange);
    applyFilters(selectedCategories, newRange, minScore);
  };

  const handleMinScoreChange = (values: number[]) => {
    const newScore = values[0];
    setMinScore(newScore);
    applyFilters(selectedCategories, yearRange, newScore);
  };

  const applyFilters = (categories: string[], years: [number, number], score: number) => {
    onFilterChange({
      categories: categories.length > 0 ? categories : undefined,
      yearRange: years,
      minScore: score > 0 ? score / 100 : undefined
    });
  };

  const clearFilters = () => {
    setSelectedCategories([]);
    setYearRange([2020, 2024]);
    setMinScore(0);
    onFilterChange({});
  };

  const hasActiveFilters = selectedCategories.length > 0 || minScore > 0 || 
    yearRange[0] !== 2020 || yearRange[1] !== 2024;

  return (
    <Card className={isMobile ? 'border-0 shadow-none' : ''}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className="text-lg flex items-center gap-2">
          <Filter className="h-5 w-5" />
          Filtres
        </CardTitle>
        {isMobile && onClose && (
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        )}
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Categories */}
        <div className="space-y-3">
          <Label className="text-sm font-semibold">Catégories</Label>
          <div className="space-y-2">
            {CATEGORIES.map((category) => (
              <div key={category} className="flex items-center space-x-2">
                <Checkbox
                  id={category}
                  checked={selectedCategories.includes(category)}
                  onCheckedChange={() => handleCategoryToggle(category)}
                />
                <Label
                  htmlFor={category}
                  className="text-sm font-normal cursor-pointer"
                >
                  {category}
                </Label>
              </div>
            ))}
          </div>
        </div>

        {/* Year Range */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-sm font-semibold">Années</Label>
            <span className="text-sm text-muted-foreground">
              {yearRange[0]} - {yearRange[1]}
            </span>
          </div>
          <Slider
            min={2020}
            max={2024}
            step={1}
            value={yearRange}
            onValueChange={handleYearRangeChange}
            className="py-4"
          />
        </div>

        {/* Minimum Score */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-sm font-semibold">Score minimum</Label>
            <span className="text-sm text-muted-foreground">
              {minScore}%
            </span>
          </div>
          <Slider
            min={0}
            max={100}
            step={5}
            value={[minScore]}
            onValueChange={handleMinScoreChange}
            className="py-4"
          />
        </div>

        {/* Clear filters */}
        {hasActiveFilters && (
          <Button 
            variant="outline" 
            size="sm" 
            onClick={clearFilters}
            className="w-full"
          >
            Effacer les filtres
          </Button>
        )}
      </CardContent>
    </Card>
  );
};
