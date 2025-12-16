import numpy as np
from typing import List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimilarityCalculator:
    """Calcule les similarités entre embeddings"""
    
    @staticmethod
    def calculate_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calcule la similarité cosinus entre deux vecteurs
        
        Args:
            vec1: Premier vecteur
            vec2: Deuxième vecteur
            
        Returns:
            Score de similarité cosinus (entre -1 et 1)
        """
        try:
            # Normaliser les vecteurs
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = np.dot(vec1, vec2) / (norm1 * norm2)
            
            # S'assurer que la similarité est dans [-1, 1]
            similarity = max(-1.0, min(1.0, similarity))
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Erreur dans calculate_cosine_similarity: {e}")
            return 0.0
    
    @staticmethod
    def calculate_batch_similarity(query_embedding: np.ndarray, 
                                  doc_embeddings: np.ndarray) -> np.ndarray:
        """
        Calcule la similarité entre un embedding de requête et plusieurs embeddings
        
        Args:
            query_embedding: Embedding de la requête
            doc_embeddings: Embeddings des documents (shape: n_docs x dim)
            
        Returns:
            Array de scores de similarité
        """
        try:
            # Normaliser les vecteurs
            query_norm = np.linalg.norm(query_embedding)
            doc_norms = np.linalg.norm(doc_embeddings, axis=1)
            
            # Éviter la division par zéro
            valid_docs = doc_norms > 0
            
            if not query_norm or not valid_docs.any():
                return np.zeros(len(doc_embeddings))
            
            # Calculer les produits scalaires
            dot_products = np.dot(doc_embeddings[valid_docs], query_embedding)
            
            # Calculer les similarités
            similarities = np.zeros(len(doc_embeddings))
            similarities[valid_docs] = dot_products / (doc_norms[valid_docs] * query_norm)
            
            # Clipper les valeurs
            similarities = np.clip(similarities, -1.0, 1.0)
            
            return similarities
            
        except Exception as e:
            logger.error(f"Erreur dans calculate_batch_similarity: {e}")
            return np.zeros(len(doc_embeddings))
    
    @staticmethod
    def find_top_k_similar(query_embedding: np.ndarray, 
                          doc_embeddings: np.ndarray, 
                          k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """
        Trouve les K documents les plus similaires
        
        Args:
            query_embedding: Embedding de la requête
            doc_embeddings: Embeddings des documents
            k: Nombre de résultats à retourner
            
        Returns:
            Tuple (indices, scores)
        """
        try:
            # Calculer toutes les similarités
            similarities = SimilarityCalculator.calculate_batch_similarity(
                query_embedding, doc_embeddings
            )
            
            # Trouver les K plus grands
            if len(similarities) <= k:
                indices = np.argsort(similarities)[::-1]
                scores = similarities[indices]
            else:
                # Utiliser argpartition pour plus d'efficacité
                indices = np.argpartition(-similarities, k)[:k]
                # Trier les K meilleurs
                top_indices = indices[np.argsort(-similarities[indices])]
                top_scores = similarities[top_indices]
                
                indices = top_indices
                scores = top_scores
            
            return indices, scores
            
        except Exception as e:
            logger.error(f"Erreur dans find_top_k_similar: {e}")
            return np.array([]), np.array([])
    
    @staticmethod
    def convert_to_percentage(cosine_score: float) -> float:
        """
        Convertit un score de similarité cosinus en pourcentage
        
        Args:
            cosine_score: Score de similarité cosinus (-1 à 1)
            
        Returns:
            Pourcentage de similarité (0 à 100)
        """
        # La similarité cosinus varie de -1 à 1
        # Nous normalisons entre 0 et 1 puis multiplions par 100
        normalized = (cosine_score + 1) / 2  # Convertir de [-1, 1] à [0, 1]
        percentage = normalized * 100
        
        return min(100.0, max(0.0, percentage))

# Fonctions d'interface pour compatibilité
def calculate_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    return SimilarityCalculator.calculate_cosine_similarity(vec1, vec2)

def calculate_similarity(query_embedding: np.ndarray, docs_embeddings: np.ndarray) -> List[float]:
    similarities = SimilarityCalculator.calculate_batch_similarity(query_embedding, docs_embeddings)
    return similarities.tolist()

if __name__ == "__main__":
    # Tests unitaires
    calculator = SimilarityCalculator()
    
    # Test 1: Vecteurs identiques
    vec1 = np.array([1, 2, 3], dtype=float)
    vec2 = np.array([1, 2, 3], dtype=float)
    sim = calculator.calculate_cosine_similarity(vec1, vec2)
    print(f"Test 1 - Vecteurs identiques: {sim:.4f} (attendu: 1.0)")
    
    # Test 2: Vecteurs orthogonaux
    vec3 = np.array([1, 0, 0], dtype=float)
    vec4 = np.array([0, 1, 0], dtype=float)
    sim = calculator.calculate_cosine_similarity(vec3, vec4)
    print(f"Test 2 - Vecteurs orthogonaux: {sim:.4f} (attendu: 0.0)")
    
    # Test 3: Batch similarity
    query = np.array([1, 0, 0], dtype=float)
    docs = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
    similarities = calculator.calculate_batch_similarity(query, docs)
    print(f"Test 3 - Batch similarity: {similarities}")
    
    # Test 4: Top K
    indices, scores = calculator.find_top_k_similar(query, docs, k=2)
    print(f"Test 4 - Top 2: indices={indices}, scores={scores}")
    
    # Test 5: Conversion en pourcentage
    for score in [-1, -0.5, 0, 0.5, 1]:
        percentage = calculator.convert_to_percentage(score)
        print(f"Score {score:.1f} → {percentage:.1f}%")
