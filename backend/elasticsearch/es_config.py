import os
from elasticsearch import Elasticsearch, ElasticsearchWarning
from dotenv import load_dotenv
import logging
import warnings

# Supprimer les warnings Elasticsearch
warnings.filterwarnings("ignore", category=ElasticsearchWarning)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class ElasticsearchConfig:
    """Configuration pour la connexion Elasticsearch"""
    
    def __init__(self):
        self.host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
        self.port = int(os.getenv('ELASTICSEARCH_PORT', 9200))
        self.scheme = os.getenv('ELASTICSEARCH_SCHEME', 'http')
        self.username = os.getenv('ELASTICSEARCH_USERNAME', '')
        self.password = os.getenv('ELASTICSEARCH_PASSWORD', '')
        self.index_name = os.getenv('ELASTICSEARCH_INDEX', 'arxiv_papers')
        self.embedding_dim = 384
        
    def get_client(self):
        """Retourne une instance du client Elasticsearch"""
        try:
            # URL de connexion
            hosts = [f"{self.scheme}://{self.host}:{self.port}"]
            logger.info(f"🔗 Tentative de connexion à: {hosts[0]}")
            
            # Configuration du client
            es_kwargs = {
                'hosts': hosts,
                'request_timeout': 30,
                'max_retries': 3,
                'retry_on_timeout': True,
                'verify_certs': False,  # Important pour développement
                'ssl_show_warn': False,
            }
            
            # Ajouter l'authentification si configurée
            if self.username and self.password:
                es_kwargs['basic_auth'] = (self.username, self.password)
            
            # Créer le client
            client = Elasticsearch(**es_kwargs)
            
            # Tester la connexion avec info() au lieu de ping()
            try:
                info = client.info()
                logger.info(f"✅ Connecté à Elasticsearch {info['version']['number']}")
                logger.info(f"   Cluster: {info['cluster_name']}")
                return client
            except Exception as ping_error:
                logger.warning(f"⚠ client.info() échoué: {ping_error}")
                
                # Essayer une autre méthode de test
                try:
                    # Tester avec une requête GET simple
                    response = client.perform_request('GET', '/')
                    if response.status_code == 200:
                        logger.info("✅ Connexion testée avec perform_request")
                        return client
                except Exception as e2:
                    logger.error(f"❌ Toutes les méthodes de test ont échoué: {e2}")
                    return None
                
        except Exception as e:
            logger.error(f"❌ Erreur création client Elasticsearch: {e}")
            return None

# Instance globale de configuration
es_config = ElasticsearchConfig()
