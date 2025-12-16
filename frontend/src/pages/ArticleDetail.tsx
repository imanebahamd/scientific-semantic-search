import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  FileText, 
  Download, 
  BookmarkPlus, 
  Users, 
  Calendar,
  ExternalLink,
  Quote,
  ArrowLeft,
  Sparkles
} from 'lucide-react';
import { Header } from '@/components/common/Header';
import { Footer } from '@/components/common/Footer';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { SimilarityIndicator } from '@/components/search/SimilarityIndicator';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { api, Article } from '@/services/api';

export default function ArticleDetail() {
  const { id } = useParams<{ id: string }>();
  const [article, setArticle] = useState<Article | null>(null);
  const [similarArticles, setSimilarArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      if (!id) return;

      setLoading(true);
      try {
        const [articleData, similarData] = await Promise.all([
          api.getArticle(id),
          api.getSimilarArticles(id)
        ]);
        
        setArticle(articleData);
        setSimilarArticles(similarData);
      } catch (error) {
        console.error('Error fetching article:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  if (loading) {
    return (
      <div className="flex flex-col min-h-screen">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <LoadingSpinner size="lg" text="Chargement de l'article..." />
        </main>
        <Footer />
      </div>
    );
  }

  if (!article) {
    return (
      <div className="flex flex-col min-h-screen">
        <Header />
        <main className="flex-1 container py-12 text-center">
          <h1 className="text-2xl font-bold mb-4">Article non trouvé</h1>
          <Link to="/">
            <Button>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Retour à l'accueil
            </Button>
          </Link>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      
      <main className="flex-1 container py-8">
        <div className="max-w-5xl mx-auto space-y-8">
          {/* Back button */}
          <Link to="/">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Retour à la recherche
            </Button>
          </Link>

          {/* Article Header */}
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold mb-4">
                {article.title}
              </h1>
              
              <div className="flex flex-wrap items-center gap-4 text-muted-foreground">
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  <span>{article.authors.join(', ')}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  <span>{article.year}</span>
                </div>
                {article.citations !== undefined && (
                  <div className="font-medium">
                    {article.citations} citations
                  </div>
                )}
              </div>
            </div>

            {/* Categories */}
            <div className="flex flex-wrap gap-2">
              {article.categories.map((category) => (
                <Badge key={category} variant="secondary" className="text-sm">
                  {category}
                </Badge>
              ))}
            </div>

            {/* Actions */}
            <div className="flex flex-wrap gap-3">
              {article.pdfUrl && (
                <Button>
                  <Download className="h-4 w-4 mr-2" />
                  Télécharger PDF
                </Button>
              )}
              
              <Button variant="outline">
                <Quote className="h-4 w-4 mr-2" />
                Exporter BibTeX
              </Button>
              
              <Button variant="outline">
                <BookmarkPlus className="h-4 w-4 mr-2" />
                Sauvegarder
              </Button>
              
              {article.doi && (
                <Button variant="ghost">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  DOI: {article.doi}
                </Button>
              )}
            </div>
          </div>

          <Separator />

          {/* Main Content */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Article Content */}
            <div className="lg:col-span-2 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    Résumé
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground leading-relaxed">
                    {article.abstract}
                  </p>
                </CardContent>
              </Card>

              {article.matchingKeywords && article.matchingKeywords.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Mots-clés correspondants</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {article.matchingKeywords.map((keyword, index) => (
                        <Badge key={index} variant="outline">
                          {keyword}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Similarity Score */}
              {article.similarity && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Score de similarité</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <SimilarityIndicator score={article.similarity} />
                    <p className="text-xs text-muted-foreground mt-3">
                      Basé sur l'analyse sémantique du contenu
                    </p>
                  </CardContent>
                </Card>
              )}

              {/* Metadata */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Métadonnées</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div>
                    <span className="font-medium">Année:</span>
                    <span className="ml-2 text-muted-foreground">{article.year}</span>
                  </div>
                  <div>
                    <span className="font-medium">Auteurs:</span>
                    <span className="ml-2 text-muted-foreground">
                      {article.authors.length}
                    </span>
                  </div>
                  {article.citations !== undefined && (
                    <div>
                      <span className="font-medium">Citations:</span>
                      <span className="ml-2 text-muted-foreground">
                        {article.citations}
                      </span>
                    </div>
                  )}
                  {article.doi && (
                    <div>
                      <span className="font-medium">DOI:</span>
                      <span className="ml-2 text-muted-foreground break-all">
                        {article.doi}
                      </span>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Similar Articles */}
          {similarArticles.length > 0 && (
            <div id="similar" className="space-y-6">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                <h2 className="text-2xl font-bold">Articles similaires</h2>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {similarArticles.map((similar) => (
                  <Link key={similar.id} to={`/article/${similar.id}`}>
                    <Card className="h-full hover:shadow-lg transition-all hover:border-primary/50">
                      <CardContent className="p-4 space-y-3">
                        <div className="space-y-2">
                          <h3 className="font-semibold line-clamp-2 hover:text-primary transition-colors">
                            {similar.title}
                          </h3>
                          <p className="text-xs text-muted-foreground">
                            {similar.authors[0]} et al. ({similar.year})
                          </p>
                        </div>
                        
                        {similar.similarity && (
                          <SimilarityIndicator score={similar.similarity} showLabel={false} />
                        )}
                        
                        <div className="flex flex-wrap gap-1">
                          {similar.categories.slice(0, 2).map((cat) => (
                            <Badge key={cat} variant="outline" className="text-xs">
                              {cat}
                            </Badge>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
