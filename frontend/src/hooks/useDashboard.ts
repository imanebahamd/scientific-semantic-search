// src/hooks/useDashboard.ts
import { useState, useEffect } from 'react';
import { api, DashboardStats } from '@/services/api';

export const useDashboard = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await api.getDashboardStats();
        setStats(data);
      } catch (err) {
        const errorMessage = err instanceof Error 
          ? err.message 
          : 'Erreur lors du chargement des statistiques';
        setError(errorMessage);
        console.error('Dashboard error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const refetch = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (err) {
      const errorMessage = err instanceof Error 
        ? err.message 
        : 'Erreur lors du chargement des statistiques';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return {
    stats,
    loading,
    error,
    refetch,
  };
};