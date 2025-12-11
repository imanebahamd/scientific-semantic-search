// Mock API service for scientific article search
// In production, replace with actual API calls

export interface Article {
  id: string;
  title: string;
  authors: string[];
  year: number;
  abstract: string;
  categories: string[];
  doi?: string;
  pdfUrl?: string;
  citations?: number;
  similarity?: number;
  matchingKeywords?: string[];
}

export interface SearchResult {
  query: string;
  results: Article[];
  totalCount: number;
  searchType: 'semantic' | 'keyword';
}

export interface DashboardStats {
  totalArticles: number;
  totalSearches: number;
  avgSimilarity: number;
  topCategories: { name: string; count: number }[];
  articlesPerYear: { year: number; count: number }[];
  topSearches: { query: string; count: number }[];
}

// Mock data
const mockArticles: Article[] = [
  {
    id: '1',
    title: 'Deep Learning for Natural Language Processing: A Comprehensive Survey',
    authors: ['Zhang, Y.', 'Wang, L.', 'Chen, M.'],
    year: 2023,
    abstract: 'This paper presents a comprehensive survey of deep learning techniques for natural language processing. We review state-of-the-art architectures including transformers, BERT, and GPT models, analyzing their applications in various NLP tasks.',
    categories: ['Machine Learning', 'NLP', 'Deep Learning'],
    doi: '10.1000/xyz123',
    pdfUrl: '/papers/deep-learning-nlp.pdf',
    citations: 156,
    similarity: 0.94,
    matchingKeywords: ['deep learning', 'natural language', 'transformers']
  },
  {
    id: '2',
    title: 'Transformer Models in Computer Vision: Recent Advances',
    authors: ['Liu, J.', 'Smith, A.', 'Johnson, R.'],
    year: 2023,
    abstract: 'Vision transformers have revolutionized computer vision tasks. This work explores recent advances in applying transformer architectures to image classification, object detection, and semantic segmentation.',
    categories: ['Computer Vision', 'Machine Learning', 'Deep Learning'],
    doi: '10.1000/abc456',
    citations: 203,
    similarity: 0.87,
    matchingKeywords: ['transformers', 'computer vision', 'deep learning']
  },
  {
    id: '3',
    title: 'Semantic Search Engines: Architecture and Implementation',
    authors: ['Brown, T.', 'Garcia, M.', 'Lee, K.'],
    year: 2022,
    abstract: 'We propose a novel architecture for semantic search engines utilizing sentence embeddings and neural information retrieval. Our approach significantly improves search relevance compared to traditional keyword-based methods.',
    categories: ['Information Retrieval', 'NLP', 'Search Systems'],
    doi: '10.1000/def789',
    citations: 89,
    similarity: 0.91,
    matchingKeywords: ['semantic search', 'embeddings', 'information retrieval']
  },
  {
    id: '4',
    title: 'BERT and Its Variants: A Comparative Study',
    authors: ['Martinez, L.', 'Wilson, P.'],
    year: 2022,
    abstract: 'This study compares various BERT-based models including RoBERTa, ALBERT, and DistilBERT across multiple benchmark tasks, providing insights into their performance trade-offs.',
    categories: ['NLP', 'Machine Learning'],
    citations: 127,
    similarity: 0.82,
    matchingKeywords: ['BERT', 'language models', 'NLP']
  },
  {
    id: '5',
    title: 'Neural Information Retrieval: From Theory to Practice',
    authors: ['Anderson, K.', 'Thomas, R.', 'White, S.'],
    year: 2023,
    abstract: 'A comprehensive guide to neural information retrieval systems, covering dense retrieval, cross-encoders, and hybrid approaches for document ranking.',
    categories: ['Information Retrieval', 'Deep Learning'],
    citations: 94,
    similarity: 0.88,
    matchingKeywords: ['neural', 'information retrieval', 'ranking']
  }
];

// API functions
export const api = {
  // Semantic search
  async searchSemantic(query: string, filters?: {
    categories?: string[];
    yearRange?: [number, number];
    minScore?: number;
  }): Promise<SearchResult> {
    await new Promise(resolve => setTimeout(resolve, 800));
    
    let results = [...mockArticles];
    
    // Apply filters
    if (filters?.categories && filters.categories.length > 0) {
      results = results.filter(article => 
        article.categories.some(cat => filters.categories?.includes(cat))
      );
    }
    
    if (filters?.yearRange) {
      const [minYear, maxYear] = filters.yearRange;
      results = results.filter(article => 
        article.year >= minYear && article.year <= maxYear
      );
    }
    
    if (filters?.minScore) {
      results = results.filter(article => 
        (article.similarity || 0) >= filters.minScore
      );
    }
    
    return {
      query,
      results,
      totalCount: results.length,
      searchType: 'semantic'
    };
  },

  // Keyword search
  async searchKeyword(query: string): Promise<SearchResult> {
    await new Promise(resolve => setTimeout(resolve, 600));
    
    return {
      query,
      results: mockArticles.slice(0, 3),
      totalCount: mockArticles.length,
      searchType: 'keyword'
    };
  },

  // Get article by ID
  async getArticle(id: string): Promise<Article | null> {
    await new Promise(resolve => setTimeout(resolve, 400));
    
    return mockArticles.find(article => article.id === id) || null;
  },

  // Get similar articles
  async getSimilarArticles(id: string): Promise<Article[]> {
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return mockArticles
      .filter(article => article.id !== id)
      .slice(0, 3)
      .map(article => ({
        ...article,
        similarity: Math.random() * 0.3 + 0.7
      }));
  },

  // Get dashboard statistics
  async getDashboardStats(): Promise<DashboardStats> {
    await new Promise(resolve => setTimeout(resolve, 600));
    
    return {
      totalArticles: 1247,
      totalSearches: 8934,
      avgSimilarity: 0.847,
      topCategories: [
        { name: 'Machine Learning', count: 456 },
        { name: 'NLP', count: 382 },
        { name: 'Computer Vision', count: 289 },
        { name: 'Deep Learning', count: 267 },
        { name: 'Information Retrieval', count: 156 }
      ],
      articlesPerYear: [
        { year: 2020, count: 234 },
        { year: 2021, count: 312 },
        { year: 2022, count: 387 },
        { year: 2023, count: 314 }
      ],
      topSearches: [
        { query: 'deep learning transformers', count: 234 },
        { query: 'semantic search', count: 189 },
        { query: 'BERT models', count: 156 },
        { query: 'computer vision', count: 134 },
        { query: 'neural networks', count: 98 }
      ]
    };
  }
};
