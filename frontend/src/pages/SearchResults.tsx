import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Filter, AlertCircle } from 'lucide-react';
import { Header } from '@/components/common/Header';
import { Footer } from '@/components/common/Footer';
import { SearchBar } from '@/components/common/SearchBar';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { ResultCard } from '@/components/search/ResultCard';
import { FilterSection } from '@/components/search/FilterSection';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useSearch, SearchFilters } from '@/hooks/useSearch';

export default function SearchResults() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { results, loading, error, searchSemantic, searchKeyword } = useSearch();
  const [filters, setFilters] = useState<SearchFilters>({});
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);

  const query = searchParams.get('q') || '';
  const type = (searchParams.get('type') || 'semantic') as 'semantic' | 'keyword';

  useEffect(() => {
    if (query) {
      performSearch(query, type);
    }
  }, [query, type, filters]);

  const performSearch = (searchQuery: string, searchType: 'semantic' | 'keyword') => {
    if (searchType === 'semantic') {
      searchSemantic(searchQuery, filters);
    } else {
      searchKeyword(searchQuery);
    }
  };

  const handleNewSearch = (newQuery: string, newType: 'semantic' | 'keyword') => {
    setSearchParams({ q: newQuery, type: newType });
  };

  const handleFilterChange = (newFilters: SearchFilters) => {
    setFilters(newFilters);
  };

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      
      <main className="flex-1 container py-8">
        {/* Search Bar */}
        <div className="mb-8">
          <SearchBar 
            onSearch={handleNewSearch}
            loading={loading}
          />
        </div>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Filters - Desktop */}
          <aside className="hidden lg:block w-64 shrink-0">
            <div className="sticky top-20">
              <FilterSection onFilterChange={handleFilterChange} />
            </div>
          </aside>

          {/* Filters - Mobile */}
          <div className="lg:hidden">
            <Sheet open={mobileFiltersOpen} onOpenChange={setMobileFiltersOpen}>
              <SheetTrigger asChild>
                <Button variant="outline" className="w-full">
                  <Filter className="h-4 w-4 mr-2" />
                  Filtres
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-80">
                <FilterSection 
                  onFilterChange={handleFilterChange}
                  onClose={() => setMobileFiltersOpen(false)}
                  isMobile
                />
              </SheetContent>
            </Sheet>
          </div>

          {/* Results */}
          <div className="flex-1 min-w-0">
            {loading ? (
              <LoadingSpinner size="lg" text="Recherche en cours..." />
            ) : results ? (
              <div className="space-y-6">
                {/* Results header */}
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-bold">
                      Résultats de recherche
                    </h2>
                    <p className="text-muted-foreground mt-1">
                      {results.totalCount} article{results.totalCount > 1 ? 's' : ''} trouvé
                      {results.totalCount > 1 ? 's' : ''} pour "{results.query}"
                    </p>
                    {results.searchType === 'semantic' && (
                      <p className="text-sm text-primary mt-1">
                        Recherche sémantique activée
                      </p>
                    )}
                  </div>
                </div>

                {/* Results list */}
                {results.results.length > 0 ? (
                  <div className="space-y-4">
                    {results.results.map((article) => (
                      <ResultCard key={article.id} article={article} />
                    ))}
                  </div>
                ) : (
                  <Alert>
                    <AlertDescription>
                      Aucun résultat trouvé. Essayez de modifier votre recherche ou d'ajuster les filtres.
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-muted-foreground">
                  Utilisez la barre de recherche ci-dessus pour commencer
                </p>
              </div>
            )}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
