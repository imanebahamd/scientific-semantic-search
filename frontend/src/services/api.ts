// src/services/api.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Article {
  id: string;
  title: string;
  authors: string[];
  year: number;
  abstract: string;
  categories: string[];
  primary_category?: string;
  doi?: string;
  pdfUrl?: string;
  citations?: number;
  similarity?: number;
  similarity_score?: number;
  score?: number;
  matchingKeywords?: string[];
  date?: string;
  month?: number;
  source?: string;
  journal_ref?: string;
  update_date?: string;
}

export interface SearchResult {
  query: string;
  results: Article[];
  totalCount: number;
  total?: number;
  searchType: 'semantic' | 'keyword';
  took?: number;
  filtersApplied?: any;
}

export interface DashboardStats {
  totalArticles: number;
  totalSearches: number;
  avgSimilarity: number;
  topCategories: { name: string; count: number }[];
  articlesPerYear: { year: number; count: number }[];
  topSearches: { query: string; count: number }[];
}

export interface CategoryInfo {
  name: string;
  count: number;
}

export interface YearRange {
  min: number;
  max: number;
  years: number[];
}

export interface TrendingSearch {
  query: string;
  count: number;
  trend: 'up' | 'down' | 'stable';
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async fetchWithErrorHandling(url: string, options?: RequestInit) {
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // ============================================
  // HEALTH & INFO
  // ============================================

  async healthCheck() {
    return this.fetchWithErrorHandling(`${this.baseUrl}/health`);
  }

  async getInfo() {
    return this.fetchWithErrorHandling(`${this.baseUrl}/`);
  }

  // ============================================
  // RECHERCHE
  // ============================================

  async searchKeyword(
    query: string, 
    size: number = 10,
    filters?: {
      categories?: string[];
      yearRange?: [number, number];
    }
  ): Promise<SearchResult> {
    let url = `${this.baseUrl}/search?query=${encodeURIComponent(query)}&k=${size}`;
    
    // Ajouter les filtres
    if (filters?.categories && filters.categories.length > 0) {
      url += `&categories=${filters.categories.join(',')}`;
    }
    if (filters?.yearRange) {
      url += `&year_min=${filters.yearRange[0]}&year_max=${filters.yearRange[1]}`;
    }
    
    const data = await this.fetchWithErrorHandling(url);
    
    return {
      query: data.query,
      results: data.results.map((r: any) => this.transformArticle(r)),
      totalCount: data.total || data.results.length,
      total: data.total,
      searchType: 'keyword',
      took: data.took,
    };
  }

  async searchSemantic(query: string, k: number = 10, filters?: {
  categories?: string[];
  yearRange?: [number, number];
  minScore?: number;
}): Promise<SearchResult> {
  // Préparer le body
  const body: any = {
    query: query,
    k: k,
  };
  
  // Préparer les filtres
  const filtersBody: any = {};
  if (filters) {
    if (filters.categories && filters.categories.length > 0) {
      filtersBody.categories = filters.categories;
    }
    if (filters.yearRange) {
      filtersBody.year_min = filters.yearRange[0];
      filtersBody.year_max = filters.yearRange[1];
    }
    if (filters.minScore !== undefined && filters.minScore > 0) {
      filtersBody.min_score = filters.minScore;
    }
  }
  
  // Ajouter filters seulement s'il y a des filtres
  if (Object.keys(filtersBody).length > 0) {
    body.filters = filtersBody;
  }
  
  try {
    // CORRECTION ICI : Enlevez complètement le "?k" de l'URL
    const data = await this.fetchWithErrorHandling(
      `${this.baseUrl}/search/semantic`,  // <-- CORRIGÉ : Pas de "?k"
      {
        method: 'POST',
        body: JSON.stringify(body),
      }
    );
    
    return {
      query: data.query || query,
      results: data.results ? data.results.map((r: any) => this.transformArticle(r)) : [],
      totalCount: data.total || (data.results ? data.results.length : 0),
      total: data.total,
      searchType: 'semantic',
      took: data.took,
      filtersApplied: data.filters_applied,
    };
  } catch (error) {
    console.error('Semantic search error:', error);
    // Fallback sur recherche keyword
    console.warn('Falling back to keyword search');
    return this.searchKeyword(query, k, filters);
  }
}

  // ============================================
  // ARTICLES
  // ============================================

  async getArticle(id: string): Promise<Article> {
    const data = await this.fetchWithErrorHandling(`${this.baseUrl}/paper/${id}`);
    return this.transformArticle(data);
  }

  async getSimilarArticles(id: string, k: number = 5): Promise<Article[]> {
    try {
      const data = await this.fetchWithErrorHandling(
        `${this.baseUrl}/paper/${id}/similar?k=${k}`
      );
      return data.results ? data.results.map((r: any) => this.transformArticle(r)) : [];
    } catch (error) {
      console.warn('Similar articles endpoint not available, using search fallback');
      
      // Fallback: chercher des articles de la même catégorie
      try {
        const article = await this.getArticle(id);
        if (article.categories.length > 0) {
          const searchResults = await this.searchKeyword(article.categories[0], k + 1);
          return searchResults.results
            .filter(a => a.id !== id)
            .slice(0, k);
        }
      } catch (fallbackError) {
        console.error('Fallback also failed:', fallbackError);
      }
      
      return [];
    }
  }

  // ============================================
  // FILTRES DYNAMIQUES
  // ============================================

  async getCategories(): Promise<CategoryInfo[]> {
    try {
      const data = await this.fetchWithErrorHandling(`${this.baseUrl}/categories`);
      return data.categories || [];
    } catch (error) {
      console.warn('Could not fetch categories, using defaults');
      return [
        { name: 'cs.AI', count: 150 },
        { name: 'cs.LG', count: 120 },
        { name: 'cs.CL', count: 95 },
        { name: 'cs.CV', count: 85 },
        { name: 'cs.NE', count: 70 },
        { name: 'cs.SE', count: 60 },
      ];
    }
  }

  async getYearRange(): Promise<YearRange> {
    try {
      const data = await this.fetchWithErrorHandling(`${this.baseUrl}/years`);
      return {
        min: data.min_year || 2020,
        max: data.max_year || 2024,
        years: data.years || [],
      };
    } catch (error) {
      console.warn('Could not fetch year range, using defaults');
      return {
        min: 2020,
        max: 2024,
        years: [2020, 2021, 2022, 2023, 2024],
      };
    }
  }

  // ============================================
  // STATISTIQUES
  // ============================================

  async getDashboardStats(): Promise<DashboardStats> {
    try {
      const data = await this.fetchWithErrorHandling(`${this.baseUrl}/stats`);
      
      // Normaliser les données pour le frontend
      const categories = Array.isArray(data.categories) ? data.categories : 
        Array.isArray(data.top_categories) ? data.top_categories : [];
      
      const years = Array.isArray(data.years) ? data.years :
        Array.isArray(data.articlesPerYear) ? data.articlesPerYear : [];
      
      const topSearches = Array.isArray(data.top_searches) ? data.top_searches : [];
      
      return {
        totalArticles: data.total_papers || data.totalArticles || 0,
        totalSearches: data.total_searches || data.totalSearches || 0,
        avgSimilarity: data.avg_similarity || 0.847,
        topCategories: categories.map((c: any) => ({
          name: c.name || c.key || c.category || '',
          count: c.count || c.doc_count || 0,
        })),
        articlesPerYear: years.map((y: any) => ({
          year: y.year || parseInt(y.key_as_string || y.key) || 2023,
          count: y.count || y.doc_count || 0,
        })),
        topSearches: topSearches.map((s: any) => ({
          query: s.query || s.key || '',
          count: s.count || s.doc_count || 0,
        })),
      };
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      // Retourner des données par défaut
      return {
        totalArticles: 1247,
        totalSearches: 8934,
        avgSimilarity: 0.847,
        topCategories: [
          { name: 'cs.AI', count: 150 },
          { name: 'cs.LG', count: 120 },
          { name: 'cs.CL', count: 95 },
          { name: 'cs.CV', count: 85 },
          { name: 'cs.NE', count: 70 },
          { name: 'cs.SE', count: 60 },
        ],
        articlesPerYear: [
          { year: 2024, count: 120 },
          { year: 2023, count: 280 },
          { year: 2022, count: 320 },
          { year: 2021, count: 290 },
          { year: 2020, count: 237 },
        ],
        topSearches: [
          { query: 'machine learning', count: 45 },
          { query: 'deep learning', count: 38 },
          { query: 'neural networks', count: 32 },
        ],
      };
    }
  }

  async getTrendingSearches(): Promise<TrendingSearch[]> {
    try {
      const data = await this.fetchWithErrorHandling(`${this.baseUrl}/search/trending`);
      return data.trending_searches || [];
    } catch (error) {
      console.warn('Could not fetch trending searches');
      return [];
    }
  }

  // ============================================
  // TRANSFORMATIONS
  // ============================================

  private transformArticle(data: any): Article {
    // Utiliser similarity_score en priorité, puis similarity, puis score normalisé
    const similarity = data.similarity_score || data.similarity || 
      (data.score ? data.score / 10 : undefined);
    
    return {
      id: data.id || data._id || '',
      title: data.title || '',
      authors: this.parseAuthors(data.authors),
      year: data.year || new Date().getFullYear(),
      abstract: data.abstract || '',
      categories: this.parseCategories(data.categories),
      primary_category: data.primary_category || (this.parseCategories(data.categories)[0] || ''),
      doi: data.doi,
      pdfUrl: data.pdf_url || data.pdfUrl,
      citations: data.citations,
      similarity: similarity,
      similarity_score: data.similarity_score,
      score: data.score,
      matchingKeywords: data.matching_keywords || [],
      date: data.date,
      month: data.month,
      source: data.source || 'arXiv',
      journal_ref: data.journal_ref,
      update_date: data.update_date,
    };
  }

  private parseAuthors(authors: any): string[] {
    if (!authors) return ['Auteur inconnu'];
    if (Array.isArray(authors)) {
      return authors
        .filter(a => a && typeof a === 'string')
        .map(a => a.trim())
        .filter(a => a.length > 0);
    }
    if (typeof authors === 'string') {
      if (authors.includes(';')) {
        return authors.split(';')
          .map(a => a.trim())
          .filter(a => a.length > 0);
      }
      if (authors.includes(',')) {
        return authors.split(',')
          .map(a => a.trim())
          .filter(a => a.length > 0);
      }
      return [authors.trim()].filter(a => a.length > 0);
    }
    return ['Auteur inconnu'];
  }

  private parseCategories(categories: any): string[] {
    if (!categories) return [];
    if (Array.isArray(categories)) {
      return categories
        .filter(c => c && typeof c === 'string')
        .map(c => c.trim())
        .filter(c => c.length > 0);
    }
    if (typeof categories === 'string') {
      if (categories.includes(',')) {
        return categories.split(',')
          .map(c => c.trim())
          .filter(c => c.length > 0);
      }
      if (categories.includes(' ')) {
        return categories.split(' ')
          .map(c => c.trim())
          .filter(c => c.length > 0);
      }
      return [categories.trim()].filter(c => c.length > 0);
    }
    return [];
  }

  // ============================================
  // UTILITAIRES
  // ============================================

  async testConnection(): Promise<boolean> {
    try {
      const health = await this.healthCheck();
      return health.status === 'healthy';
    } catch (error) {
      console.error('Connection test failed:', error);
      return false;
    }
  }

  async getSystemInfo(): Promise<{
    health: any;
    stats: DashboardStats;
    categories: CategoryInfo[];
    yearRange: YearRange;
  }> {
    try {
      const [health, stats, categories, yearRange] = await Promise.all([
        this.healthCheck(),
        this.getDashboardStats(),
        this.getCategories(),
        this.getYearRange(),
      ]);

      return {
        health,
        stats,
        categories,
        yearRange,
      };
    } catch (error) {
      console.error('Error fetching system info:', error);
      throw error;
    }
  }

  async advancedSearch(params: {
    query: string;
    type: 'semantic' | 'keyword';
    filters?: {
      categories?: string[];
      yearRange?: [number, number];
      minScore?: number;
    };
    limit?: number;
  }): Promise<SearchResult> {
    const { query, type, filters, limit = 10 } = params;

    if (type === 'semantic') {
      return this.searchSemantic(query, limit, filters);
    } else {
      return this.searchKeyword(query, limit, filters);
    }
  }

  getSearchStats(results: Article[]): {
    totalResults: number;
    averageYear: number;
    categoryDistribution: Record<string, number>;
    authorCount: number;
    avgSimilarity: number;
  } {
    if (results.length === 0) {
      return {
        totalResults: 0,
        averageYear: 0,
        categoryDistribution: {},
        authorCount: 0,
        avgSimilarity: 0,
      };
    }

    // Année moyenne
    const years = results.map(r => r.year).filter(y => y > 0);
    const averageYear = years.length > 0 
      ? Math.round(years.reduce((a, b) => a + b, 0) / years.length)
      : 0;

    // Distribution des catégories
    const categoryDistribution: Record<string, number> = {};
    results.forEach(article => {
      article.categories.forEach(cat => {
        categoryDistribution[cat] = (categoryDistribution[cat] || 0) + 1;
      });
    });

    // Nombre d'auteurs uniques
    const uniqueAuthors = new Set<string>();
    results.forEach(article => {
      article.authors.forEach(author => uniqueAuthors.add(author));
    });

    // Similarité moyenne
    const similarities = results.map(r => r.similarity || 0).filter(s => s > 0);
    const avgSimilarity = similarities.length > 0
      ? parseFloat((similarities.reduce((a, b) => a + b, 0) / similarities.length).toFixed(3))
      : 0;

    return {
      totalResults: results.length,
      averageYear,
      categoryDistribution,
      authorCount: uniqueAuthors.size,
      avgSimilarity,
    };
  }

  async exportSearchResults(results: Article[], format: 'json' | 'csv' = 'json'): Promise<string> {
    if (format === 'json') {
      return JSON.stringify(results, null, 2);
    } else {
      // CSV export
      const headers = ['ID', 'Title', 'Authors', 'Year', 'Categories', 'Similarity', 'Abstract'];
      const rows = results.map(article => [
        article.id,
        `"${article.title.replace(/"/g, '""')}"`,
        `"${article.authors.join('; ')}"`,
        article.year,
        `"${article.categories.join(', ')}"`,
        article.similarity ? (article.similarity * 100).toFixed(1) + '%' : 'N/A',
        `"${article.abstract.replace(/"/g, '""').substring(0, 200)}..."`
      ]);
      
      return [
        headers.join(','),
        ...rows.map(row => row.join(','))
      ].join('\n');
    }
  }
}

// Instance singleton de l'API
export const api = new ApiService();

// Export du type pour utilisation externe
export type { ApiService };

// Export de fonctions helper
export const formatAuthors = (authors: string[], maxDisplay: number = 3): string => {
  if (authors.length === 0) return 'Auteur inconnu';
  if (authors.length <= maxDisplay) return authors.join(', ');
  return `${authors.slice(0, maxDisplay).join(', ')} et al.`;
};

export const formatCategories = (categories: string[]): string => {
  if (categories.length === 0) return 'Non catégorisé';
  return categories.slice(0, 3).join(' • ') + (categories.length > 3 ? ` +${categories.length - 3}` : '');
};

export const formatYear = (year: number): string => {
  if (!year || year === 0) return 'Année inconnue';
  return year.toString();
};

export const getScoreColor = (score: number): string => {
  if (!score) return 'text-muted-foreground';
  if (score >= 0.9) return 'text-green-600';
  if (score >= 0.8) return 'text-green-500';
  if (score >= 0.7) return 'text-yellow-500';
  if (score >= 0.6) return 'text-orange-500';
  return 'text-red-500';
};

export const getScoreLabel = (score: number): string => {
  if (!score) return 'Non évalué';
  if (score >= 0.9) return 'Excellent';
  if (score >= 0.8) return 'Très bon';
  if (score >= 0.7) return 'Bon';
  if (score >= 0.6) return 'Moyen';
  return 'Faible';
};

export const formatSimilarity = (score: number | undefined): string => {
  if (!score) return 'N/A';
  return `${(score * 100).toFixed(1)}%`;
};