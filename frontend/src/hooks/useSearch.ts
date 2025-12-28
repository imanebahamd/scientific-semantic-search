// src/hooks/useSearch.ts - Version mise à jour
import { useState } from 'react';
import { api, SearchResult, Article } from '@/services/api';
import { metricsLogger } from '@/services/metricsLogger';

export interface SearchFilters {
  categories?: string[];
  yearRange?: [number, number];
  minScore?: number;
}

export const useSearch = () => {
  const [results, setResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const searchSemantic = async (query: string, filters?: SearchFilters) => {
    if (!query.trim()) {
      setError('Veuillez entrer une requête de recherche');
      return;
    }

    setLoading(true);
    setError(null);
    
    const startTime = Date.now();

    try {
      const result = await api.searchSemantic(query, 10, filters);
      setResults(result);
      
      // Log des métriques
      const executionTime = Date.now() - startTime;
      metricsLogger.logSearchMetrics(result, executionTime);
      
      // Optionnel: afficher les résultats détaillés dans la console
      if (result.results.length > 0) {
        metricsLogger.logDetailedResults(result.results);
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur lors de la recherche';
      setError(errorMessage);
      setResults(null);
      
      // Log de l'erreur
      metricsLogger.logError(err, `Recherche sémantique: "${query}"`);
    } finally {
      setLoading(false);
      
      // Log du temps d'exécution
      metricsLogger.logPerformance(startTime, `Recherche "${query.substring(0, 20)}..."`);
    }
  };

  const searchKeyword = async (query: string) => {
    if (!query.trim()) {
      setError('Veuillez entrer une requête de recherche');
      return;
    }

    setLoading(true);
    setError(null);
    const startTime = Date.now();

    try {
      const result = await api.searchKeyword(query, 10);
      setResults(result);
      
      // Log des métriques
      const executionTime = Date.now() - startTime;
      metricsLogger.logSearchMetrics(result, executionTime);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur lors de la recherche';
      setError(errorMessage);
      setResults(null);
      
      // Log de l'erreur
      metricsLogger.logError(err, `Recherche keyword: "${query}"`);
    } finally {
      setLoading(false);
      
      // Log du temps d'exécution
      metricsLogger.logPerformance(startTime, `Recherche keyword "${query.substring(0, 20)}..."`);
    }
  };

  const clearResults = () => {
    setResults(null);
    setError(null);
  };

  return {
    results,
    loading,
    error,
    searchSemantic,
    searchKeyword,
    clearResults,
  };
};