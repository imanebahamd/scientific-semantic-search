# backend/api.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import requests
from fastapi import Body
import time
import numpy as np
from datetime import datetime
import logging
from collections import Counter
import os

ELASTICSEARCH_URL = f"http://{os.getenv('ELASTICSEARCH_HOST', 'elasticsearch')}:{os.getenv('ELASTICSEARCH_PORT', '9200')}"
# ============================================
# CONFIGURATION DU LOGGING SIMPLIFIÉ
# ============================================

# Configurer le logging pour afficher dans le terminal VS Code
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Historique des recherches en mémoire
search_history = []
MAX_HISTORY = 100

# ============================================
# FONCTIONS DE LOGGING SIMPLIFIÉES
# ============================================

def log_search_start(query: str, search_type: str):
    """Log le début d'une recherche"""
    logger.info("🔍" + "="*60)
    logger.info(f"🔍 NOUVELLE RECHERCHE: {query}")
    logger.info(f"🔍 Type: {search_type}")
    logger.info(f"🔍 Heure: {datetime.now().strftime('%H:%M:%S')}")
    logger.info("🔍" + "="*60)

def log_search_results(query: str, results: list, execution_time: float, search_type: str):
    """Log les résultats d'une recherche de manière simplifiée"""
    
    # Calculer les scores
    scores = [r.get("similarity_score", 0) for r in results if isinstance(r.get("similarity_score"), (int, float))]
    
    logger.info("📊" + "="*60)
    logger.info("📊 RÉSUMÉ DES RÉSULTATS")
    logger.info("📊" + "="*60)
    
    logger.info(f"📋 Requête: {query}")
    logger.info(f"🎯 Type: {search_type}")
    logger.info(f"⏱️  Temps: {execution_time:.2f}ms")
    logger.info(f"📄 Résultats: {len(results)}")
    
    if scores:
        logger.info(f"🏆 Score max: {max(scores)*100:.1f}%")
        logger.info(f"📊 Score moyen: {np.mean(scores)*100:.1f}%")
        logger.info(f"📉 Score médian: {np.median(scores)*100:.1f}%")
        logger.info(f"⚖️  Score min: {min(scores)*100:.1f}%")
    
    # Top 3 des résultats
    if results:
        logger.info("\n🥇 TOP 3 DES RÉSULTATS:")
        for i, result in enumerate(results[:3]):
            score = result.get("similarity_score", 0)
            title = result.get("title", "")[:60] + "..." if len(result.get("title", "")) > 60 else result.get("title", "")
            category = result.get("categories", ["N/A"])[0]
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
            logger.info(f"{medal} {title}")
            logger.info(f"   Score: {score*100:.1f}% | Catégorie: {category}")
    
    # Distribution des catégories
    if results:
        categories = {}
        for result in results:
            for cat in result.get("categories", []):
                categories[cat] = categories.get(cat, 0) + 1
        
        if categories:
            logger.info("\n🏷️  DISTRIBUTION DES CATÉGORIES:")
            sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
            for cat, count in sorted_cats:
                percentage = (count / len(results)) * 100
                logger.info(f"  {cat}: {count} articles ({percentage:.1f}%)")
    
    logger.info("="*60 + "\n")
    
    # Sauvegarder dans l'historique
    save_to_history(query, results, execution_time, search_type)

def save_to_history(query: str, results: list, execution_time: float, search_type: str):
    """Sauvegarde la recherche dans l'historique"""
    scores = [r.get("similarity_score", 0) for r in results if isinstance(r.get("similarity_score"), (int, float))]
    
    entry = {
        'timestamp': datetime.now().isoformat(),
        'query': query,
        'search_type': search_type,
        'execution_time': execution_time,
        'total_results': len(results),
        'top_scores': scores[:5],
        'categories': list(set([cat for r in results for cat in r.get('categories', [])]))
    }
    
    search_history.insert(0, entry)
    if len(search_history) > MAX_HISTORY:
        search_history.pop()

def log_error(error: Exception, context: str = ""):
    """Log une erreur"""
    logger.error("❌" + "="*60)
    logger.error(f"❌ ERREUR: {str(error)}")
    if context:
        logger.error(f"❌ Contexte: {context}")
    logger.error("❌" + "="*60)

# ============================================
# INITIALISATION DE L'API
# ============================================
api = FastAPI(
    title="Scientific Semantic Search API",
    description="API pour la recherche sémantique d'articles scientifiques avec métriques",
    version="2.0.0"
)

# ============================================
# CONFIGURATION CORS
# ============================================
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# MODÈLES PYDANTIC
# ============================================
class SearchFilters(BaseModel):
    categories: Optional[List[str]] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    min_score: Optional[float] = None

# ============================================
# FONCTIONS UTILITAIRES
# ============================================
def format_elasticsearch_response(hit):
    """Formate une réponse Elasticsearch en objet structuré"""
    source = hit.get("_source", {})
    score = hit.get("_score", 0)
    
    # Normaliser le score entre 0 et 1 pour la similarité
    similarity_score = min(1.0, score / 10.0) if score > 10 else score / 10.0
    
    return {
        "id": hit.get("_id", ""),
        "score": score,
        "similarity_score": round(similarity_score, 4),
        "title": source.get("title", ""),
        "abstract": source.get("abstract", ""),
        "authors": source.get("authors", []),
        "categories": source.get("categories", []),
        "year": source.get("year", 0),
        "primary_category": source.get("primary_category", ""),
        "date": source.get("date", ""),
        "source": source.get("source", "arXiv")
    }

def calculate_similarity_stats(results):
    """Calcule les statistiques de similarité"""
    if not results:
        return {}
    
    scores = [r.get("similarity_score", 0) for r in results]
    
    return {
        "max_score": max(scores) if scores else 0,
        "min_score": min(scores) if scores else 0,
        "avg_score": sum(scores) / len(scores) if scores else 0,
        "median_score": np.median(scores) if scores else 0,
        "std_dev": np.std(scores) if len(scores) > 1 else 0,
        "total_results": len(results)
    }

def apply_filters(results, filters):
    """Applique les filtres supplémentaires sur les résultats"""
    if not filters:
        return results
    
    filtered_results = results.copy()
    
    # Filtre par score minimum
    if filters.min_score:
        filtered_results = [
            r for r in filtered_results 
            if r.get("similarity_score", 0) >= filters.min_score
        ]
    
    return filtered_results

# ============================================
# ENDPOINTS HEALTH & INFO
# ============================================
@api.get("/")
async def root():
    return {
        "message": "Scientific Semantic Search API",
        "status": "online",
        "version": "2.0.0",
        "metrics": "activées",
        "timestamp": datetime.now().isoformat()
    }

@api.get("/health")
async def health_check():
    # Vérifier la connexion à Elasticsearch
    try:
        response = requests.get(ELASTICSEARCH_URL, timeout=5)
        es_status = "connected" if response.status_code == 200 else "disconnected"
    except:
        es_status = "disconnected"
    
    return {
        "status": "healthy",
        "service": "search-api",
        "elasticsearch": es_status,
        "timestamp": datetime.now().isoformat(),
        "search_history_count": len(search_history)
    }

# ============================================
# ENDPOINTS DE RECHERCHE (AVEC LOGGING)
# ============================================
@api.post("/search/semantic")
async def semantic_search(
    query: str = Body(..., description="Requête sémantique"),
    k: int = Body(10, description="Nombre de résultats"),
    filters: Optional[SearchFilters] = Body(None, description="Filtres de recherche")
):
    """Recherche sémantique avec filtres et logging"""
    
    # Démarrer le timer
    start_time = time.time()
    log_search_start(query, "semantic")
    
    try:
        # Construction de la requête Elasticsearch
        es_query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^2", "abstract"],
                                "fuzziness": "AUTO"
                            }
                        }
                    ],
                    "filter": []
                }
            },
            "size": k,
            "_source": ["id", "title", "abstract", "authors", "categories", "year", "primary_category", "date", "source"]
        }
        
        # Ajouter filtre de catégories
        if filters and filters.categories:
            es_query["query"]["bool"]["filter"].append({
                "terms": {
                    "categories.keyword": filters.categories
                }
            })
        
        # Ajouter filtre d'années
        if filters and (filters.year_min or filters.year_max):
            year_filter = {"range": {"year": {}}}
            if filters.year_min:
                year_filter["range"]["year"]["gte"] = filters.year_min
            if filters.year_max:
                year_filter["range"]["year"]["lte"] = filters.year_max
            es_query["query"]["bool"]["filter"].append(year_filter)
        
        # Exécuter la recherche
        response = requests.post(
            f"{ELASTICSEARCH_URL}/arxiv_papers_unique/_search",
            json=es_query,
            timeout=10
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Elasticsearch error")
        
        data = response.json()
        
        # Formater les résultats
        all_results = []
        for hit in data.get("hits", {}).get("hits", []):
            formatted_result = format_elasticsearch_response(hit)
            all_results.append(formatted_result)
        
        # Appliquer les filtres supplémentaires
        filtered_results = apply_filters(all_results, filters)
        
        # Calculer le temps d'exécution
        execution_time = (time.time() - start_time) * 1000
        
        # Calculer les statistiques
        stats = calculate_similarity_stats(filtered_results)
        
        # Logger les résultats
        log_search_results(query, filtered_results, execution_time, "semantic")
        
        # Préparer la réponse
        response_data = {
            "query": query,
            "total": len(filtered_results),
            "total_unfiltered": len(all_results),
            "results": filtered_results,
            "execution_time": f"{execution_time:.2f}ms",
            "similarity_stats": stats,
            "filters_applied": filters.dict() if filters else {},
            "search_type": "semantic"
        }
        
        return response_data
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        log_error(e, f"Recherche sémantique: '{query}'")
        
        raise HTTPException(
            status_code=500, 
            detail={
                "error": str(e),
                "execution_time": f"{execution_time:.2f}ms",
                "query": query
            }
        )

@api.get("/search")
async def text_search(
    query: str = Query(..., description="Requête de recherche textuelle"),
    k: int = Query(10, description="Nombre de résultats", alias="size"),
    categories: Optional[str] = Query(None, description="Catégories (séparées par des virgules)"),
    min_score: Optional[float] = Query(None, description="Score minimum (0-1)")
):
    """Recherche textuelle simple avec logging"""
    
    # Démarrer le timer
    start_time = time.time()
    log_search_start(query, "keyword")
    
    try:
        es_query = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^2", "abstract", "authors"],
                    "fuzziness": "AUTO"
                }
            },
            "size": k,
            "_source": ["id", "title", "abstract", "authors", "categories", "year", "primary_category", "date", "source"]
        }
        
        # Ajouter filtres de catégories si spécifiés
        if categories:
            categories_list = [cat.strip() for cat in categories.split(",")]
            es_query["query"] = {
                "bool": {
                    "must": {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^2", "abstract", "authors"],
                            "fuzziness": "AUTO"
                        }
                    },
                    "filter": {
                        "terms": {
                            "categories.keyword": categories_list
                        }
                    }
                }
            }
        
        response = requests.post(
            f"{ELASTICSEARCH_URL}/arxiv_papers_unique/_search",
            json=es_query,
            timeout=10
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Elasticsearch error")
        
        data = response.json()
        
        # Formater les résultats
        all_results = []
        for hit in data.get("hits", {}).get("hits", []):
            formatted_result = format_elasticsearch_response(hit)
            all_results.append(formatted_result)
        
        # Appliquer le filtre de score minimum
        if min_score:
            filtered_results = [
                r for r in all_results 
                if r.get("similarity_score", 0) >= min_score
            ]
        else:
            filtered_results = all_results
        
        # Calculer le temps d'exécution
        execution_time = (time.time() - start_time) * 1000
        
        # Calculer les statistiques
        stats = calculate_similarity_stats(filtered_results)
        
        # Logger les résultats
        log_search_results(query, filtered_results, execution_time, "keyword")
        
        # Préparer les filtres appliqués
        filters_applied = {}
        if categories:
            filters_applied["categories"] = categories_list
        if min_score:
            filters_applied["min_score"] = min_score
        
        return {
            "query": query,
            "total": len(filtered_results),
            "total_unfiltered": len(all_results),
            "results": filtered_results,
            "took": data.get("took"),
            "execution_time": f"{execution_time:.2f}ms",
            "similarity_stats": stats,
            "filters_applied": filters_applied,
            "search_type": "keyword"
        }
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        log_error(e, f"Recherche textuelle: '{query}'")
        
        raise HTTPException(
            status_code=500, 
            detail={
                "error": str(e),
                "execution_time": f"{execution_time:.2f}ms",
                "query": query
            }
        )

# ============================================
# ENDPOINTS ARTICLE
# ============================================
@api.get("/paper/{paper_id}")
async def get_paper(paper_id: str):
    """Récupérer les détails d'un article spécifique"""
    
    try:
        response = requests.get(
            f"{ELASTICSEARCH_URL}/arxiv_papers_unique/_doc/{paper_id}",
            timeout=10
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Paper not found")
        elif response.status_code != 200:
            raise HTTPException(status_code=500, detail="Elasticsearch error")
        
        data = response.json()
        
        # Formater la réponse
        source = data.get("_source", {})
        formatted = {
            "id": data.get("_id", ""),
            "title": source.get("title", ""),
            "abstract": source.get("abstract", ""),
            "authors": source.get("authors", []),
            "categories": source.get("categories", []),
            "year": source.get("year", 0),
            "primary_category": source.get("primary_category", ""),
            "date": source.get("date", ""),
            "source": source.get("source", "arXiv"),
            "doi": source.get("doi", ""),
            "journal_ref": source.get("journal_ref", ""),
            "update_date": source.get("update_date", "")
        }
        
        return formatted
        
    except Exception as e:
        log_error(e, f"Récupération article: {paper_id}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# ENDPOINTS FILTRES
# ============================================
@api.get("/categories")
async def get_categories():
    """Récupère toutes les catégories disponibles"""
    try:
        es_query = {
            "size": 0,
            "aggs": {
                "categories": {
                    "terms": {
                        "field": "categories.keyword",
                        "size": 100
                    }
                }
            }
        }
        
        response = requests.post(
            f"{ELASTICSEARCH_URL}/arxiv_papers_unique/_search",
            json=es_query,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            buckets = data.get("aggregations", {}).get("categories", {}).get("buckets", [])
            
            categories = [
                {
                    "name": bucket["key"],
                    "count": bucket["doc_count"]
                }
                for bucket in buckets
            ]
            
            return {"categories": categories}
        else:
            return {"categories": []}
            
    except Exception as e:
        return {"categories": []}

@api.get("/years")
async def get_years():
    """Récupère les années disponibles"""
    try:
        es_query = {
            "size": 0,
            "aggs": {
                "years": {
                    "terms": {
                        "field": "year",
                        "size": 50,
                        "order": {"_key": "desc"}
                    }
                }
            }
        }
        
        response = requests.post(
            f"{ELASTICSEARCH_URL}/arxiv_papers_unique/_search",
            json=es_query,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            buckets = data.get("aggregations", {}).get("years", {}).get("buckets", [])
            
            years = [bucket["key"] for bucket in buckets]
            
            return {
                "years": years,
                "min_year": min(years) if years else 2020,
                "max_year": max(years) if years else 2024,
                "total_years": len(years)
            }
        else:
            return {
                "years": [],
                "min_year": 2020,
                "max_year": 2024,
                "total_years": 0
            }
            
    except Exception as e:
        return {
            "years": [],
            "min_year": 2020,
            "max_year": 2024,
            "total_years": 0
        }

# ============================================
# ENDPOINTS STATISTIQUES ET MÉTRIQUES
# ============================================
@api.get("/stats")
async def get_stats():
    """Statistiques de la base de données et des recherches"""
    try:
        # Nombre total de documents
        count_response = requests.get(
            f"{ELASTICSEARCH_URL}/arxiv_papers_unique/_count",
            timeout=10
        )
        
        total_count = 0
        if count_response.status_code == 200:
            total_count = count_response.json().get("count", 0)
        
        # Années et catégories
        years_response = requests.post(
            f"{ELASTICSEARCH_URL}/arxiv_papers_unique/_search",
            json={
                "size": 0,
                "aggs": {
                    "years": {
                        "terms": {
                            "field": "year",
                            "size": 10,
                            "order": {"_key": "desc"}
                        }
                    },
                    "top_categories": {
                        "terms": {
                            "field": "categories.keyword",
                            "size": 15,
                            "order": {"_count": "desc"}
                        }
                    }
                }
            },
            timeout=10
        )
        
        recent_years = []
        top_categories = []
        
        if years_response.status_code == 200:
            data = years_response.json()
            
            # Années récentes
            years_buckets = data.get("aggregations", {}).get("years", {}).get("buckets", [])
            recent_years = [
                {"year": bucket["key"], "count": bucket["doc_count"]} 
                for bucket in years_buckets
            ]
            
            # Catégories top
            categories_buckets = data.get("aggregations", {}).get("top_categories", {}).get("buckets", [])
            top_categories = [
                {"name": bucket["key"], "count": bucket["doc_count"]} 
                for bucket in categories_buckets
            ]
        
        # Statistiques des recherches
        if search_history:
            total_searches = len(search_history)
            semantic_searches = sum(1 for h in search_history if h['search_type'] == 'semantic')
            avg_execution_time = np.mean([h['execution_time'] for h in search_history])
            
            # Top queries
            query_counter = Counter([h['query'] for h in search_history])
            top_queries = [{"query": q, "count": c} for q, c in query_counter.most_common(5)]
        else:
            total_searches = 0
            semantic_searches = 0
            avg_execution_time = 0
            top_queries = []
        
        return {
            "database_stats": {
                "total_papers": total_count,
                "recent_years": recent_years,
                "top_categories": top_categories
            },
            "search_stats": {
                "total_searches": total_searches,
                "semantic_searches": semantic_searches,
                "keyword_searches": total_searches - semantic_searches,
                "avg_execution_time": f"{avg_execution_time:.2f}ms",
                "top_queries": top_queries
            },
            "system_status": {
                "elasticsearch": "connected" if total_count > 0 else "disconnected",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        log_error(e, "Statistiques système")
        return {
            "database_stats": {
                "total_papers": 0,
                "recent_years": [],
                "top_categories": []
            },
            "search_stats": {
                "total_searches": len(search_history),
                "semantic_searches": 0,
                "keyword_searches": 0,
                "avg_execution_time": "0ms",
                "top_queries": []
            },
            "system_status": {
                "elasticsearch": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        }

@api.get("/metrics/history")
async def get_search_history(limit: int = Query(10, description="Nombre d'entrées")):
    """Récupère l'historique des recherches"""
    history = search_history[:limit]
    
    if history:
        total_time = sum(h["execution_time"] for h in history)
        avg_time = total_time / len(history)
        
        # Distribution par type
        semantic_count = sum(1 for h in history if h["search_type"] == "semantic")
        keyword_count = len(history) - semantic_count
        
        return {
            "history": history,
            "stats": {
                "total": len(history),
                "avg_execution_time": f"{avg_time:.2f}ms",
                "semantic_searches": semantic_count,
                "keyword_searches": keyword_count,
                "semantic_percentage": f"{(semantic_count/len(history))*100:.1f}%" if history else "0%"
            }
        }
    else:
        return {
            "history": [],
            "stats": {
                "total": 0,
                "avg_execution_time": "0ms",
                "semantic_searches": 0,
                "keyword_searches": 0,
                "semantic_percentage": "0%"
            }
        }

@api.get("/metrics/export")
async def export_metrics():
    """Exporte les métriques au format JSON"""
    import json
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"search_metrics_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(search_history, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Export JSON réussi: {filename}")
        
        return {
            "message": "Export JSON réussi",
            "file": filename,
            "entries_exported": len(search_history),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log_error(e, "Export métriques")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# ENDPOINTS SUPPLEMENTAIRES
# ============================================
@api.get("/paper/{paper_id}/similar")
async def get_similar_papers(paper_id: str, k: int = Query(5, description="Nombre de résultats")):
    """Récupère les articles similaires"""
    try:
        # D'abord, obtenir l'article
        paper_response = requests.get(
            f"{ELASTICSEARCH_URL}/arxiv_papers_unique/_doc/{paper_id}",
            timeout=10
        )
        
        if paper_response.status_code != 200:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper_data = paper_response.json()
        source = paper_data.get("_source", {})
        
        # Rechercher des articles similaires par catégorie
        categories = source.get("categories", [])
        
        if not categories:
            return {"results": []}
        
        # Recherche par catégorie principale
        es_query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "terms": {
                                "categories.keyword": categories[:3]
                            }
                        }
                    ],
                    "must_not": [
                        {
                            "term": {
                                "_id": paper_id
                            }
                        }
                    ]
                }
            },
            "size": k,
            "_source": ["id", "title", "abstract", "authors", "categories", "year"],
            "sort": [
                {"year": {"order": "desc"}}
            ]
        }
        
        response = requests.post(
            f"{ELASTICSEARCH_URL}/arxiv_papers_unique/_search",
            json=es_query,
            timeout=10
        )
        
        if response.status_code != 200:
            return {"results": []}
        
        data = response.json()
        
        results = []
        for hit in data.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            results.append({
                "id": hit.get("_id", ""),
                "title": source.get("title", ""),
                "abstract": source.get("abstract", "")[:200] + "...",
                "authors": source.get("authors", []),
                "categories": source.get("categories", []),
                "year": source.get("year", 0),
                "score": hit.get("_score", 0)
            })
        
        return {"results": results}
        
    except Exception as e:
        log_error(e, f"Recherche articles similaires: {paper_id}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# EXÉCUTION
# ============================================
if __name__ == "__main__":
    import uvicorn
    
    # Afficher un message de démarrage
    print("\n" + "="*60)
    print("🚀 SCIENTIFIC SEMANTIC SEARCH API v2.0.0")
    print("="*60)
    print("📊 Logging des métriques: ACTIVÉ")
    print("🌐 API disponible sur: http://0.0.0.0:8001")
    print("📈 Documentation: http://0.0.0.0:8001/docs")
    print("📋 Commandes utiles:")
    print("   • curl http://localhost:8001/health")
    print("   • curl http://localhost:8001/stats")
    print("   • curl http://localhost:8001/metrics/history")
    print("="*60 + "\n")
    
    uvicorn.run(api, host="0.0.0.0", port=8001)

# Debug function (ajouter après ELASTICSEARCH_URL)
def debug_config():
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🔧 DEBUG - ELASTICSEARCH_URL = {ELASTICSEARCH_URL}")
    logger.info(f"🔧 DEBUG - URL complète exemple: {ELASTICSEARCH_URL}/arxiv_papers_unique/_search")

# Appeler au démarrage (ajouter à la fin du fichier, avant le __main__)
debug_config()
