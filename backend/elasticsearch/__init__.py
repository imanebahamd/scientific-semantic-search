"""
Package Elasticsearch pour Scientific Semantic Search.
"""

from .es_config import ElasticsearchConfig, es_config
from .data_importer import DataImporter

# La classe FixedArXivDataImporter n'existe plus dans data_importer_arxiv.py
# Elle a été renommée en ArXivDataImporter
try:
    from .data_importer_arxiv import FixedArXivDataImporter as ArXivDataImporter
except ImportError:
    try:
        from .data_importer_arxiv import ArXivDataImporter
    except ImportError:
        # Créer une classe vide si non trouvée
        class ArXivDataImporter:
            pass

__all__ = [
    'ElasticsearchConfig',
    'es_config',
    'DataImporter',
    'ArXivDataImporter'
]
