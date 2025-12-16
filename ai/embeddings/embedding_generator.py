import json
import numpy as np
import pandas as pd
from tqdm import tqdm
import logging
from pathlib import Path
from typing import List, Dict, Any
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from ai.embeddings.sentence_bert_handler import SentenceBERTHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Générateur d'embeddings pour les articles scientifiques"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceBERTHandler(model_name)
        self.embedding_dim = self.model.embedding_dim
    
    def load_arxiv_data(self, input_file: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Charge les données arXiv depuis un fichier JSON
        
        Args:
            input_file: Chemin vers le fichier JSON
            limit: Limite le nombre d'articles (pour les tests)
            
        Returns:
            Liste d'articles
        """
        logger.info(f"Chargement des données depuis {input_file}")
        
        articles = []
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                for i, line in enumerate(tqdm(f, desc="Chargement des articles")):
                    if limit and i >= limit:
                        break
                    
                    try:
                        article = json.loads(line.strip())
                        articles.append(article)
                    except json.JSONDecodeError:
                        continue
            
            logger.info(f"{len(articles)} articles chargés")
            return articles
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement: {e}")
            raise
    
    def preprocess_text(self, title: str, abstract: str) -> str:
        """
        Prétraite le texte pour l'embedding
        
        Args:
            title: Titre de l'article
            abstract: Résumé de l'article
            
        Returns:
            Texte prétraité
        """
        # Nettoyer le texte
        title = title.strip() if title else ""
        abstract = abstract.strip() if abstract else ""
        
        # Combiner titre et abstract
        combined = f"{title}. {abstract}"
        
        # Limiter la longueur (modèle a une limite de tokens)
        max_length = 500
        if len(combined) > max_length:
            combined = combined[:max_length] + "..."
        
        return combined
    
    def generate_embeddings(self, articles: List[Dict[str, Any]], 
                           batch_size: int = 32) -> np.ndarray:
        """
        Génère les embeddings pour une liste d'articles
        
        Args:
            articles: Liste d'articles
            batch_size: Taille du batch
            
        Returns:
            Array d'embeddings
        """
        logger.info(f"Génération des embeddings pour {len(articles)} articles")
        
        # Extraire et prétraiter les textes
        texts = []
        valid_indices = []
        
        for idx, article in enumerate(tqdm(articles, desc="Prétraitement")):
            title = article.get('title', '')
            abstract = article.get('abstract', '')
            
            if title and abstract:
                text = self.preprocess_text(title, abstract)
                texts.append(text)
                valid_indices.append(idx)
        
        logger.info(f"{len(texts)} textes valides pour l'embedding")
        
        if not texts:
            logger.warning("Aucun texte valide trouvé")
            return np.array([])
        
        # Générer les embeddings par batch
        embeddings = self.model.encode_batch(texts, batch_size=batch_size)
        embeddings_array = np.array(embeddings)
        
        logger.info(f"Embeddings générés: shape {embeddings_array.shape}")
        return embeddings_array, valid_indices
    
    def save_embeddings(self, embeddings: np.ndarray, output_file: str):
        """
        Sauvegarde les embeddings dans un fichier
        
        Args:
            embeddings: Array d'embeddings
            output_file: Chemin du fichier de sortie
        """
        logger.info(f"Sauvegarde des embeddings dans {output_file}")
        
        # Créer le dossier parent si nécessaire
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder en format numpy
        np.save(output_file, embeddings)
        logger.info(f"Embeddings sauvegardés: {embeddings.shape}")
    
    def generate_and_save(self, input_file: str, output_file: str, 
                         limit: int = None, batch_size: int = 32):
        """
        Pipeline complet: charge, génère et sauvegarde les embeddings
        
        Args:
            input_file: Fichier d'entrée JSON
            output_file: Fichier de sortie .npy
            limit: Limite d'articles
            batch_size: Taille du batch
        """
        # 1. Charger les données
        articles = self.load_arxiv_data(input_file, limit)
        
        if not articles:
            logger.warning("Aucun article chargé")
            return
        
        # 2. Générer les embeddings
        embeddings, valid_indices = self.generate_embeddings(articles, batch_size)
        
        if embeddings.size == 0:
            logger.warning("Aucun embedding généré")
            return
        
        # 3. Sauvegarder les embeddings
        self.save_embeddings(embeddings, output_file)
        
        # 4. Sauvegarder les métadonnées
        self.save_metadata(articles, valid_indices, output_file)
        
        logger.info("Pipeline d'embedding terminé avec succès")
    
    def save_metadata(self, articles: List[Dict[str, Any]], 
                     valid_indices: List[int], output_file: str):
        """
        Sauvegarde les métadonnées des articles
        
        Args:
            articles: Liste complète d'articles
            valid_indices: Indices des articles valides
            output_file: Chemin de base pour les fichiers
        """
        metadata_file = str(Path(output_file).with_suffix('.json'))
        
        metadata = []
        for idx in valid_indices:
            article = articles[idx]
            metadata.append({
                'id': article.get('id', ''),
                'title': article.get('title', ''),
                'authors': article.get('authors', ''),
                'categories': article.get('categories', ''),
                'date': article.get('update_date', '')
            })
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Métadonnées sauvegardées: {metadata_file}")

def generate_article_embeddings(input_file: str, output_file: str, 
                               limit: int = 1000, batch_size: int = 32):
    """
    Fonction principale pour générer les embeddings
    
    Args:
        input_file: Fichier d'entrée JSON
        output_file: Fichier de sortie .npy
        limit: Limite d'articles (optionnel)
        batch_size: Taille du batch
    """
    generator = EmbeddingGenerator()
    generator.generate_and_save(input_file, output_file, limit, batch_size)

if __name__ == "__main__":
    # Exemple d'utilisation
    input_file = "data/arxiv-metadata.json"
    output_file = "data/embeddings/arxiv_embeddings.npy"
    
    # Pour les tests, limiter à 1000 articles
    generate_article_embeddings(input_file, output_file, limit=1000)
    
    # Vérifier les embeddings générés
    embeddings = np.load(output_file)
    print(f"Embeddings shape: {embeddings.shape}")
    print(f"Embeddings dtype: {embeddings.dtype}")
    print(f"Exemple d'embedding (premier élément): {embeddings[0][:10]}...")
