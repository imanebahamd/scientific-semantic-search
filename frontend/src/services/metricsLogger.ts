// src/services/metricsLogger.ts
export interface SearchMetrics {
  query: string;
  searchType: 'semantic' | 'keyword';
  timestamp: Date;
  executionTime: number;
  totalResults: number;
  topScores: number[];
  filters?: any;
  categoriesDistribution?: Record<string, number>;
  averageScore?: number;
}

export interface SearchStats {
  query: string;
  type: string;
  duration: number;
  totalResults: number;
  scoreStats: {
    min: number;
    max: number;
    avg: number;
    median: number;
  };
  categories: Record<string, number>;
  topResult: {
    title: string;
    score: number;
  };
}

class MetricsLogger {
  private static instance: MetricsLogger;
  private searchHistory: SearchMetrics[] = [];
  private readonly maxHistory = 50;
  private readonly consoleStyles = {
    header: 'font-weight: bold; font-size: 14px; color: #3498db;',
    title: 'font-weight: bold; font-size: 12px; color: #2c3e50;',
    success: 'color: #27ae60; font-weight: bold;',
    warning: 'color: #f39c12;',
    info: 'color: #3498db;',
    error: 'color: #e74c3c; font-weight: bold;',
    highlight: 'color: #9b59b6; font-weight: bold;',
    metric: 'color: #16a085;',
    value: 'color: #2c3e50;',
  };

  private constructor() {
    // Singleton pattern
  }

  static getInstance(): MetricsLogger {
    if (!MetricsLogger.instance) {
      MetricsLogger.instance = new MetricsLogger();
    }
    return MetricsLogger.instance;
  }

  private formatTable(data: any, title?: string): void {
    if (title) {
      console.log(`%c${title}`, this.consoleStyles.title);
    }
    
    // Créer un tableau formaté
    if (Array.isArray(data)) {
      console.table(data);
    } else if (typeof data === 'object') {
      console.table([data]);
    } else {
      console.log(data);
    }
  }

  private formatHeader(text: string): void {
    const border = '═'.repeat(text.length + 4);
    console.log(`%c╔${border}╗`, this.consoleStyles.header);
    console.log(`%c║  ${text.toUpperCase()}  ║`, this.consoleStyles.header);
    console.log(`%c╚${border}╝`, this.consoleStyles.header);
  }

  private calculateStats(scores: number[]): {
    min: number;
    max: number;
    avg: number;
    median: number;
    stdDev: number;
  } {
    if (scores.length === 0) {
      return { min: 0, max: 0, avg: 0, median: 0, stdDev: 0 };
    }

    const sorted = [...scores].sort((a, b) => a - b);
    const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
    
    // Calcul de la médiane
    const middle = Math.floor(sorted.length / 2);
    const median = sorted.length % 2 === 0 
      ? (sorted[middle - 1] + sorted[middle]) / 2 
      : sorted[middle];
    
    // Calcul de l'écart-type
    const squareDiffs = scores.map(score => Math.pow(score - avg, 2));
    const avgSquareDiff = squareDiffs.reduce((a, b) => a + b, 0) / scores.length;
    const stdDev = Math.sqrt(avgSquareDiff);

    return {
      min: sorted[0],
      max: sorted[sorted.length - 1],
      avg: parseFloat(avg.toFixed(3)),
      median: parseFloat(median.toFixed(3)),
      stdDev: parseFloat(stdDev.toFixed(3)),
    };
  }

  logSearchMetrics(searchResult: any, executionTime: number): void {
    try {
      const metrics: SearchMetrics = {
        query: searchResult.query,
        searchType: searchResult.searchType,
        timestamp: new Date(),
        executionTime,
        totalResults: searchResult.totalCount,
        topScores: searchResult.results.map((r: any) => r.similarity || r.score || 0).slice(0, 10),
        filters: searchResult.filtersApplied,
      };

      // Calculer la distribution des catégories
      const categories: Record<string, number> = {};
      searchResult.results.forEach((article: any) => {
        article.categories?.forEach((cat: string) => {
          categories[cat] = (categories[cat] || 0) + 1;
        });
      });

      metrics.categoriesDistribution = categories;
      metrics.averageScore = metrics.topScores.length > 0 
        ? parseFloat((metrics.topScores.reduce((a, b) => a + b, 0) / metrics.topScores.length).toFixed(3))
        : 0;

      this.searchHistory.unshift(metrics);
      if (this.searchHistory.length > this.maxHistory) {
        this.searchHistory.pop();
      }

      this.displayMetrics(metrics, searchResult);
    } catch (error) {
      console.error('Error logging metrics:', error);
    }
  }

  private displayMetrics(metrics: SearchMetrics, searchResult: any): void {
    console.clear(); // Optionnel - nettoie la console
    
    // En-tête principale
    this.formatHeader('📊 MÉTRIQUES DE RECHERCHE');
    
    // Informations de base
    console.groupCollapsed('%c📋 Informations de recherche', this.consoleStyles.title);
    console.log(`%c🔍 Requête:`, this.consoleStyles.info, metrics.query);
    console.log(`%c🎯 Type:`, this.consoleStyles.info, metrics.searchType);
    console.log(`%c⏱️  Temps d'exécution:`, this.consoleStyles.info, `${metrics.executionTime}ms`);
    console.log(`%c📄 Résultats totaux:`, this.consoleStyles.info, metrics.totalResults);
    console.log(`%c📅 Date:`, this.consoleStyles.info, metrics.timestamp.toLocaleString());
    console.groupEnd();

    // Statistiques des scores
    if (metrics.topScores.length > 0) {
      const stats = this.calculateStats(metrics.topScores);
      
      console.group('%c📈 Statistiques des scores', this.consoleStyles.title);
      console.log(`%c🏆 Score max:`, this.consoleStyles.highlight, `${(stats.max * 100).toFixed(1)}%`);
      console.log(`%c📊 Score moyen:`, this.consoleStyles.highlight, `${(stats.avg * 100).toFixed(1)}%`);
      console.log(`%c📉 Score médian:`, this.consoleStyles.highlight, `${(stats.median * 100).toFixed(1)}%`);
      console.log(`%c⚖️  Score min:`, this.consoleStyles.highlight, `${(stats.min * 100).toFixed(1)}%`);
      console.log(`%c📐 Écart-type:`, this.consoleStyles.highlight, `${(stats.stdDev * 100).toFixed(1)}%`);
      console.groupEnd();

      // Visualisation des scores
      this.displayScoreChart(metrics.topScores);
    }

    // Distribution des catégories
    if (metrics.categoriesDistribution && Object.keys(metrics.categoriesDistribution).length > 0) {
      console.group('%c🏷️  Distribution des catégories', this.consoleStyles.title);
      const sortedCategories = Object.entries(metrics.categoriesDistribution)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 5);
      
      sortedCategories.forEach(([category, count]) => {
        const percentage = (count / metrics.totalResults * 100).toFixed(1);
        console.log(
          `%c${category}:`, 
          this.consoleStyles.metric, 
          `${count} articles (${percentage}%)`
        );
      });
      console.groupEnd();
    }

    // Top 3 des résultats
    console.group('%c🥇 Top 3 des résultats', this.consoleStyles.title);
    searchResult.results.slice(0, 3).forEach((result: any, index: number) => {
      const emoji = index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉';
      const score = result.similarity || result.score || 0;
      console.log(
        `%c${emoji} ${result.title?.substring(0, 50)}...`, 
        this.consoleStyles.success
      );
      console.log(`   Score: ${(score * 100).toFixed(1)}% | Catégorie: ${result.categories?.[0] || 'N/A'}`);
    });
    console.groupEnd();

    // Filtres appliqués
    if (metrics.filters && Object.keys(metrics.filters).length > 0) {
      console.group('%c⚙️  Filtres appliqués', this.consoleStyles.title);
      Object.entries(metrics.filters).forEach(([key, value]) => {
        console.log(`%c${key}:`, this.consoleStyles.metric, value);
      });
      console.groupEnd();
    }

    // Séparateur
    console.log('%c' + '─'.repeat(80), this.consoleStyles.info);
  }

  private displayScoreChart(scores: number[]): void {
    console.group('%c📊 Distribution des scores (graphique)', this.consoleStyles.title);
    
    const maxScore = Math.max(...scores);
    const minScore = Math.min(...scores);
    const buckets = 10;
    const bucketSize = (maxScore - minScore) / buckets;
    
    // Créer les buckets
    const histogram: number[] = new Array(buckets).fill(0);
    scores.forEach(score => {
      const bucketIndex = Math.min(
        Math.floor((score - minScore) / bucketSize),
        buckets - 1
      );
      histogram[bucketIndex]++;
    });
    
    // Afficher l'histogramme
    const maxCount = Math.max(...histogram);
    histogram.forEach((count, index) => {
      const percentage = (count / scores.length * 100).toFixed(1);
      const barLength = Math.round((count / maxCount) * 20);
      const bar = '█'.repeat(barLength) + '░'.repeat(20 - barLength);
      const rangeStart = (minScore + index * bucketSize).toFixed(3);
      const rangeEnd = (minScore + (index + 1) * bucketSize).toFixed(3);
      
      console.log(
        `[${rangeStart}-${rangeEnd}]: %c${bar} %c${count} (${percentage}%)`,
        this.consoleStyles.highlight,
        this.consoleStyles.metric
      );
    });
    
    console.groupEnd();
  }

  logDetailedResults(results: any[]): void {
    console.group('%c🔍 Résultats détaillés', this.consoleStyles.title);
    
    results.forEach((result, index) => {
      const score = result.similarity || result.score || 0;
      const scoreColor = score >= 0.9 ? this.consoleStyles.success :
                        score >= 0.7 ? this.consoleStyles.info :
                        this.consoleStyles.warning;
      
      console.groupCollapsed(`%c${index + 1}. ${result.title?.substring(0, 60)}...`, scoreColor);
      
      console.log(`%c📊 Score:`, this.consoleStyles.metric, `${(score * 100).toFixed(1)}%`);
      console.log(`%c👥 Auteurs:`, this.consoleStyles.metric, result.authors?.join(', '));
      console.log(`%c🏷️  Catégories:`, this.consoleStyles.metric, result.categories?.join(', '));
      console.log(`%c📅 Année:`, this.consoleStyles.metric, result.year);
      console.log(`%c📄 ID:`, this.consoleStyles.metric, result.id);
      
      if (result.abstract) {
        console.log(`%c📝 Résumé:`, this.consoleStyles.metric, result.abstract.substring(0, 150) + '...');
      }
      
      console.groupEnd();
    });
    
    console.groupEnd();
  }

  getSearchHistory(): SearchMetrics[] {
    return [...this.searchHistory];
  }

  exportHistory(format: 'json' | 'table' = 'table'): void {
    console.group('%c📋 Historique des recherches', this.consoleStyles.title);
    
    if (format === 'json') {
      console.log(JSON.stringify(this.searchHistory, null, 2));
    } else {
      const tableData = this.searchHistory.map(metric => ({
        Requête: metric.query.substring(0, 30) + (metric.query.length > 30 ? '...' : ''),
        Type: metric.searchType,
        'Temps (ms)': metric.executionTime,
        'Résultats': metric.totalResults,
        'Score moyen': `${(metric.averageScore! * 100).toFixed(1)}%`,
        Date: metric.timestamp.toLocaleTimeString(),
      }));
      
      console.table(tableData);
    }
    
    console.groupEnd();
  }

  logPerformance(startTime: number, operation: string): void {
    const duration = Date.now() - startTime;
    let color = this.consoleStyles.success;
    let emoji = '✅';
    
    if (duration > 1000) {
      color = this.consoleStyles.warning;
      emoji = '⚠️ ';
    } else if (duration > 3000) {
      color = this.consoleStyles.error;
      emoji = '❌';
    }
    
    console.log(`%c${emoji} ${operation}: ${duration}ms`, color);
  }

  logError(error: any, context?: string): void {
    console.group('%c❌ ERREUR', this.consoleStyles.error);
    
    if (context) {
      console.log(`%cContexte:`, this.consoleStyles.title, context);
    }
    
    console.log(`%cMessage:`, this.consoleStyles.error, error.message || error);
    
    if (error.stack) {
      console.log(`%cStack trace:`, this.consoleStyles.warning);
      console.trace(error);
    }
    
    console.groupEnd();
  }
}

// Export singleton
export const metricsLogger = MetricsLogger.getInstance();