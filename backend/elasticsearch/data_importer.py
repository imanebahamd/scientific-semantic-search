#!/usr/bin/env python3
"""
Importateur optimisé pour 5000+ documents sans embeddings
Version rapide pour développement
"""

import json
import requests
import time
import hashlib
import sys
from pathlib import Path
from tqdm import tqdm
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataImporter:
    """Importateur optimisé pour datasets de développement (5000+ docs)"""
    
    def __init__(self):
        self.es_url = "http://localhost:9200"
        self.index_name = "arxiv_papers"
        self.batch_size = 500
        self.max_docs = 5000
        
        # Vérifier la connexion Elasticsearch
        self.check_elasticsearch()
    
    def check_elasticsearch(self):
        """Vérifie la connexion à Elasticsearch"""
        try:
            response = requests.get(self.es_url, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ Connecté à Elasticsearch: {self.es_url}")
                return True
            else:
                logger.error(f"❌ Elasticsearch non disponible: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur connexion Elasticsearch: {e}")
            return False
    
    def find_data_files(self):
        """Trouve tous les fichiers de données disponibles"""
        logger.info("🔍 Recherche des fichiers de données...")
        
        # Chemins possibles
        possible_paths = [
            Path("../../data"),  # Par rapport à backend/elasticsearch
            Path("../../../data"),  # Par rapport à la racine du projet
            Path("data")  # Local
        ]
        
        data_dir = None
        for path in possible_paths:
            if path.exists() and path.is_dir():
                data_dir = path
                break
        
        if not data_dir:
            logger.error("❌ Aucun dossier data trouvé")
            return []
        
        # Fichiers JSON à rechercher
        json_patterns = ["*.json", "cleaned/*.json"]
        data_files = []
        
        for pattern in json_patterns:
            for filepath in data_dir.glob(pattern):
                if filepath.is_file() and filepath.stat().st_size > 0:
                    data_files.append(filepath)
        
        # Trier par taille (les plus gros d'abord)
        data_files.sort(key=lambda x: x.stat().st_size, reverse=True)
        
        logger.info(f"📁 {len(data_files)} fichiers trouvés:")
        for f in data_files[:5]:  # Afficher seulement 5 premiers
            size_mb = f.stat().st_size / (1024*1024)
            logger.info(f"   • {f.name} ({size_mb:.1f} MB)")
        
        if len(data_files) > 5:
            logger.info(f"   ... et {len(data_files) - 5} autres")
        
        return data_files
    
    def load_and_merge_data(self, data_files):
        """Charge et fusionne les données de tous les fichiers"""
        logger.info("📖 Chargement et fusion des données...")
        
        all_documents = []
        seen_hashes = set()
        
        for filepath in data_files:
            try:
                logger.info(f"  Lecture de {filepath.name}...")
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if not isinstance(data, list):
                    logger.warning(f"    ⚠ Format invalide dans {filepath.name} (attendu liste)")
                    continue
                
                logger.info(f"    ✅ {len(data)} documents trouvés")
                
                # Traiter chaque document
                for doc in data:
                    # Standardiser le document
                    standardized = self.standardize_document(doc, filepath.name)
                    
                    if standardized:
                        # Vérifier les doublons par hash
                        doc_hash = hashlib.md5(json.dumps(standardized, sort_keys=True).encode()).hexdigest()
                        
                        if doc_hash not in seen_hashes:
                            seen_hashes.add(doc_hash)
                            all_documents.append(standardized)
                
            except json.JSONDecodeError as e:
                logger.error(f"    ❌ Erreur JSON dans {filepath.name}: {e}")
            except Exception as e:
                logger.error(f"    ❌ Erreur lecture {filepath.name}: {e}")
        
        # Limiter au nombre maximum
        if len(all_documents) > self.max_docs:
            logger.info(f"📊 Limitation à {self.max_docs} documents (sur {len(all_documents)})")
            all_documents = all_documents[:self.max_docs]
        
        logger.info(f"📊 Total documents uniques: {len(all_documents)}")
        return all_documents
    
    def standardize_document(self, doc, source_file):
        """Standardise un document"""
        # Extraire l'ID
        doc_id = doc.get('arxiv_id') or doc.get('id') or doc.get('_id', '')
        if not doc_id:
            return None
        
        # Standardiser les champs
        standardized = {
            "id": doc_id,
            "arxiv_id": doc_id,
            "title": doc.get('title', doc.get('Title', '')).strip(),
            "abstract": doc.get('abstract', doc.get('Abstract', doc.get('summary', ''))).strip(),
            "authors": self.clean_list_field(doc.get('authors', [])),
            "categories": self.clean_list_field(doc.get('categories', [])),
            "primary_category": doc.get('primary_category', doc.get('main_category', '')),
            "date": self.extract_date(doc),
            "year": self.extract_year(doc),
            "source": "arXiv",
            "import_source": source_file,
            "import_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Vérifier que le document a un titre et un abstract
        if not standardized['title'] or not standardized['abstract']:
            return None
        
        # Nettoyer l'abstract (limiter la longueur)
        if len(standardized['abstract']) > 5000:
            standardized['abstract'] = standardized['abstract'][:5000] + "..."
        
        return standardized
    
    def clean_list_field(self, field):
        """Nettoie un champ qui peut être une liste ou une string"""
        if isinstance(field, list):
            return [str(item).strip() for item in field if item]
        elif isinstance(field, str):
            # Essayer de parser comme JSON si c'est une string JSON
            try:
                parsed = json.loads(field)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if item]
            except:
                # Sinon, split par virgule
                return [item.strip() for item in field.split(',') if item.strip()]
        return []
    
    def extract_date(self, doc):
        """Extrait la date du document"""
        date_fields = ['published', 'date', 'publication_date', 'created']
        
        for field in date_fields:
            if field in doc and doc[field]:
                date_str = str(doc[field])
                # Essayer d'extraire YYYY-MM-DD
                if len(date_str) >= 10:
                    return date_str[:10]
        
        # Date par défaut
        return "2025-01-01"
    
    def extract_year(self, doc):
        """Extrait l'année du document"""
        # D'abord essayer les champs explicites
        if 'year' in doc and doc['year']:
            try:
                return int(doc['year'])
            except:
                pass
        
        # Essayer d'extraire de la date
        date_str = self.extract_date(doc)
        if len(date_str) >= 4:
            try:
                return int(date_str[:4])
            except:
                pass
        
        # Par défaut
        return 2025
    
    def create_index(self):
        """Crée l'index Elasticsearch"""
        logger.info(f"📁 Création de l'index '{self.index_name}'...")
        
        # Vérifier si l'index existe déjà
        try:
            response = requests.get(f"{self.es_url}/{self.index_name}")
            if response.status_code == 200:
                logger.info("🗑️ Index existe déjà, suppression...")
                requests.delete(f"{self.es_url}/{self.index_name}")
                time.sleep(2)
        except:
            pass
        
        # Mapping optimisé pour la recherche
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "refresh_interval": "30s",
                "analysis": {
                    "analyzer": {
                        "default": {
                            "type": "standard",
                            "stopwords": "_english_"
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "arxiv_id": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "analyzer": "default",
                        "fields": {
                            "keyword": {"type": "keyword", "ignore_above": 256}
                        }
                    },
                    "abstract": {
                        "type": "text",
                        "analyzer": "default"
                    },
                    "authors": {"type": "keyword"},
                    "categories": {"type": "keyword"},
                    "primary_category": {"type": "keyword"},
                    "date": {"type": "date", "format": "yyyy-MM-dd"},
                    "year": {"type": "integer"},
                    "source": {"type": "keyword"},
                    "import_source": {"type": "keyword"},
                    "import_timestamp": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"}
                }
            }
        }
        
        try:
            response = requests.put(
                f"{self.es_url}/{self.index_name}",
                json=mapping,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info("✅ Index créé avec succès")
                return True
            else:
                logger.error(f"❌ Erreur création index: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception création index: {e}")
            return False
    
    def import_documents(self, documents):
        """Importe les documents dans Elasticsearch"""
        logger.info(f"🚀 Importation de {len(documents)} documents...")
        
        total_imported = 0
        start_time = time.time()
        
        # Importer par lots
        for i in tqdm(range(0, len(documents), self.batch_size), 
                     desc="Importation", unit="batch"):
            batch = documents[i:i + self.batch_size]
            
            # Préparer le format bulk
            bulk_data = []
            for doc in batch:
                # Action d'indexation
                bulk_data.append(json.dumps({
                    "index": {
                        "_index": self.index_name,
                        "_id": doc["id"]
                    }
                }))
                # Document
                bulk_data.append(json.dumps(doc))
            
            # Convertir en NDJSON
            ndjson = '\n'.join(bulk_data) + '\n'
            
            # Envoyer avec retry
            success = self.send_batch_with_retry(ndjson)
            if success:
                total_imported += len(batch)
            
            # Log périodique
            if (i + self.batch_size) % 1000 == 0:
                elapsed = time.time() - start_time
                rate = total_imported / elapsed
                logger.info(f"  ⚡ {total_imported:,} docs importés @ {rate:.1f} docs/sec")
            
            # Petite pause
            time.sleep(0.1)
        
        elapsed = time.time() - start_time
        rate = total_imported / elapsed if elapsed > 0 else 0
        
        logger.info(f"✅ Importation terminée!")
        logger.info(f"   • Documents importés: {total_imported:,}")
        logger.info(f"   • Temps total: {elapsed:.1f} secondes")
        logger.info(f"   • Vitesse: {rate:.1f} documents/sec")
        
        return total_imported
    
    def send_batch_with_retry(self, ndjson_data, max_retries=3):
        """Envoie un batch avec mécanisme de retry"""
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.es_url}/_bulk",
                    data=ndjson_data,
                    headers={'Content-Type': 'application/x-ndjson'},
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if not result.get('errors'):
                        return True
                    else:
                        # Log des erreurs mais continuer
                        errors = [item.get('index', {}).get('error') 
                                 for item in result.get('items', []) 
                                 if 'error' in item.get('index', {})]
                        if errors:
                            logger.warning(f"⚠ Erreurs dans le batch: {errors[:2]}...")
                        return len(errors) < len(result.get('items', [])) / 2  # Moitié d'erreurs max
                else:
                    logger.warning(f"⚠ Tentative {attempt + 1}/{max_retries} échouée: {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"⚠ Exception tentative {attempt + 1}/{max_retries}: {e}")
            
            # Attendre avant de réessayer
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"  ⏳ Attente de {wait_time}s avant nouvelle tentative...")
                time.sleep(wait_time)
        
        return False
    
    def verify_import(self):
        """Vérifie l'importation"""
        logger.info("🔍 Vérification de l'importation...")
        
        # Attendre que l'indexation soit terminée
        time.sleep(3)
        
        try:
            # Rafraîchir l'index
            requests.post(f"{self.es_url}/{self.index_name}/_refresh", timeout=10)
            
            # Compter les documents
            response = requests.get(f"{self.es_url}/{self.index_name}/_count", timeout=10)
            if response.status_code == 200:
                count = response.json().get('count', 0)
                logger.info(f"📊 Documents dans l'index: {count:,}")
                
                # Test recherche
                test_query = {
                    "query": {
                        "match": {
                            "title": "machine learning"
                        }
                    },
                    "size": 1
                }
                
                response = requests.post(
                    f"{self.es_url}/{self.index_name}/_search",
                    json=test_query,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    total_hits = data['hits']['total']['value']
                    took = data['took']
                    
                    logger.info(f"🔍 Test recherche 'machine learning':")
                    logger.info(f"   • Résultats: {total_hits:,}")
                    logger.info(f"   • Temps: {took}ms")
                    
                    if data['hits']['hits']:
                        doc = data['hits']['hits'][0]['_source']
                        logger.info(f"📄 Exemple: {doc.get('title', '')[:60]}...")
                
                return True
                
            else:
                logger.error(f"❌ Impossible de vérifier: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur vérification: {e}")
            return False
    
    def optimize_index(self):
        """Optimise l'index après importation"""
        logger.info("🔧 Optimisation de l'index...")
        
        try:
            # Fusionner les segments
            response = requests.post(
                f"{self.es_url}/{self.index_name}/_forcemerge?max_num_segments=1",
                timeout=120  # Long timeout pour le merge
            )
            
            if response.status_code == 200:
                logger.info("✅ Fusion des segments terminée")
            else:
                logger.warning(f"⚠ Fusion échouée: {response.status_code}")
            
            # Statistiques
            response = requests.get(f"{self.es_url}/{self.index_name}/_stats/store", timeout=10)
            if response.status_code == 200:
                stats = response.json()
                size_bytes = stats['indices'][self.index_name]['total']['store']['size_in_bytes']
                size_mb = size_bytes / (1024*1024)
                logger.info(f"💾 Taille index: {size_mb:.1f} MB")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur optimisation: {e}")
            return False
    
    def run(self):
        """Exécute l'importation complète"""
        logger.info("=" * 60)
        logger.info("🚀 IMPORTATEUR OPTIMISÉ POUR DÉVELOPPEMENT")
        logger.info("=" * 60)
        
        # 1. Vérifier Elasticsearch
        if not self.check_elasticsearch():
            return False
        
        # 2. Trouver les fichiers de données
        data_files = self.find_data_files()
        if not data_files:
            logger.error("❌ Aucun fichier de données trouvé")
            return False
        
        # 3. Charger et fusionner les données
        documents = self.load_and_merge_data(data_files)
        if not documents:
            logger.error("❌ Aucun document à importer")
            return False
        
        # 4. Créer l'index
        if not self.create_index():
            return False
        
        time.sleep(2)
        
        # 5. Importer les documents
        imported_count = self.import_documents(documents)
        
        # 6. Vérifier
        self.verify_import()
        
        # 7. Optimiser
        self.optimize_index()
        
        # Résumé
        logger.info("=" * 60)
        logger.info("✅ IMPORTATION TERMINÉE AVEC SUCCÈS!")
        logger.info(f"📁 Index: {self.index_name}")
        logger.info(f"📊 Documents: {imported_count:,}")
        logger.info(f"🌐 Test API: http://localhost:8000/search?query=machine+learning")
        logger.info("=" * 60)
        
        return True

def main():
    """Point d'entrée principal"""
    try:
        # Vérifier si tqdm est installé
        try:
            import tqdm
        except ImportError:
            print("❌ Le module 'tqdm' n'est pas installé.")
            print("   Installer avec: pip install tqdm")
            return
        
        importer = DataImporter()
        success = importer.run()
        
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹ Importation interrompue par l'utilisateur.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
