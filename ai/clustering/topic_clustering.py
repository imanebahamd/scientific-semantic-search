import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from typing import List, Dict, Any, Tuple
import logging
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TopicClustering:
    """Clustering thématique des articles scientifiques"""
    
    def __init__(self, embeddings_file: str, metadata_file: str = None):
        """
        Initialise le clustering
        
        Args:
            embeddings_file: Fichier .npy contenant les embeddings
            metadata_file: Fichier JSON contenant les métadonnées
        """
        self.embeddings_file = embeddings_file
        self.metadata_file = metadata_file or embeddings_file.replace('.npy', '.json')
        
        # Charger les données
        self.load_data()
        
        logger.info(f"Clustering initialisé avec {len(self.embeddings)} documents")
    
    def load_data(self):
        """Charge les embeddings et métadonnées"""
        try:
            self.embeddings = np.load(self.embeddings_file)
            
            if Path(self.metadata_file).exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = []
                logger.warning(f"Métadonnées non trouvées: {self.metadata_file}")
                
        except Exception as e:
            logger.error(f"Erreur lors du chargement: {e}")
            raise
    
    def find_optimal_clusters(self, max_clusters: int = 10) -> Dict[int, float]:
        """
        Trouve le nombre optimal de clusters
        
        Args:
            max_clusters: Nombre maximum de clusters à tester
            
        Returns:
            Dictionnaire {n_clusters: score_silhouette}
        """
        logger.info(f"Recherche du nombre optimal de clusters (max={max_clusters})")
        
        # Limiter le nombre de points pour accélérer
        sample_size = min(1000, len(self.embeddings))
        indices = np.random.choice(len(self.embeddings), sample_size, replace=False)
        sample_embeddings = self.embeddings[indices]
        
        scores = {}
        
        for n_clusters in range(2, max_clusters + 1):
            try:
                kmeans = KMeans(
                    n_clusters=n_clusters,
                    random_state=42,
                    n_init=10,
                    max_iter=300
                )
                cluster_labels = kmeans.fit_predict(sample_embeddings)
                
                # Calculer le score silhouette
                if len(np.unique(cluster_labels)) > 1:
                    silhouette_avg = silhouette_score(sample_embeddings, cluster_labels)
                    scores[n_clusters] = silhouette_avg
                    
                    logger.info(f"  {n_clusters} clusters: score silhouette = {silhouette_avg:.4f}")
                    
            except Exception as e:
                logger.warning(f"  Erreur pour {n_clusters} clusters: {e}")
                continue
        
        return scores
    
    def perform_clustering(self, n_clusters: int = 8) -> Tuple[np.ndarray, Any]:
        """
        Effectue le clustering K-Means
        
        Args:
            n_clusters: Nombre de clusters
            
        Returns:
            Tuple (labels, modèle KMeans)
        """
        logger.info(f"Clustering avec {n_clusters} clusters...")
        
        # Utiliser PCA pour réduire la dimension si nécessaire
        use_pca = self.embeddings.shape[1] > 50
        embeddings_to_cluster = self.embeddings
        
        if use_pca:
            logger.info(f"Réduction PCA de {self.embeddings.shape[1]} à 50 dimensions")
            pca = PCA(n_components=50, random_state=42)
            embeddings_to_cluster = pca.fit_transform(self.embeddings)
            self.pca = pca
        
        # Clustering K-Means
        kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10,
            max_iter=300,
            verbose=0
        )
        
        cluster_labels = kmeans.fit_predict(embeddings_to_cluster)
        self.kmeans_model = kmeans
        self.cluster_labels = cluster_labels
        
        # Calculer les scores
        if len(np.unique(cluster_labels)) > 1:
            silhouette = silhouette_score(embeddings_to_cluster, cluster_labels)
            logger.info(f"Score silhouette: {silhouette:.4f}")
        
        # Calculer les tailles des clusters
        cluster_sizes = np.bincount(cluster_labels)
        for i, size in enumerate(cluster_sizes):
            logger.info(f"  Cluster {i}: {size} documents ({size/len(cluster_labels)*100:.1f}%)")
        
        return cluster_labels, kmeans
    
    def analyze_clusters(self, n_clusters: int = 8) -> List[Dict[str, Any]]:
        """
        Analyse les clusters et extrait les thèmes
        
        Args:
            n_clusters: Nombre de clusters
            
        Returns:
            Liste d'analyses de clusters
        """
        # Effectuer le clustering
        cluster_labels, _ = self.perform_clustering(n_clusters)
        
        # Analyser chaque cluster
        clusters_analysis = []
        
        for cluster_id in range(n_clusters):
            # Indices des documents dans ce cluster
            cluster_indices = np.where(cluster_labels == cluster_id)[0]
            
            if len(cluster_indices) == 0:
                continue
            
            # Extraire les catégories des documents
            categories = []
            titles = []
            
            for idx in cluster_indices[:100]:  # Limiter pour l'analyse
                if idx < len(self.metadata):
                    meta = self.metadata[idx]
                    
                    # Catégories
                    if 'categories' in meta:
                        if isinstance(meta['categories'], str):
                            categories.extend(meta['categories'].split())
                        elif isinstance(meta['categories'], list):
                            categories.extend(meta['categories'])
                    
                    # Titres
                    if 'title' in meta:
                        titles.append(meta['title'])
            
            # Trouver les catégories les plus communes
            from collections import Counter
            if categories:
                category_counter = Counter(categories)
                top_categories = category_counter.most_common(5)
            else:
                top_categories = []
            
            # Analyser les titres pour les mots-clés
            import re
            from collections import Counter as Counter2
            
            all_words = []
            for title in titles:
                words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
                all_words.extend(words)
            
            # Filtrer les mots communs
            common_words = {'the', 'and', 'for', 'with', 'using', 'based', 'from', 'this', 'that'}
            filtered_words = [w for w in all_words if w not in common_words]
            
            if filtered_words:
                word_counter = Counter2(filtered_words)
                top_keywords = word_counter.most_common(10)
            else:
                top_keywords = []
            
            # Calculer les statistiques
            cluster_stats = {
                'cluster_id': int(cluster_id),
                'size': len(cluster_indices),
                'percentage': len(cluster_indices) / len(cluster_labels) * 100,
                'top_categories': [{'category': cat, 'count': count} for cat, count in top_categories],
                'top_keywords': [{'keyword': word, 'count': count} for word, count in top_keywords],
                'sample_titles': titles[:5] if titles else []
            }
            
            clusters_analysis.append(cluster_stats)
        
        # Trier par taille décroissante
        clusters_analysis.sort(key=lambda x: x['size'], reverse=True)
        
        return clusters_analysis
    
    def visualize_clusters(self, n_clusters: int = 8, save_path: str = None):
        """
        Visualise les clusters en 2D
        
        Args:
            n_clusters: Nombre de clusters
            save_path: Chemin pour sauvegarder la visualisation
        """
        logger.info("Visualisation des clusters...")
        
        # Effectuer le clustering
        cluster_labels, _ = self.perform_clustering(n_clusters)
        
        # Réduire en 2D avec PCA
        pca_2d = PCA(n_components=2, random_state=42)
        embeddings_2d = pca_2d.fit_transform(self.embeddings)
        
        # Créer la visualisation
        plt.figure(figsize=(12, 8))
        
        # Scatter plot
        scatter = plt.scatter(
            embeddings_2d[:, 0], 
            embeddings_2d[:, 1],
            c=cluster_labels,
            cmap='tab20',
            alpha=0.6,
            s=10
        )
        
        # Ajouter les centres de clusters en 2D
        if hasattr(self, 'kmeans_model'):
            # Convertir les centres en 2D
            if hasattr(self, 'pca'):
                # Si on a utilisé PCA pour le clustering
                centers_original = self.kmeans_model.cluster_centers_
                # Il faudrait inverser la transformation PCA, mais c'est complexe
                # On utilise une approximation
                centers_2d = pca_2d.transform(centers_original.dot(self.pca.components_.T))
            else:
                centers_2d = pca_2d.transform(self.kmeans_model.cluster_centers_)
            
            plt.scatter(
                centers_2d[:, 0], 
                centers_2d[:, 1],
                c='red',
                marker='X',
                s=200,
                label='Centres de clusters'
            )
        
        plt.title(f'Clustering Thématique des Articles ({n_clusters} clusters)', fontsize=16)
        plt.xlabel('Composante PCA 1', fontsize=12)
        plt.ylabel('Composante PCA 2', fontsize=12)
        plt.colorbar(scatter, label='Cluster')
        plt.grid(alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Visualisation sauvegardée: {save_path}")
        
        plt.show()
    
    def save_clustering_results(self, output_file: str, n_clusters: int = 8):
        """
        Sauvegarde les résultats du clustering
        
        Args:
            output_file: Fichier de sortie
            n_clusters: Nombre de clusters
        """
        # Analyser les clusters
        clusters_analysis = self.analyze_clusters(n_clusters)
        
        # Sauvegarder
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(clusters_analysis, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Résultats du clustering sauvegardés: {output_file}")
        
        # Sauvegarder aussi les labels
        labels_file = output_file.replace('.json', '_labels.npy')
        np.save(labels_file, self.cluster_labels)
        
        return clusters_analysis

def cluster_embeddings(embeddings_file: str, output_file: str = None, 
                      n_clusters: int = 8, visualize: bool = True):
    """
    Fonction principale pour le clustering
    
    Args:
        embeddings_file: Fichier d'embeddings
        output_file: Fichier de sortie (optionnel)
        n_clusters: Nombre de clusters
        visualize: Afficher la visualisation
    """
    if output_file is None:
        output_file = embeddings_file.replace('.npy', f'_clusters_{n_clusters}.json')
    
    # Initialiser le clustering
    clusterer = TopicClustering(embeddings_file)
    
    # Trouver le nombre optimal de clusters
    logger.info("Recherche du nombre optimal de clusters...")
    optimal_scores = clusterer.find_optimal_clusters(max_clusters=15)
    
    if optimal_scores:
        best_n = max(optimal_scores, key=optimal_scores.get)
        logger.info(f"Nombre optimal de clusters: {best_n} (score: {optimal_scores[best_n]:.4f})")
    else:
        best_n = n_clusters
        logger.info(f"Utilisation de {n_clusters} clusters par défaut")
    
    # Effectuer le clustering avec le meilleur nombre
    clusters_analysis = clusterer.save_clustering_results(output_file, best_n)
    
    # Visualiser si demandé
    if visualize:
        viz_path = output_file.replace('.json', '.png')
        clusterer.visualize_clusters(best_n, viz_path)
    
    # Afficher le résumé
    logger.info("\n" + "="*50)
    logger.info("RÉSUMÉ DU CLUSTERING")
    logger.info("="*50)
    
    for cluster in clusters_analysis:
        logger.info(f"\nCluster {cluster['cluster_id']} ({cluster['size']} documents, {cluster['percentage']:.1f}%):")
        
        if cluster['top_categories']:
            top_cats = ", ".join([f"{cat['category']} ({cat['count']})" 
                                for cat in cluster['top_categories'][:3]])
            logger.info(f"  Catégories principales: {top_cats}")
        
        if cluster['top_keywords']:
            top_kws = ", ".join([f"{kw['keyword']} ({kw['count']})" 
                               for kw in cluster['top_keywords'][:5]])
            logger.info(f"  Mots-clés: {top_kws}")
    
    return clusters_analysis

if __name__ == "__main__":
    # Exemple d'utilisation
    embeddings_file = "data/embeddings/arxiv_embeddings.npy"
    
    if Path(embeddings_file).exists():
        # Clustering avec 8 clusters
        results = cluster_embeddings(
            embeddings_file, 
            n_clusters=8,
            visualize=True
        )
        
        print(f"\n{len(results)} clusters analysés")
    else:
        print(f"Fichier {embeddings_file} introuvable.")
