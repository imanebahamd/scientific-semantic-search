import { useState, useCallback } from 'react';
import { api, SearchResult } from '@/services/api';

export interface SearchFilters {
  categories?: string[];
  yearRange?: [number, number];
  minScore?: number;
}

export const useSearch = () => {
  const [results, setResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const searchSemantic = useCallback(async (query: string, filters?: SearchFilters) => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const data = await api.searchSemantic(query, filters);
      setResults(data);
    } catch (err) {
      setError('Failed to perform search. Please try again.');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const searchKeyword = useCallback(async (query: string) => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const data = await api.searchKeyword(query);
      setResults(data);
    } catch (err) {
      setError('Failed to perform search. Please try again.');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const clearResults = useCallback(() => {
    setResults(null);
    setError(null);
  }, []);

  return {
    results,
    loading,
    error,
    searchSemantic,
    searchKeyword,
    clearResults
  };
};
