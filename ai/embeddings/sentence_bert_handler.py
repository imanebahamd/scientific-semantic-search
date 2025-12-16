import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from typing import List, Union
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentenceBERTHandler:
    """Handler pour le modèle Sentence-BERT"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: str = None):
        """
        Initialise le modèle Sentence-BERT
        
        Args:
            model_name: Nom du modèle à charger
            device: Device à utiliser ('cuda' ou 'cpu')
        """
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
            
        self.model_name = model_name
        logger.info(f"Chargement du modèle {model_name} sur {self.device}")
        
        try:
            self.model = SentenceTransformer(model_name, device=self.device)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Modèle chargé. Dimension d'embedding: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {e}")
            raise
    
    def encode(self, texts: Union[str, List[str]], 
               batch_size: int = 32,
               convert_to_numpy: bool = True,
               normalize_embeddings: bool = True) -> np.ndarray:
        """
        Encode du texte en embeddings
        
        Args:
            texts: Texte ou liste de textes à encoder
            batch_size: Taille du batch pour l'encodage
            convert_to_numpy: Convertir en numpy array
            normalize_embeddings: Normaliser les embeddings
            
        Returns:
            Array d'embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
        
        logger.debug(f"Encodage de {len(texts)} texte(s)")
        
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=len(texts) > 100,
                convert_to_numpy=convert_to_numpy,
                normalize_embeddings=normalize_embeddings
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Erreur lors de l'encodage: {e}")
            raise
    
    def encode_batch(self, texts: List[str], batch_size: int = 64) -> List[np.ndarray]:
        """
        Encode une grande liste de textes par batch
        
        Args:
            texts: Liste de textes
            batch_size: Taille du batch
            
        Returns:
            Liste d'embeddings
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.debug(f"Traitement du batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
            
            batch_embeddings = self.encode(batch, batch_size=min(batch_size, len(batch)))
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    def get_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calcule la similarité cosinus entre deux embeddings
        
        Args:
            embedding1: Premier embedding
            embedding2: Deuxième embedding
            
        Returns:
            Score de similarité cosinus
        """
        from ai.semantic_search.similarity_calculator import calculate_cosine_similarity
        return calculate_cosine_similarity(embedding1, embedding2)
    
    def get_model_info(self) -> dict:
        """Retourne des informations sur le modèle"""
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dim,
            "device": self.device,
            "max_seq_length": self.model.max_seq_length
        }

# Instance globale pour éviter de recharger le modèle
_global_model = None

def get_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceBERTHandler:
    """Factory pour obtenir une instance du modèle (singleton pattern)"""
    global _global_model
    
    if _global_model is None:
        _global_model = SentenceBERTHandler(model_name)
    
    return _global_model

if __name__ == "__main__":
    # Test du modèle
    model = SentenceBERTHandler()
    
    # Test avec un texte simple
    test_texts = [
        "Machine learning for computer vision",
        "Deep learning in image processing",
        "Neural networks for visual recognition"
    ]
    
    embeddings = model.encode(test_texts)
    print(f"Shape des embeddings: {embeddings.shape}")
    print(f"Dimension: {embeddings.shape[1]}")
    
    # Test de similarité
    sim = model.get_similarity(embeddings[0], embeddings[1])
    print(f"Similarité entre texte 1 et 2: {sim:.4f}")
