import { Github, Mail, BookOpen } from 'lucide-react';

export const Footer = () => {
  return (
    <footer className="border-t border-border bg-surface mt-auto">
      <div className="container py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <BookOpen className="h-5 w-5 text-primary" />
              <span className="font-bold">ScholarSearch</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Base documentaire intelligente avec recherche sémantique pour articles scientifiques.
            </p>
          </div>

          <div>
            <h3 className="font-semibold mb-4">Technologies</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>FastAPI + Elasticsearch</li>
              <li>Sentence-BERT</li>
              <li>React + Tailwind CSS</li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold mb-4">Contact</h3>
            <div className="flex space-x-4">
              <a 
                href="https://github.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-primary transition-colors"
              >
                <Github className="h-5 w-5" />
              </a>
              <a 
                href="mailto:contact@scholarsearch.com"
                className="text-muted-foreground hover:text-primary transition-colors"
              >
                <Mail className="h-5 w-5" />
              </a>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-border text-center text-sm text-muted-foreground">
          <p>&copy; 2024 ScholarSearch. Projet universitaire de recherche sémantique.</p>
        </div>
      </div>
    </footer>
  );
};
