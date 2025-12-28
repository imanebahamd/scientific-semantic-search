import { BookOpen } from 'lucide-react';

export const Footer = () => {
  return (
    <footer className="border-t border-border bg-surface mt-auto">
      <div className="container py-6">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center space-x-3">
            <BookOpen className="h-6 w-6 text-primary" />
            <div>
              <span className="font-bold text-lg block">ScholarSearch</span>
              <p className="text-sm text-muted-foreground">
                Base documentaire intelligente pour articles scientifiques
              </p>
            </div>
          </div>

          <div className="text-center md:text-right">
            <p className="text-sm text-muted-foreground">
              FastAPI • Elasticsearch • Sentence-BERT • React
            </p>
          </div>
        </div>

        <div className="mt-6 pt-6 border-t border-border text-center text-xs text-muted-foreground">
          <p>&copy; 2024 ScholarSearch — Projet universitaire</p>
        </div>
      </div>
    </footer>
  );
};