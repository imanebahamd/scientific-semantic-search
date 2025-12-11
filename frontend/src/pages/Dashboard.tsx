import { 
  BookOpen, 
  Search, 
  TrendingUp,
  BarChart3
} from 'lucide-react';
import { Header } from '@/components/common/Header';
import { Footer } from '@/components/common/Footer';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { StatCard } from '@/components/dashboard/StatCard';
import { ChartCard } from '@/components/dashboard/ChartCard';
import { Badge } from '@/components/ui/badge';
import { useDashboard } from '@/hooks/useDashboard';
import {
  Bar,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';

export default function Dashboard() {
  const { stats, loading, error } = useDashboard();

  if (loading) {
    return (
      <div className="flex flex-col min-h-screen">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <LoadingSpinner size="lg" text="Chargement des statistiques..." />
        </main>
        <Footer />
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="flex flex-col min-h-screen">
        <Header />
        <main className="flex-1 container py-12 text-center">
          <h1 className="text-2xl font-bold mb-4">Erreur de chargement</h1>
          <p className="text-muted-foreground">{error}</p>
        </main>
        <Footer />
      </div>
    );
  }

  const COLORS = [
    'hsl(var(--chart-1))',
    'hsl(var(--chart-2))',
    'hsl(var(--chart-3))',
    'hsl(var(--chart-4))',
    'hsl(var(--chart-5))'
  ];

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      
      <main className="flex-1 container py-8">
        <div className="space-y-8">
          {/* Page Header */}
          <div>
            <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
            <p className="text-muted-foreground">
              Statistiques et analytics du corpus documentaire
            </p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="Total Articles"
              value={stats.totalArticles.toLocaleString()}
              description="Documents indexés"
              icon={BookOpen}
              trend={{ value: 12.5, isPositive: true }}
            />
            
            <StatCard
              title="Recherches"
              value={stats.totalSearches.toLocaleString()}
              description="Requêtes effectuées"
              icon={Search}
              trend={{ value: 8.3, isPositive: true }}
            />
            
            <StatCard
              title="Similarité Moyenne"
              value={`${Math.round(stats.avgSimilarity * 100)}%`}
              description="Précision des résultats"
              icon={TrendingUp}
            />
            
            <StatCard
              title="Catégories"
              value={stats.topCategories.length}
              description="Domaines couverts"
              icon={BarChart3}
            />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Articles per Year */}
            <ChartCard
              title="Articles par année"
              description="Distribution temporelle du corpus"
            >
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={stats.articlesPerYear}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis 
                    dataKey="year" 
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={12}
                  />
                  <YAxis 
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={12}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '6px'
                    }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {stats.articlesPerYear.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            {/* Top Categories */}
            <ChartCard
              title="Top catégories"
              description="Distribution par domaine scientifique"
            >
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={stats.topCategories} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis 
                    type="number"
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={12}
                  />
                  <YAxis 
                    type="category"
                    dataKey="name" 
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={12}
                    width={120}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '6px'
                    }}
                  />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                    {stats.topCategories.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          {/* Top Searches */}
          <ChartCard
            title="Recherches populaires"
            description="Requêtes les plus fréquentes"
          >
            <div className="space-y-3">
              {stats.topSearches.map((search, index) => (
                <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-surface hover:bg-surface-hover transition-colors">
                  <div className="flex items-center gap-3 flex-1">
                    <Badge variant="outline" className="font-mono">
                      #{index + 1}
                    </Badge>
                    <span className="font-medium">{search.query}</span>
                  </div>
                  <Badge variant="secondary">
                    {search.count} recherches
                  </Badge>
                </div>
              ))}
            </div>
          </ChartCard>
        </div>
      </main>

      <Footer />
    </div>
  );
}
