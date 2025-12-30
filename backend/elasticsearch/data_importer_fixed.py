
#!/usr/bin/env python3
"""
Importateur OPTIMISÉ avec IDs UNIQUES pour éviter les écrasements
Version pour exécution depuis l'hôte
"""

import json
import requests
import time
import hashlib
import sys
import os
from pathlib import Path
from tqdm import tqdm
import logging
import random

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataImporterFixed:
    """Importateur avec IDs uniques pour éviter les écrasements"""
    
    def __init__(self):
        # Essayer d'abord localhost (pour exécution depuis l'hôte)
        # Si dans Docker, utiliser le nom du service
        self.es_url = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
        self.index_name = "arxiv_papers_unique"
        self.batch_size = 500
        self.max_docs = 10000
        
        logger.info(f"🔗 URL Elasticsearch: {self.es_url}")
        logger.info(f"📁 Index cible: {self.index_name}")
        
        # Vérifier la connexion
        self.check_elasticsearch()
    
    def check_elasticsearch(self):
        """Vérifie la connexion à Elasticsearch"""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                logger.info(f"🔍 Tentative de connexion {attempt + 1}/{max_retries}...")
                response = requests.get(self.es_url, timeout=10)
                if response.status_code == 200:
                    logger.info(f"✅ Connecté à Elasticsearch: {self.es_url}")
                    # Afficher les infos
                    info = response.json()
                    logger.info(f"   Version: {info['version']['number']}")
                    logger.info(f"   Cluster: {info['cluster_name']}")
                    return True
                else:
                    logger.warning(f"⚠ Code HTTP {response.status_code}")
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"⚠ Connexion échouée: {e}")
                # Essayer localhost si ce n'était pas déjà le cas
                if self.es_url == 'http://elasticsearch:9200':
                    self.es_url = 'http://localhost:9200'
                    logger.info(f"🔄 Essai avec {self.es_url}")
            except Exception as e:
                logger.warning(f"⚠ Erreur: {e}")
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"⏳ Attente de {wait_time}s avant nouvelle tentative...")
                time.sleep(wait_time)
        
        logger.error("❌ Impossible de se connecter à Elasticsearch")
        logger.info("💡 Vérifiez que Elasticsearch est démarré:")
        logger.info("   docker compose ps")
        logger.info("   docker compose logs elasticsearch")
        return False
    
    def generate_unique_id(self, doc, source_file):
        """Génère un ID unique pour chaque document"""
        # Utiliser arxiv_id + hash du titre + source pour garantir l'unicité
        arxiv_id = doc.get('arxiv_id', doc.get('id', ''))
        title = doc.get('title', '')
        
        if arxiv_id and title:
            # Combiner arxiv_id, hash du titre et source
            content = f"{arxiv_id}_{hashlib.md5(title.encode()).hexdigest()[:8]}_{source_file}"
            return hashlib.md5(content.encode()).hexdigest()
        else:
            # Fallback: timestamp + random
            return f"doc_{int(time.time())}_{random.randint(1000, 9999)}"
    
    def load_all_data(self):
        """Charge toutes les données avec IDs uniques"""
        logger.info("📁 Chargement de toutes les données...")
        
        # Chercher le dossier data depuis différents chemins
        possible_paths = [
            Path("../../data"),          # Depuis backend/elasticsearch
            Path("../../../data"),       # Depuis la racine du projet
            Path("/app/data"),           # Dans Docker
            Path("data")                 # Local
        ]
        
        data_dir = None
        for path in possible_paths:
            if path.exists() and path.is_dir():
                data_dir = path
                logger.info(f"📁 Dossier data trouvé: {data_dir}")
                break
        
        if not data_dir:
            logger.error("❌ Dossier data introuvable")
            return []
        
        # Tous les fichiers JSON disponibles
        json_patterns = ["*.json", "cleaned/*.json", "raw/*.json"]
        json_files = []
        
        for pattern in json_patterns:
            try:
                json_files.extend(list(data_dir.glob(pattern)))
            except:
                pass
        
        logger.info(f"📋 {len(json_files)} fichiers JSON trouvés")
        
        all_documents = []
        seen_content_hashes = set()  # Pour détecter le contenu dupliqué
        
        for filepath in json_files:
            try:
                file_size = filepath.stat().st_size / 1024  # Taille en KB
                logger.info(f"  📖 {filepath.name} ({file_size:.1f} KB)")
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if not isinstance(data, list):
                    logger.warning(f"    ⚠ Format invalide (attendu liste)")
                    continue
                
                logger.info(f"    ✅ {len(data)} documents")
                
                # Traiter chaque document
                processed = 0
                for doc in data:
                    # Standardiser le document
                    standardized = self.standardize_document(doc, filepath.name)
                    
                    if standardized:
                        # Vérifier le contenu dupliqué (même titre + abstract)
                        content_hash = hashlib.md5(
                            f"{standardized['title']}{standardized['abstract']}".encode()
                        ).hexdigest()
                        
                        if content_hash not in seen_content_hashes:
                            seen_content_hashes.add(content_hash)
                            
                            # Générer un ID unique
                            unique_id = self.generate_unique_id(doc, filepath.name)
                            standardized['id'] = unique_id
                            standardized['unique_id'] = unique_id
                            
                            all_documents.append(standardized)
                            processed += 1
                
                logger.info(f"    ➕ {processed} nouveaux documents uniques")
                
            except json.JSONDecodeError as e:
                logger.error(f"    ❌ Erreur JSON dans {filepath.name}: {e}")
            except Exception as e:
                logger.error(f"    ❌ Erreur {filepath.name}: {e}")
                continue
        
        logger.info(f"📊 Total documents uniques: {len(all_documents)}")
        
        # Statistiques
        if all_documents:
            sources = {}
            for doc in all_documents:
                source = doc.get('import_source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
            
            logger.info("📈 Statistiques par source:")
            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"   • {source}: {count} documents")
        
        return all_documents[:self.max_docs]
    
    def standardize_document(self, doc, source_file):
        """Standardise un document"""
        try:
            # Extraire les champs de base
            title = doc.get('title', doc.get('Title', ''))
            abstract = doc.get('abstract', doc.get('Abstract', doc.get('summary', '')))
            
            if not title or not abstract:
                return None
            
            # Nettoyer
            title = str(title).strip()
            abstract = str(abstract).strip()
            
            # Vérifier la longueur minimale
            if len(abstract) < 50:
                return None
            
            # Limiter la longueur de l'abstract
            if len(abstract) > 5000:
                abstract = abstract[:5000] + "..."
            
            # Extraire arxiv_id
            arxiv_id = doc.get('arxiv_id', doc.get('id', ''))
            
            # Extraire auteurs
            authors = self.extract_authors(doc)
            
            # Extraire catégories
            categories = self.extract_categories(doc)
            
            # Extraire date
            date_info = self.extract_date_info(doc)
            
            return {
                "title": title,
                "abstract": abstract,
                "arxiv_id": arxiv_id,
                "authors": authors,
                "categories": categories,
                "primary_category": categories[0] if categories else "",
                "date": date_info['date'],
                "year": date_info['year'],
                "month": date_info['month'],
                "source": "arXiv",
                "import_source": source_file,
                "import_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "content_length": len(abstract)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur standardisation: {e}")
            return None
    
    def extract_authors(self, doc):
        """Extrait et nettoie la liste des auteurs"""
        authors = doc.get('authors', [])
        if isinstance(authors, list):
            return [str(a).strip() for a in authors if a]
        elif isinstance(authors, str):
            # Essayer de parser
            try:
                parsed = json.loads(authors)
                if isinstance(parsed, list):
                    return [str(a).strip() for a in parsed if a]
            except:
                # Split par virgule
                return [a.strip() for a in authors.split(',') if a.strip()]
        return []
    
    def extract_categories(self, doc):
        """Extrait et nettoie les catégories"""
        categories = doc.get('categories', [])
        if isinstance(categories, list):
            return [str(c).strip() for c in categories if c]
        elif isinstance(categories, str):
            try:
                parsed = json.loads(categories)
                if isinstance(parsed, list):
                    return [str(c).strip() for c in parsed if c]
            except:
                return [c.strip() for c in categories.split(',') if c.strip()]
        return []
    
    def extract_date_info(self, doc):
        """Extrait les informations de date"""
        date_str = doc.get('published', doc.get('date', doc.get('publication_date', '')))
        year = doc.get('year', 2025)
        month = doc.get('month', 1)
        
        if date_str:
            # Essayer d'extraire YYYY-MM-DD
            if isinstance(date_str, str) and len(date_str) >= 10:
                try:
                    date_part = date_str[:10]
                    # Vérifier le format
                    if date_part[4] == '-' and date_part[7] == '-':
                        year = int(date_part[:4])
                        month = int(date_part[5:7])
                        return {
                            'date': date_part,
                            'year': year,
                            'month': month
                        }
                except:
                    pass
        
        # Fallback
        return {
            'date': f"{year}-{month:02d}-01",
            'year': year,
            'month': month
        }
    
    def create_index(self):
        """Crée un nouvel index avec mapping optimisé"""
        logger.info(f"📁 Création de l'index '{self.index_name}'...")
        
        # Vérifier si l'index existe déjà
        try:
            response = requests.get(f"{self.es_url}/{self.index_name}")
            if response.status_code == 200:
                logger.info("🗑️ Index existe déjà, suppression...")
                response = requests.delete(f"{self.es_url}/{self.index_name}")
                if response.status_code == 200:
                    logger.info("✅ Index supprimé")
                    time.sleep(3)
                else:
                    logger.warning(f"⚠ Erreur suppression index: {response.text}")
        except Exception as e:
            logger.warning(f"⚠ Erreur vérification index: {e}")
        
        # Mapping optimisé
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "refresh_interval": "30s",
                "max_result_window": 10000,
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
                    "unique_id": {"type": "keyword"},
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
                    "month": {"type": "integer"},
                    "source": {"type": "keyword"},
                    "import_source": {"type": "keyword"},
                    "import_timestamp": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
                    "content_length": {"type": "integer"}
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
        """Importe les documents avec IDs uniques"""
        if not documents:
            logger.error("❌ Aucun document à importer")
            return 0
        
        logger.info(f"🚀 Importation de {len(documents)} documents uniques...")
        
        total_imported = 0
        start_time = time.time()
        batch_count = (len(documents) + self.batch_size - 1) // self.batch_size
        
        # Importer par lots
        progress_bar = tqdm(range(0, len(documents), self.batch_size), 
                           desc="Importation", unit="batch", total=batch_count)
        
        for i in progress_bar:
            batch = documents[i:i + self.batch_size]
            
            # Préparer le bulk
            bulk_data = []
            for doc in batch:
                bulk_data.append(json.dumps({
                    "index": {
                        "_index": self.index_name,
                        "_id": doc["id"]  # ID unique
                    }
                }))
                bulk_data.append(json.dumps(doc))
            
            # Convertir en NDJSON
            ndjson = '\n'.join(bulk_data) + '\n'
            
            # Envoyer avec retry
            max_retries = 3
            for retry in range(max_retries):
                try:
                    response = requests.post(
                        f"{self.es_url}/_bulk",
                        data=ndjson,
                        headers={'Content-Type': 'application/x-ndjson'},
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if not result.get('errors'):
                            imported = len(batch)
                            total_imported += imported
                            
                            # Mettre à jour la barre de progression
                            progress_bar.set_postfix({
                                "imported": f"{total_imported:,}",
                                "rate": f"{(total_imported / (time.time() - start_time)):.1f}/s"
                            })
                            break
                        else:
                            # Compter les succès
                            success = 0
                            errors = []
                            for item in result.get('items', []):
                                if 'error' in item.get('index', {}):
                                    errors.append(item['index']['error'])
                                else:
                                    success += 1
                            
                            total_imported += success
                            if errors and retry == max_retries - 1:
                                logger.warning(f"⚠ {len(errors)} erreurs dans le batch")
                            
                            break
                    else:
                        logger.warning(f"⚠ HTTP {response.status_code} sur le batch")
                        
                except Exception as e:
                    logger.warning(f"⚠ Exception batch (retry {retry + 1}/{max_retries}): {e}")
                
                if retry < max_retries - 1:
                    time.sleep(2 ** retry)  # Exponential backoff
            
            # Pause courte entre les batches
            time.sleep(0.05)
        
        progress_bar.close()
        
        elapsed = time.time() - start_time
        rate = total_imported / elapsed if elapsed > 0 else 0
        
        logger.info(f"✅ Importation terminée!")
        logger.info(f"   • Documents importés: {total_imported:,}")
        logger.info(f"   • Temps total: {elapsed:.1f} secondes")
        logger.info(f"   • Vitesse: {rate:.1f} documents/sec")
        
        return total_imported
    
    def verify_and_stats(self):
        """Vérifie l'importation et affiche les statistiques"""
        logger.info("🔍 Vérification et statistiques...")
        time.sleep(3)  # Attendre l'indexation
        
        try:
            # Rafraîchir l'index
            response = requests.post(f"{self.es_url}/{self.index_name}/_refresh", timeout=10)
            if response.status_code != 200:
                logger.warning("⚠ Rafraîchissement échoué")
            
            # Compter les documents
            response = requests.get(f"{self.es_url}/{self.index_name}/_count", timeout=10)
            if response.status_code == 200:
                count = response.json().get('count', 0)
                logger.info(f"📊 Documents dans l'index: {count:,}")
                
                if count == 0:
                    logger.error("❌ L'index est vide!")
                    return False
                
                # Statistiques détaillées
                stats_query = {
                    "size": 0,
                    "aggs": {
                        "sources": {
                            "terms": {
                                "field": "import_source.keyword",
                                "size": 10
                            }
                        },
                        "top_categories": {
                            "terms": {
                                "field": "categories.keyword",
                                "size": 10
                            }
                        },
                        "years": {
                            "terms": {
                                "field": "year",
                                "size": 10,
                                "order": {"_key": "desc"}
                            }
                        }
                    }
                }
                
                response = requests.post(
                    f"{self.es_url}/{self.index_name}/_search",
                    json=stats_query,
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    logger.info("📁 Sources des documents:")
                    sources = data.get('aggregations', {}).get('sources', {}).get('buckets', [])
                    for bucket in sources[:5]:
                        logger.info(f"   • {bucket['key']}: {bucket['doc_count']}")
                    
                    logger.info("🏷️  Catégories principales:")
                    categories = data.get('aggregations', {}).get('top_categories', {}).get('buckets', [])
                    for bucket in categories[:5]:
                        logger.info(f"   • {bucket['key']}: {bucket['doc_count']}")
                    
                    logger.info("📅 Distribution par année:")
                    years = data.get('aggregations', {}).get('years', {}).get('buckets', [])
                    for bucket in years:
                        logger.info(f"   • {bucket['key']}: {bucket['doc_count']}")
                
                # Tester une recherche
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
                    test_data = response.json()
                    total = test_data['hits']['total']['value']
                    took = test_data['took']
                    logger.info(f"🔍 Test recherche 'machine learning':")
                    logger.info(f"   • Résultats: {total:,}")
                    logger.info(f"   • Temps: {took}ms")
                    
                    if test_data['hits']['hits']:
                        doc = test_data['hits']['hits'][0]['_source']
                        logger.info(f"📄 Exemple: {doc.get('title', '')[:60]}...")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur vérification: {e}")
            return False
    
    def optimize_index(self):
        """Optimise l'index après importation"""
        logger.info("🔧 Optimisation de l'index...")
        
        try:
            # Fusionner les segments pour meilleure performance
            response = requests.post(
                f"{self.es_url}/{self.index_name}/_forcemerge?max_num_segments=1",
                timeout=120
            )
            
            if response.status_code == 200:
                logger.info("✅ Fusion des segments terminée")
            else:
                logger.warning(f"⚠ Fusion échouée: {response.status_code}")
            
            # Statistiques de stockage
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
        logger.info("🚀 IMPORTATEUR AVEC IDs UNIQUES")
        logger.info("=" * 60)
        
        # 1. Vérifier Elasticsearch
        if not self.check_elasticsearch():
            logger.error("❌ Impossible de continuer sans Elasticsearch")
            return False
        
        # 2. Charger les données
        documents = self.load_all_data()
        if not documents:
            logger.error("❌ Aucun document à importer")
            return False
        
        logger.info(f"🎯 Prêt à importer {len(documents)} documents uniques")
        
        # 3. Créer l'index
        if not self.create_index():
            return False
        
        time.sleep(2)
        
        # 4. Importer
        imported_count = self.import_documents(documents)
        
        if imported_count == 0:
            logger.error("❌ Aucun document importé")
            return False
        
        # 5. Vérifier et afficher les stats
        self.verify_and_stats()
        
        # 6. Optimiser
        self.optimize_index()
        
        # Résumé
        logger.info("=" * 60)
        logger.info("✅ IMPORTATION RÉUSSIE!")
        logger.info(f"📁 Index: {self.index_name}")
        logger.info(f"📊 Documents uniques: {imported_count:,}")
        logger.info(f"🌐 API disponible sur: http://localhost:8000")
        logger.info("=" * 60)
        
        return True

def main():
    """Point d'entrée principal"""
    try:
        # Vérifier les dépendances
        try:
            import tqdm
        except ImportError:
            print("❌ 'tqdm' non installé. Installation...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "tqdm"])
            import tqdm
        
        print("\n" + "="*60)
        print("🔧 IMPORTATION DE DONNÉES SCIENTIFIQUES")
        print("="*60)
        
        importer = DataImporterFixed()
        success = importer.run()
        
        if success:
            print("\n🎉 IMPORTATION TERMINÉE AVEC SUCCÈS!")
            print("\n📋 PROCHAINES ÉTAPES:")
            print("1. Mettre à jour l'API pour utiliser le nouvel index:")
            print("   sed -i 's|arxiv_papers|arxiv_papers_unique|g' backend/api/routes_simple.py")
            print("\n2. Redémarrer le backend:")
            print("   docker compose restart backend")
            print("\n3. Tester l'API:")
            print("   curl http://localhost:8000/search?query=machine+learning")
            print("\n" + "="*60)
            sys.exit(0)
        else:
            print("\n❌ IMPORTATION ÉCHOUÉE")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹ Interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


