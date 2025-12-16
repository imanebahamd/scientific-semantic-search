import numpy as np
import json
from typing import List, Dict, Any, Optional, Tuple
import logging
from pathlib import Path

from ai.embeddings.sentence_bert_handler import SentenceBERTHandler
from ai.semantic_search.similarity_calculator import SimilarityCalculator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SemanticSearchEngine:
    """Moteur de recherche sémantique local"""
    
    def __init__(self, embeddings_file: str, metadata_file: str = None):
        """
        Initialise le moteur de recherche
        
        Args:
            embeddings_file: Fichier .npy contenant les embeddings
            metadata_file: Fichier JSON contenant les métadonnées
        """
        self.embeddings_file = embeddings_file
        self.metadata_file = metadata_file or embeddings_file.replace('.npy', '.json')
        
        # Charger le modèle Sentence-BERT
        self.model = SentenceBERTHandler()
        
        # Charger les embeddings et métadonnées
        self.load_data()
        
        logger.info(f"Moteur de recherche initialisé avec {len(self.embeddings)} documents")
    
    def load_data(self):
        """Charge les embeddings et métadonnées"""
        try:
            # Charger les embeddings
            self.embeddings = np.load(self.embeddings_file)
            logger.info(f"Embeddings chargés: {self.embeddings.shape}")
            
            # Charger les métadonnées
            if Path(self.metadata_file).exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                logger.info(f"Métadonnées chargées: {len(self.metadata)} articles")
            else:
                logger.warning(f"Fichier de métadonnées {self.metadata_file} introuvable")
                self.metadata = []
                
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données: {e}")
            raise
    
    def encode_query(self, query: str) -> np.ndarray:
        """
        Encode une requête textuelle en embedding
        
        Args:
            query: Requête textuelle
            
        Returns:
            Embedding de la requête
        """
        return self.model.encode([query])[0]
    
    def search(self, query: str, k: int = 5, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Recherche sémantique
        
        Args:
            query: Requête textuelle
            k: Nombre de résultats à retourner
            threshold: Seuil de similarité minimum (cosinus)
            
        Returns:
            Liste de résultats
        """
        logger.info(f"Recherche: '{query}' (k={k}, threshold={threshold})")
        
        try:
            # 1. Encoder la requête
            query_embedding = self.encode_query(query)
            
            # 2. Trouver les K documents les plus similaires
            indices, scores = SimilarityCalculator.find_top_k_similar(
                query_embedding, self.embeddings, k
            )
            
            # 3. Filtrer par seuil
            results = []
            for idx, score in zip(indices, scores):
                if score >= threshold:
                    result = self._create_result(idx, score, query)
                    if result:
                        results.append(result)
            
            # 4. Trier par score décroissant
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # 5. Si aucun résultat au-dessus du seuil
            if not results:
                logger.info(f"Aucun résultat pertinent (meilleur score: {scores[0]:.3f})")
                return [{
                    'query': query,
                    'message': f"Aucun résultat pertinent trouvé (seuil: {threshold})",
                    'best_score': float(scores[0]) if len(scores) > 0 else 0.0
                }]
            
            logger.info(f"{len(results)} résultats trouvés (meilleur score: {results[0]['similarity_score']:.3f})")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {e}")
            return [{
                'query': query,
                'error': str(e)
            }]
    
    def _create_result(self, idx: int, score: float, query: str) -> Optional[Dict[str, Any]]:
        """
        Crée un résultat de recherche
        
        Args:
            idx: Index du document
            score: Score de similarité
            query: Requête originale
            
        Returns:
            Dictionnaire de résultat
        """
        try:
            result = {
                'query': query,
                'document_index': int(idx),
                'similarity_score': float(score),
                'similarity_percentage': SimilarityCalculator.convert_to_percentage(score),
                'match_quality': self._get_match_quality(score)
            }
            
            # Ajouter les métadonnées si disponibles
            if self.metadata and idx < len(self.metadata):
                meta = self.metadata[idx]
                result.update({
                    'id': meta.get('id', f'doc_{idx}'),
                    'title': meta.get('title', ''),
                    'authors': meta.get('authors', ''),
                    'categories': meta.get('categories', ''),
                    'date': meta.get('date', '')
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du résultat {idx}: {e}")
            return None
    
    def _get_match_quality(self, score: float) -> str:
        """
        Retourne une description qualitative de la similarité
        
        Args:
            score: Score de similarité cosinus
            
        Returns:
            Description qualitative
        """
        if score >= 0.8:
            return "Excellente correspondance"
        elif score >= 0.6:
            return "Bonne correspondance"
        elif score >= 0.4:
            return "Correspondance modérée"
        elif score >= 0.2:
            return "Faible correspondance"
        else:
            return "Très faible correspondance"
    
    def search_by_embedding(self, query_embedding: np.ndarray, 
                           k: int = 5, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Recherche directement par embedding
        
        Args:
            query_embedding: Embedding de la requête
            k: Nombre de résultats
            threshold: Seuil de similarité
            
        Returns:
            Liste de résultats
        """
        try:
            indices, scores = SimilarityCalculator.find_top_k_similar(
                query_embedding, self.embeddings, k
            )
            
            results = []
            for idx, score in zip(indices, scores):
                if score >= threshold:
                    result = self._create_result(idx, score, "Embedding query")
                    if result:
                        results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur dans search_by_embedding: {e}")
            return []
    
    def get_document_by_index(self, idx: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un document par son index
        
        Args:
            idx: Index du document
            
        Returns:
            Document ou None
        """
        if idx < 0 or idx >= len(self.embeddings):
            return None
        
        if self.metadata and idx < len(self.metadata):
            return self.metadata[idx]
        
        return {
            'index': idx,
            'embedding_shape': self.embeddings[idx].shape
        }

if __name__ == "__main__":
    # Test du moteur de recherche
    # Note: Les fichiers de test doivent être générés d'abord
    
    embeddings_file = "data/embeddings/arxiv_embeddings.npy"
    metadata_file = "data/embeddings/arxiv_embeddings.json"
    
    if Path(embeddings_file).exists():
        engine = SemanticSearchEngine(embeddings_file, metadata_file)
        
        # Test de recherche
        test_queries = [
            "machine learning",
            "deep neural networks",
            "computer vision applications",
            "natural language processing"
        ]
        
        for query in test_queries:
            print(f"\nRecherche: '{query}'")
            results = engine.search(query, k=3, threshold=0.3)
            
            for i, result in enumerate(results):
                if 'message' in result:
                    print(f"  {result['message']}")
                else:
                    print(f"  Résultat {i+1}:")
                    print(f"    Titre: {result.get('title', 'N/A')[:50]}...")
                    print(f"    Score: {result['similarity_score']:.3f} ({result['similarity_percentage']:.1f}%)")
                    print(f"    Qualité: {result['match_quality']}")
    else:
        print(f"Fichier {embeddings_file} introuvable. Veuillez d'abord générer les embeddings.")
