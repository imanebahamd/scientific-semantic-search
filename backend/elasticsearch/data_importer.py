import json
import pandas as pd
import numpy as np
from datetime import datetime
from tqdm import tqdm
import sys
import os

# Ajouter le chemin parent pour importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.elasticsearch.es_config import es_config
from ai.embeddings.sentence_bert_handler import SentenceBERTHandler

class DataImporter:
    """Classe pour importer les données arXiv dans Elasticsearch"""
    
    def __init__(self, data_path='data/arxiv-metadata.json'):
        self.data_path = data_path
        self.es = es_config.get_client()
        self.index_name = es_config.index_name
        self.embedding_model = SentenceBERTHandler()
        self.batch_size = 100  # Nombre de documents par batch
        
    def check_index_exists(self):
        """Vérifie si l'index existe déjà"""
        return self.es.indices.exists(index=self.index_name)
    
    def create_index(self):
        """Crée l'index avec le mapping approprié"""
        if self.check_index_exists():
            print(f"L'index {self.index_name} existe déjà.")
            return False
        
        # Charger le mapping depuis le fichier JSON
        with open('backend/elasticsearch/index_mapping.json', 'r') as f:
            mapping = json.load(f)
        
        # Créer l'index avec les settings et mappings
        self.es.indices.create(
            index=self.index_name,
            body=mapping
        )
        print(f"Index {self.index_name} créé avec succès.")
        return True
    
    def delete_index(self):
        """Supprime l'index (pour le développement)"""
        if self.check_index_exists():
            self.es.indices.delete(index=self.index_name)
            print(f"Index {self.index_name} supprimé.")
            return True
        return False
    
    def filter_computer_science(self, categories):
        """Filtre les catégories pour ne garder que l'informatique"""
        if isinstance(categories, str):
            return any(cat.startswith('cs.') for cat in categories.split())
        return False
    
    def generate_embeddings(self, text):
        """Génère les embeddings pour un texte"""
        if not text or pd.isna(text):
            return np.zeros(384).tolist()
        return self.embedding_model.encode([text])[0].tolist()
    
    def process_chunk(self, chunk):
        """Traite un chunk de données"""
        processed_docs = []
        
        for _, row in chunk.iterrows():
            # Filtrer les articles d'informatique
            if not self.filter_computer_science(row.get('categories', '')):
                continue
            
            # Préparer le document
            doc = {
                'id': str(row.get('id', '')),
                'title': row.get('title', ''),
                'abstract': row.get('abstract', ''),
                'authors': row.get('authors', '').split('; ') if '; ' in row.get('authors', '') else [row.get('authors', '')],
                'categories': row.get('categories', '').split(),
                'primary_category': row.get('categories', '').split()[0] if row.get('categories', '') else '',
                'doi': row.get('doi', ''),
                'journal_ref': row.get('journal-ref', ''),
                'year': int(row.get('update_date', '')[:4]) if row.get('update_date') else 2023,
                'month': int(row.get('update_date', '')[5:7]) if row.get('update_date') else 1
            }
            
            # Gérer les dates
            try:
                doc['date'] = datetime.strptime(row.get('versions', [{}])[0].get('created', ''), '%a, %d %b %Y %H:%M:%S %Z').strftime('%Y-%m-%d')
                doc['update_date'] = datetime.strptime(row.get('update_date', ''), '%Y-%m-%d').strftime('%Y-%m-%d')
            except:
                doc['date'] = '2023-01-01'
                doc['update_date'] = '2023-01-01'
            
            # Générer les embeddings
            title_text = str(doc['title'])
            abstract_text = str(doc['abstract'])
            combined_text = f"{title_text}. {abstract_text}"
            
            doc['title_embedding'] = self.generate_embeddings(title_text)
            doc['abstract_embedding'] = self.generate_embeddings(abstract_text)
            doc['combined_embedding'] = self.generate_embeddings(combined_text)
            
            processed_docs.append(doc)
        
        return processed_docs
    
    def import_data(self, limit=None):
        """Importe les données depuis le fichier JSON"""
        
        # Vérifier que le fichier existe
        if not os.path.exists(self.data_path):
            print(f"Fichier {self.data_path} introuvable.")
            return
        
        print(f"Début de l'importation depuis {self.data_path}")
        
        # Lire le fichier JSON par chunks
        chunk_size = 1000
        total_docs = 0
        
        with pd.read_json(self.data_path, lines=True, chunksize=chunk_size) as reader:
            for chunk_num, chunk in enumerate(reader):
                print(f"Traitement du chunk {chunk_num + 1}...")
                
                # Traiter le chunk
                processed_docs = self.process_chunk(chunk)
                
                # Indexer les documents
                if processed_docs:
                    self.bulk_index(processed_docs)
                    total_docs += len(processed_docs)
                    print(f"  → {len(processed_docs)} documents indexés")
                
                # Limiter pour les tests
                if limit and total_docs >= limit:
                    print(f"Limite de {limit} documents atteinte.")
                    break
        
        print(f"Importation terminée. {total_docs} documents indexés.")
    
    def bulk_index(self, docs):
        """Indexe un batch de documents"""
        actions = []
        
        for doc in docs:
            action = {
                "_index": self.index_name,
                "_id": doc['id'],
                "_source": doc
            }
            actions.append(action)
        
        # Utiliser l'API bulk pour l'efficacité
        from elasticsearch.helpers import bulk
        success, failed = bulk(self.es, actions, stats_only=True)
        
        if failed:
            print(f"  Erreur lors de l'indexation de {failed} documents")
    
    def test_connection(self):
        """Teste la connexion à Elasticsearch"""
        try:
            info = self.es.info()
            print(f"Connecté à Elasticsearch {info['version']['number']}")
            return True
        except Exception as e:
            print(f"Erreur de connexion: {e}")
            return False

if __name__ == "__main__":
    importer = DataImporter()
    
    # Tester la connexion
    if not importer.test_connection():
        exit(1)
    
    # Créer l'index
    importer.create_index()
    
    # Importer les données (limité à 1000 pour les tests)
    importer.import_data(limit=1000)
    
    # Afficher les statistiques
    stats = importer.es.count(index=importer.index_name)
    print(f"\nTotal documents dans l'index: {stats['count']}")
