# backend/services/metrics_logger.py
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np
from pathlib import Path
import logging

class ServerMetricsLogger:
    """Logger pour afficher les métriques dans le terminal VS Code"""
    
    def __init__(self, log_file: str = None):
        self.log_file = log_file
        self.search_history: List[Dict] = []
        self.max_history = 100
        
        # Configuration du logging
        self.setup_logging()
        
    def setup_logging(self):
        """Configure le logging pour VS Code terminal"""
        # Créer un formateur personnalisé
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Handler pour console (terminal VS Code)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # Logger principal
        self.logger = logging.getLogger('SearchMetrics')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        
        # Fichier de log si spécifié
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def log_search_start(self, query: str, search_type: str = "semantic"):
        """Log le début d'une recherche"""
        self.logger.info("🔍" + "="*60)
        self.logger.info(f"🔍 NOUVELLE RECHERCHE: {query}")
        self.logger.info(f"🔍 Type: {search_type}")
        self.logger.info(f"🔍 Heure: {datetime.now().strftime('%H:%M:%S')}")
        self.logger.info("🔍" + "="*60)
        return time.time()
    
    def log_search_results(self, query: str, results: List[Dict], 
                          execution_time: float, search_type: str = "semantic"):
        """Log les résultats d'une recherche"""
        
        # Calculer les métriques
        scores = [r.get('similarity_score', r.get('score', 0)) for r in results]
        if isinstance(scores[0], (int, float)):
            scores = [float(s) for s in scores]
        else:
            scores = []
        
        # Afficher le résumé
        self.logger.info("📊" + "="*60)
        self.logger.info("📊 RÉSUMÉ DES RÉSULTATS")
        self.logger.info("📊" + "="*60)
        
        self.logger.info(f"📋 Requête: {query}")
        self.logger.info(f"🎯 Type: {search_type}")
        self.logger.info(f"⏱️  Temps: {execution_time:.2f}ms")
        self.logger.info(f"📄 Résultats: {len(results)}")
        
        if scores:
            self.logger.info(f"🏆 Score max: {max(scores)*100:.1f}%")
            self.logger.info(f"📊 Score moyen: {np.mean(scores)*100:.1f}%")
            self.logger.info(f"📉 Score médian: {np.median(scores)*100:.1f}%")
            self.logger.info(f"⚖️  Score min: {min(scores)*100:.1f}%")
        
        # Afficher le top 3
        self.logger.info("\n🥇 TOP 3 DES RÉSULTATS:")
        for i, result in enumerate(results[:3]):
            score = result.get('similarity_score', result.get('score', 0))
            title = result.get('title', '')[:60] + "..." if len(result.get('title', '')) > 60 else result.get('title', '')
            category = result.get('categories', [''])[0] if result.get('categories') else 'N/A'
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
            self.logger.info(f"{medal} {title}")
            self.logger.info(f"   Score: {float(score)*100:.1f}% | Catégorie: {category}")
        
        # Distribution des catégories
        if results:
            categories = {}
            for result in results:
                for cat in result.get('categories', []):
                    categories[cat] = categories.get(cat, 0) + 1
            
            if categories:
                self.logger.info("\n🏷️  DISTRIBUTION DES CATÉGORIES:")
                sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
                for cat, count in sorted_cats:
                    percentage = (count / len(results)) * 100
                    self.logger.info(f"  {cat}: {count} articles ({percentage:.1f}%)")
        
        # Histogramme ASCII des scores
        if scores:
            self.logger.info("\n📈 DISTRIBUTION DES SCORES:")
            self.display_histogram(scores)
        
        self.logger.info("="*60 + "\n")
        
        # Sauvegarder dans l'historique
        self.save_to_history(query, results, execution_time, search_type)
    
    def display_histogram(self, scores: List[float], bins: int = 10):
        """Affiche un histogramme ASCII des scores"""
        if not scores:
            return
        
        # Convertir en pourcentages
        percentages = [s * 100 for s in scores]
        
        # Créer les bins
        min_val, max_val = min(percentages), max(percentages)
        bin_width = (max_val - min_val) / bins
        
        histogram = [0] * bins
        for p in percentages:
            bin_idx = min(int((p - min_val) / bin_width), bins - 1)
            histogram[bin_idx] += 1
        
        # Afficher l'histogramme
        max_count = max(histogram) if histogram else 1
        for i in range(bins):
            count = histogram[i]
            bar_length = int((count / max_count) * 40)
            bar = "█" * bar_length + "░" * (40 - bar_length)
            
            range_start = min_val + i * bin_width
            range_end = min_val + (i + 1) * bin_width
            
            if count > 0:
                percentage = (count / len(scores)) * 100
                self.logger.info(f"  [{range_start:.1f}-{range_end:.1f}%]: {bar} {count} ({percentage:.1f}%)")
    
    def save_to_history(self, query: str, results: List[Dict], 
                       execution_time: float, search_type: str):
        """Sauvegarde la recherche dans l'historique"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'search_type': search_type,
            'execution_time': execution_time,
            'total_results': len(results),
            'top_scores': [r.get('similarity_score', r.get('score', 0)) for r in results[:5]],
            'categories': list(set([cat for r in results for cat in r.get('categories', [])]))
        }
        
        self.search_history.insert(0, entry)
        if len(self.search_history) > self.max_history:
            self.search_history.pop()
    
    def show_history(self):
        """Affiche l'historique des recherches"""
        self.logger.info("📋" + "="*60)
        self.logger.info("📋 HISTORIQUE DES RECHERCHES")
        self.logger.info("📋" + "="*60)
        
        for i, entry in enumerate(self.search_history[:10]):  # Montrer les 10 dernières
            date_str = datetime.fromisoformat(entry['timestamp']).strftime('%H:%M:%S')
            avg_score = np.mean(entry['top_scores']) * 100 if entry['top_scores'] else 0
            
            self.logger.info(f"{i+1}. [{date_str}] {entry['query'][:40]}...")
            self.logger.info(f"   Type: {entry['search_type']} | Temps: {entry['execution_time']:.0f}ms")
            self.logger.info(f"   Résultats: {entry['total_results']} | Score moyen: {avg_score:.1f}%")
        
        self.logger.info("="*60)
    
    def export_history(self, filename: str = "search_history.json"):
        """Exporte l'historique au format JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.search_history, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"✅ Historique exporté vers {filename}")
    
    def log_error(self, error: Exception, context: str = ""):
        """Log une erreur"""
        self.logger.error("❌" + "="*60)
        self.logger.error(f"❌ ERREUR: {str(error)}")
        if context:
            self.logger.error(f"❌ Contexte: {context}")
        self.logger.error("❌" + "="*60)

# Instance singleton
server_metrics_logger = ServerMetricsLogger()