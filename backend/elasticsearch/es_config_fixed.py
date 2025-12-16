import os
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class ElasticsearchConfigFixed:
    """Configuration fixée pour Elasticsearch 8.x"""
    
    def __init__(self, force_no_auth=True):
        self.host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
        self.port = int(os.getenv('ELASTICSEARCH_PORT', 9200))
        self.index_name = os.getenv('ELASTICSEARCH_INDEX', 'arxiv_papers')
        self.force_no_auth = force_no_auth
        
    def check_es_available(self):
        """Vérifie si Elasticsearch répond via HTTP simple"""
        try:
            url = f"http://{self.host}:{self.port}"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_client(self):
        """Retourne un client Elasticsearch qui fonctionne"""
        # D'abord vérifier qu'ES est disponible
        if not self.check_es_available():
            logger.error(f"❌ Elasticsearch non disponible sur http://{self.host}:{self.port}")
            logger.info("💡 Vérifiez: docker compose ps et curl http://localhost:9200")
            return None
        
        logger.info(f"✅ Elasticsearch disponible sur http://{self.host}:{self.port}")
        
        # Configuration pour contourner les problèmes de sécurité
        es_config = {
            'hosts': [f"http://{self.host}:{self.port}"],
            'verify_certs': False,
            'ssl_show_warn': False,
            'request_timeout': 60,
            'max_retries': 10,
            'retry_on_timeout': True,
        }
        
        # Pour ES 8.x avec sécurité désactivée
        if self.force_no_auth:
            es_config['basic_auth'] = None
        
        try:
            client = Elasticsearch(**es_config)
            
            # Tester avec une méthode simple
            try:
                # Essayer d'abord sans authentification
                info = client.info(request_timeout=10)
                logger.info(f"✅ Connecté à Elasticsearch {info['version']['number']}")
                return client
            except Exception as auth_error:
                logger.warning(f"⚠ Premier essai échoué: {auth_error}")
                
                # Essayer avec des paramètres différents
                es_config_simple = {
                    'hosts': [f"http://{self.host}:{self.port}"],
                    'verify_certs': False,
                    'request_timeout': 30,
                }
                
                client_simple = Elasticsearch(**es_config_simple)
                
                try:
                    info = client_simple.info()
                    logger.info(f"✅ Connecté (méthode simple) à ES {info['version']['number']}")
                    return client_simple
                except Exception as e:
                    logger.error(f"❌ Toutes les méthodes ont échoué: {e}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Impossible de créer le client: {e}")
            return None

# Instance fixée
es_config_fixed = ElasticsearchConfigFixed(force_no_auth=True)
