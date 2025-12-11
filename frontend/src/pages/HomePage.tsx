import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Search, TrendingUp, Database, Zap } from 'lucide-react';
import { Header } from '@/components/common/Header';
import { Footer } from '@/components/common/Footer';
import { SearchBar } from '@/components/common/SearchBar';
import { Card, CardContent } from '@/components/ui/card';

export default function HomePage() {
  const navigate = useNavigate();
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (query: string, type: 'semantic' | 'keyword') => {
    setIsSearching(true);
    // Simulate search delay
    await new Promise(resolve => setTimeout(resolve, 500));
    navigate(`/search?q=${encodeURIComponent(query)}&type=${type}`);
  };

  const features = [
    {
      icon: Sparkles,
      title: 'Recherche Sémantique',
      description: 'Trouvez des articles par contexte et sens, pas seulement par mots-clés exacts.'
    },
    {
      icon: TrendingUp,
      title: 'Similarité Contextuelle',
      description: 'Découvrez des articles connexes grâce à l\'analyse sémantique avancée.'
    },
    {
      icon: Database,
      title: 'Base Étendue',
      description: 'Accédez à une collection de 1247+ articles scientifiques indexés.'
    },
    {
      icon: Zap,
      title: 'Résultats Rapides',
      description: 'Recherche instantanée avec scores de pertinence en temps réel.'
    }
  ];

  const stats = [
    { value: '1,247', label: 'Articles indexés' },
    { value: '8,934', label: 'Recherches effectuées' },
    { value: '84.7%', label: 'Précision moyenne' }
  ];

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      
      <main className="flex-1">
        {/* Hero Section */}
        <section className="py-20 px-4 bg-gradient-to-b from-background to-surface">
          <div className="container max-w-4xl mx-auto text-center space-y-8">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium">
                <Sparkles className="h-4 w-4" />
                Recherche Sémantique Intelligente
              </div>
              
              <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
                Découvrez la science
                <span className="text-primary block mt-2">au-delà des mots-clés</span>
              </h1>
              
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                Une base documentaire intelligente propulsée par l'IA pour explorer 
                la littérature scientifique avec une compréhension contextuelle profonde.
              </p>
            </div>

            {/* Search Bar */}
            <div className="max-w-3xl mx-auto pt-4">
              <SearchBar 
                onSearch={handleSearch}
                loading={isSearching}
                size="large"
              />
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 pt-8">
              {stats.map((stat, index) => (
                <div key={index} className="space-y-1">
                  <p className="text-3xl font-bold text-primary">{stat.value}</p>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-20 px-4">
          <div className="container max-w-6xl mx-auto">
            <div className="text-center mb-12 space-y-4">
              <h2 className="text-3xl md:text-4xl font-bold">
                Fonctionnalités Avancées
              </h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Exploitez la puissance de l'intelligence artificielle pour une recherche 
                scientifique plus pertinente et contextuelle.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {features.map((feature, index) => (
                <Card key={index} className="hover:shadow-lg transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex gap-4">
                      <div className="shrink-0">
                        <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                          <feature.icon className="h-6 w-6 text-primary" />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <h3 className="text-xl font-bold">{feature.title}</h3>
                        <p className="text-muted-foreground">{feature.description}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Technology Section */}
        <section className="py-20 px-4 bg-surface">
          <div className="container max-w-4xl mx-auto text-center space-y-8">
            <div className="space-y-4">
              <h2 className="text-3xl md:text-4xl font-bold">
                Technologies Utilisées
              </h2>
              <p className="text-lg text-muted-foreground">
                Une stack moderne pour des performances optimales
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardContent className="p-6 text-center space-y-2">
                  <h3 className="font-bold">Backend</h3>
                  <p className="text-sm text-muted-foreground">
                    FastAPI + Elasticsearch
                  </p>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-6 text-center space-y-2">
                  <h3 className="font-bold">Intelligence Artificielle</h3>
                  <p className="text-sm text-muted-foreground">
                    Sentence-BERT
                  </p>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-6 text-center space-y-2">
                  <h3 className="font-bold">Frontend</h3>
                  <p className="text-sm text-muted-foreground">
                    React + Tailwind CSS
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20 px-4">
          <div className="container max-w-3xl mx-auto text-center space-y-6">
            <h2 className="text-3xl md:text-4xl font-bold">
              Prêt à explorer ?
            </h2>
            <p className="text-lg text-muted-foreground">
              Commencez votre recherche dès maintenant et découvrez des articles 
              scientifiques pertinents grâce à notre moteur de recherche sémantique.
            </p>
            <SearchBar 
              onSearch={handleSearch}
              loading={isSearching}
              showTypeSelector={false}
              placeholder="Essayez 'deep learning', 'semantic search'..."
            />
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
