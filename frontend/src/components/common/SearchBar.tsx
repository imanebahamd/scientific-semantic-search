// src/components/common/SearchBar.tsx
import { useState } from 'react';
import { Search } from 'lucide-react';
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
  size?: 'default' | 'large';
  showTypeSelector?: boolean;
  placeholder?: string;
}

export const SearchBar = ({
  onSearch,
  loading = false,
  size = 'default',
  showTypeSelector = true,
  placeholder = 'Rechercher des articles scientifiques...',
}: SearchBarProps) => {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState<'semantic' | 'keyword'>('semantic');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim(), searchType);
    }
  };

  const inputClasses = size === 'large' 
    ? 'h-14 text-lg pr-32' 
    : 'h-10 pr-28';

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="relative flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
          <Input
            type="text"
            placeholder={placeholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className={`pl-10 ${inputClasses}`}
            disabled={loading}
          />
        </div>


        <Button
          type="submit"
          disabled={loading || !query.trim()}
          className={size === 'large' ? 'h-14 px-8' : 'h-10'}
        >
          {loading ? (
            <>
              <span className="animate-spin mr-2">⏳</span>
              Recherche...
            </>
          ) : (
            <>
              <Search className="h-4 w-4 mr-2" />
              Rechercher
            </>
          )}
        </Button>
      </div>

      {/* Exemples de recherche */}
      <div className="mt-3 flex flex-wrap gap-2">
        <span className="text-sm text-muted-foreground">Exemples:</span>
        {[
          'machine learning',
          'deep learning transformers',
          'computer vision',
          'natural language processing',
        ].map((example) => (
          <button
            key={example}
            type="button"
            onClick={() => {
              setQuery(example);
              onSearch(example, searchType);
            }}
            className="text-sm text-primary hover:underline"
            disabled={loading}
          >
            {example}
          </button>
        ))}
      </div>
    </form>
  );
};