#!/usr/bin/env python3
"""
Script d'importation spécifique pour les données arXiv téléchargées.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import numpy as np
from tqdm import tqdm
import argparse
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ajouter le chemin parent pour importer les modules
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.append(str(PROJECT_ROOT))

# Remplacer l'import de es_config par la version fixée
try:
    from backend.elasticsearch.es_config_fixed import es_config_fixed as es_config
    logger.info("✅ Utilisation de es_config_fixed")
except ImportError:
    from backend.elasticsearch.es_config import es_config
    logger.info("✅ Utilisation de es_config standard")
from ai.embeddings.sentence_bert_handler import SentenceBERTHandler

class ArXivDataImporter:
    """Importateur corrigé avec gestion des dates"""
    
    def __init__(self, data_path=None):
        if data_path is None:
            data_path = PROJECT_ROOT / "data" / "cleaned" / "enhanced_cs.json"
        
        self.data_path = Path(data_path)
        self.es = es_config.get_client()
        self.index_name = es_config.index_name
        self.embedding_model = SentenceBERTHandler()
        self.batch_size = 10
    
    def format_date(self, date_str):
        """Formate une date pour Elasticsearch"""
        if not date_str:
            return "2023-01-01"
        
        try:
            # Si c'est une date ISO (avec T)
            if "T" in date_str:
                # Pour Elasticsearch 7, utiliser format simple
                dt = dateutil.parser.parse(date_str)
                return dt.strftime("%Y-%m-%d")
            
            # Sinon essayer de parser
            try:
                dt = dateutil.parser.parse(date_str)
                return dt.strftime("%Y-%m-%d")
            except:
                # Format simple YYYY-MM-DD
                return date_str[:10] if len(date_str) >= 10 else "2023-01-01"
        except:
            return "2023-01-01"
    
    def create_index(self):
        """Crée l'index avec mapping simplifié"""
        if self.es.indices.exists(index=self.index_name):
            logger.info(f"Index {self.index_name} existe déjà.")
            return True
        
        # Mapping simplifié sans problèmes de date
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "title": {"type": "text"},
                    "abstract": {"type": "text"},
                    "authors": {"type": "keyword"},
                    "categories": {"type": "keyword"},
                    "primary_category": {"type": "keyword"},
                    "date": {"type": "date", "format": "yyyy-MM-dd"},  # Format simple
                    "year": {"type": "integer"},
                    "month": {"type": "integer"},
                    "source": {"type": "keyword"},
                    "title_embedding": {
                        "type": "dense_vector",
                        "dims": 384,
                        "index": True,
                        "similarity": "cosine"
                    },
                    "abstract_embedding": {
                        "type": "dense_vector",
                        "dims": 384,
                        "index": True,
                        "similarity": "cosine"
                    },
                    "combined_embedding": {
                        "type": "dense_vector",
                        "dims": 384,
                        "index": True,
                        "similarity": "cosine"
                    }
                }
            }
        }
        
        try:
            self.es.indices.create(index=self.index_name, body=mapping)
            logger.info(f"✅ Index {self.index_name} créé")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur création index: {e}")
            return False
    
    def load_data(self, limit=None):
        """Charge les données"""
        logger.info(f"📖 Chargement depuis {self.data_path}")
        
        if not self.data_path.exists():
            logger.error(f"❌ Fichier introuvable")
            return []
        
        with open(self.data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if limit:
            data = data[:limit]
        
        logger.info(f"✅ {len(data)} articles chargés")
        return data
    
    def process_and_import(self, limit=None):
        """Traite et importe les données"""
        # Charger
        articles = self.load_data(limit)
        if not articles:
            return False
        
        # Traiter
        logger.info("🔧 Traitement des articles...")
        imported_count = 0
        
        for i, article in enumerate(tqdm(articles, desc="Importation")):
            try:
                # Créer le document
                doc = {
                    "id": article.get("arxiv_id", f"doc_{i}"),
                    "title": article.get("title", ""),
                    "abstract": article.get("abstract", ""),
                    "authors": article.get("authors", []),
                    "categories": article.get("categories", []),
                    "primary_category": article.get("main_category", ""),
                    "date": self.format_date(article.get("published", "")),
                    "year": article.get("publication_year", 2023),
                    "month": article.get("publication_month", 1),
                    "source": "arXiv"
                }
                
                # Nettoyer les listes
                if isinstance(doc["authors"], str):
                    doc["authors"] = [doc["authors"]]
                
                # Générer les embeddings
                text = f"{doc['title']} {doc['abstract']}"
                embedding = self.embedding_model.encode([text])[0].tolist()
                doc["combined_embedding"] = embedding
                
                # Indexer
                self.es.index(
                    index=self.index_name,
                    id=doc["id"],
                    body=doc,
                    refresh=True
                )
                
                imported_count += 1
                
                # Log progress
                if (i + 1) % 10 == 0:
                    logger.info(f"  {i + 1} articles traités")
                    
            except Exception as e:
                logger.warning(f"⚠ Erreur article {i}: {e}")
                continue
        
        logger.info(f"✅ {imported_count}/{len(articles)} articles importés")
        return imported_count > 0
    
    def verify_import(self):
        """Vérifie l'importation"""
        try:
            count = self.es.count(index=self.index_name)
            logger.info(f"📊 Documents dans l'index: {count['count']}")
            
            # Afficher un exemple
            result = self.es.search(
                index=self.index_name,
                body={"query": {"match_all": {}}, "size": 1}
            )
            
            if result["hits"]["hits"]:
                doc = result["hits"]["hits"][0]["_source"]
                logger.info(f"📋 Exemple importé: {doc.get('title', '')[:50]}...")
            
            return True
        except Exception as e:
            logger.error(f"❌ Erreur vérification: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Importateur corrigé')
    parser.add_argument('--limit', type=int, default=5, help='Nombre d\'articles')
    parser.add_argument('--delete', action='store_true', help='Supprimer index existant')
    
    args = parser.parse_args()
    
    logger.info("🚀 IMPORTATEUR CORRIGÉ")
    logger.info("=" * 50)
    
    # Créer l'importateur
    importer = ArXivDataImporter()
    
    # Vérifier la connexion
    if not importer.es:
        logger.error("❌ Impossible de se connecter à Elasticsearch")
        return
    
    # Supprimer l'index si demandé
    if args.delete and importer.es.indices.exists(index=importer.index_name):
        importer.es.indices.delete(index=importer.index_name)
        logger.info(f"🗑️ Index {importer.index_name} supprimé")
    
    # Créer l'index
    if not importer.create_index():
        logger.error("❌ Erreur création index")
        return
    
    # Importer
    if importer.process_and_import(args.limit):
        logger.info("✅ Importation réussie")
        importer.verify_import()
    else:
        logger.error("❌ Importation échouée")

if __name__ == "__main__":
    main()
