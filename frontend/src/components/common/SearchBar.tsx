import { useState, FormEvent } from 'react';
import { Search, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface SearchBarProps {
  onSearch: (query: string, type: 'semantic' | 'keyword') => void;
  loading?: boolean;
  showTypeSelector?: boolean;
  placeholder?: string;
  size?: 'default' | 'large';
}

export const SearchBar = ({
  onSearch,
  loading = false,
  showTypeSelector = true,
  placeholder = 'Rechercher des articles scientifiques...',
  size = 'default'
}: SearchBarProps) => {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState<'semantic' | 'keyword'>('semantic');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query, searchType);
    }
  };

  const inputClass = size === 'large' 
    ? 'h-14 text-lg pl-12 pr-4' 
    : 'h-12 pl-10 pr-4';

  const iconClass = size === 'large' 
    ? 'h-6 w-6 left-4' 
    : 'h-5 w-5 left-3';

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className={`absolute ${iconClass} top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none`} />
          <Input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholder}
            className={inputClass}
            disabled={loading}
          />
        </div>

        {showTypeSelector && (
          <Select value={searchType} onValueChange={(value: 'semantic' | 'keyword') => setSearchType(value)}>
            <SelectTrigger className="w-full sm:w-[180px] h-12">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="semantic">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-accent" />
                  Sémantique
                </div>
              </SelectItem>
              <SelectItem value="keyword">
                <div className="flex items-center gap-2">
                  <Search className="h-4 w-4" />
                  Mots-clés
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        )}

        <Button 
          type="submit" 
          disabled={loading || !query.trim()}
          className="h-12 px-8"
          size={size === 'large' ? 'lg' : 'default'}
        >
          {loading ? 'Recherche...' : 'Rechercher'}
        </Button>
      </div>

      {searchType === 'semantic' && (
        <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
          <Sparkles className="h-3 w-3 text-accent" />
          Recherche sémantique activée - trouve des résultats par contexte et sens
        </p>
      )}
    </form>
  );
};
