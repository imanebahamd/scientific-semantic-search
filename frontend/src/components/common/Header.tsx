import { Link, useLocation } from 'react-router-dom';
import { Search, BarChart3, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';

export const Header = () => {
  const location = useLocation();
  
  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <Link to="/" className="flex items-center space-x-2">
          <BookOpen className="h-6 w-6 text-primary" />
          <span className="text-xl font-bold">ScholarSearch</span>
        </Link>

        <nav className="flex items-center space-x-1">
          <Link to="/">
            <Button 
              variant={isActive('/') ? 'secondary' : 'ghost'}
              size="sm"
              className="gap-2"
            >
              <Search className="h-4 w-4" />
              <span className="hidden sm:inline">Recherche</span>
            </Button>
          </Link>
          
          
        </nav>
      </div>
    </header>
  );
};
