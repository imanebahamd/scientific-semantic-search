# ai/embeddings/sentence_bert_handler.py
import numpy as np
from typing import List
import logging

logger = logging.getLogger(__name__)

class SentenceBERTHandler:
    """Handler pour générer des embeddings avec Sentence-BERT"""
    
    def __init__(self, model_name="all-MiniLM-L6-v2", device="cpu"):
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"📦 Chargement du modèle {model_name}...")
            self.model = SentenceTransformer(model_name)
            self.model.to(device)
            logger.info("✅ Modèle chargé avec succès")
        except ImportError as e:
            logger.warning(f"⚠️ SentenceTransformers non disponible: {e}")
            logger.info("📝 Utilisation de embeddings factices pour le développement")
            self.model = None
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """Génère des embeddings pour une liste de textes"""
        if self.model is None:
            # Retourne des embeddings factices pour le développement
            n = len(texts)
            return np.random.randn(n, 384).astype(np.float32)
        
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"❌ Erreur génération embeddings: {e}")
            # Fallback vers embeddings factices
            n = len(texts)
            return np.random.randn(n, 384).astype(np.float32)
    
    def encode_single(self, text: str) -> np.ndarray:
        """Génère un embedding pour un seul texte"""
        return self.encode([text])[0]

# Version simplifiée sans dépendances lourdes
class DummyEmbeddingModel:
    """Modèle factice pour le développement quand sentence-transformers n'est pas disponible"""
    
    def __init__(self, dim=384):
        self.dim = dim
    
    def encode(self, texts):
        n = len(texts)
        # Génère des embeddings aléatoires mais cohérents (basés sur le hash du texte)
        embeddings = np.zeros((n, self.dim), dtype=np.float32)
        for i, text in enumerate(texts):
            # Hash simple pour avoir des embeddings déterministes
            import hashlib
            hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16) % 10000
            np.random.seed(hash_val)
            embeddings[i] = np.random.randn(self.dim)
        return embeddings

# Alternative : utiliser directement
def get_embedding_model(use_dummy=False):
    """Retourne un modèle d'embedding (réel ou factice)"""
    if use_dummy:
        logger.info("🎭 Utilisation du modèle factice d'embeddings")
        return DummyEmbeddingModel()
    else:
        try:
            return SentenceBERTHandler()
        except:
            logger.warning("⚠️ Retour au modèle factice")
            return DummyEmbeddingModel()
