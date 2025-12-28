import { Link } from 'react-router-dom';
import { FileText, ExternalLink, BookmarkPlus, Users, Calendar } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { SimilarityIndicator } from './SimilarityIndicator';
import { Article } from '@/services/api';

interface ResultCardProps {
  article: Article;
}

export const ResultCard = ({ article }: ResultCardProps) => {
  return (
    <Card className="hover:shadow-lg transition-all duration-200 hover:border-primary/50">
      <CardContent className="p-6">
        <div className="space-y-4">
          {/* Title and similarity */}
          <div className="space-y-3">
            <div className="flex items-start justify-between gap-4">
              <Link 
                to={`/article/${article.id}`}
                className="flex-1"
              >
                <h3 className="text-lg font-bold text-foreground hover:text-primary transition-colors line-clamp-2">
                  {article.title}
                </h3>
              </Link>
              
              {article.similarity && (
                <div className="w-32 shrink-0">
                  <SimilarityIndicator score={article.similarity} showLabel={false} />
                </div>
              )}
            </div>

            {/* Authors and year */}
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <Users className="h-4 w-4" />
                <span>{article.authors.join(', ')}</span>
              </div>
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                <span>{article.year}</span>
              </div>
              {article.citations !== undefined && (
                <span className="font-medium">
                  {article.citations} citations
                </span>
              )}
            </div>
          </div>

          {/* Abstract */}
          <p className="text-sm text-muted-foreground line-clamp-3">
            {article.abstract}
          </p>

          {/* Categories */}
          <div className="flex flex-wrap gap-2">
            {article.categories.map((category) => (
              <Badge key={category} variant="secondary">
                {category}
              </Badge>
            ))}
          </div>

          {/* Matching keywords */}
          {article.matchingKeywords && article.matchingKeywords.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-2 border-t border-border">
              <span className="text-xs font-medium text-muted-foreground">Mots-clés:</span>
              {article.matchingKeywords.map((keyword, index) => (
                <Badge key={index} variant="outline" className="text-xs">
                  {keyword}
                </Badge>
              ))}
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-wrap gap-2 pt-2">
            <Link to={`/article/${article.id}`}>
              <Button size="sm" variant="default">
                <FileText className="h-4 w-4 mr-2" />
                Détails
              </Button>
            </Link>
            
            
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
