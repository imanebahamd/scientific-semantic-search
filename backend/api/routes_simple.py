#!/usr/bin/env python3
"""
API Backend simplifiée pour Scientific Semantic Search
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import requests
import json
from datetime import datetime

app = FastAPI(
    title="Scientific Semantic Search API",
    description="API de recherche sémantique d'articles scientifiques",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Endpoint racine"""
    return {
        "message": "Scientific Semantic Search API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "search": "/search",
            "search_semantic": "/search/semantic",
            "paper_by_id": "/paper/{paper_id}",
            "stats": "/stats"
        }
    }

@app.get("/health")
async def health_check():
    """Vérifie la santé de l'API et d'Elasticsearch"""
    try:
        # Tester Elasticsearch
        es_response = requests.get("http://localhost:9200", timeout=5)
        es_ok = es_response.status_code == 200
        
        return {
            "status": "healthy",
            "api": "running",
            "elasticsearch": "connected" if es_ok else "disconnected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "api": "running",
            "elasticsearch": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/search")
async def search_papers(
    query: str = Query(..., description="Termes de recherche"),
    size: int = Query(10, description="Nombre de résultats")
):
    """Recherche classique par mots-clés"""
    
    try:
        # Requête Elasticsearch
        es_query = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^2", "abstract"],
                    "fuzziness": "AUTO"
                }
            },
            "size": size,
            "_source": ["id", "title", "abstract", "authors", "categories", "date", "year"]
        }
        
        response = requests.post(
            "http://localhost:9200/arxiv_papers/_search",
            json=es_query,
            timeout=10
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Elasticsearch error")
        
        data = response.json()
        
        # Formater les résultats
        results = []
        for hit in data.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            results.append({
                "id": hit.get("_id", ""),
                "score": hit.get("_score", 0),
                "title": source.get("title", ""),
                "abstract": source.get("abstract", "")[:300] + "..." if len(source.get("abstract", "")) > 300 else source.get("abstract", ""),
                "authors": source.get("authors", []),
                "categories": source.get("categories", []),
                "date": source.get("date", ""),
                "year": source.get("year", 0)
            })
        
        return {
            "query": query,
            "total": data.get("hits", {}).get("total", {}).get("value", 0),
            "took": data.get("took", 0),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search/semantic")
async def semantic_search(
    query: str = Query(..., description="Requête sémantique"),
    k: int = Query(5, description="Nombre de résultats")
):
    """Recherche sémantique par similarité de vecteurs"""
    
    try:
        # Pour l'instant, retourner la même chose que la recherche classique
        # Dans une version future, vous intégrerez Sentence-BERT ici
        return await search_papers(query=query, size=k)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/paper/{paper_id}")
async def get_paper_by_id(paper_id: str):
    """Récupère un article par son ID"""
    
    try:
        response = requests.get(
            f"http://localhost:9200/arxiv_papers/_doc/{paper_id}",
            timeout=10
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Paper not found")
        elif response.status_code != 200:
            raise HTTPException(status_code=500, detail="Elasticsearch error")
        
        data = response.json()
        source = data.get("_source", {})
        
        return {
            "id": data.get("_id", ""),
            "found": True,
            "title": source.get("title", ""),
            "abstract": source.get("abstract", ""),
            "authors": source.get("authors", []),
            "categories": source.get("categories", []),
            "primary_category": source.get("primary_category", ""),
            "date": source.get("date", ""),
            "year": source.get("year", 0),
            "month": source.get("month", 0),
            "source": source.get("source", "arXiv")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_statistics():
    """Récupère les statistiques de la base"""
    
    try:
        # Nombre total
        count_response = requests.get(
            "http://localhost:9200/arxiv_papers/_count",
            timeout=10
        )
        
        # Agrégations
        agg_query = {
            "size": 0,
            "aggs": {
                "categories": {
                    "terms": {
                        "field": "categories.keyword",
                        "size": 10
                    }
                },
                "years": {
                    "terms": {
                        "field": "year",
                        "size": 5,
                        "order": {"_key": "desc"}
                    }
                }
            }
        }
        
        agg_response = requests.post(
            "http://localhost:9200/arxiv_papers/_search",
            json=agg_query,
            timeout=10
        )
        
        if count_response.status_code != 200 or agg_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Elasticsearch error")
        
        count_data = count_response.json()
        agg_data = agg_response.json()
        
        return {
            "total_papers": count_data.get("count", 0),
            "categories": [
                {"category": bucket["key"], "count": bucket["doc_count"]}
                for bucket in agg_data.get("aggregations", {}).get("categories", {}).get("buckets", [])
            ],
            "years": [
                {"year": bucket["key"], "count": bucket["doc_count"]}
                for bucket in agg_data.get("aggregations", {}).get("years", {}).get("buckets", [])
            ],
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Scientific Semantic Search API...")
    print("📡 API: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("🔍 Elasticsearch: http://localhost:9200")
    uvicorn.run(app, host="0.0.0.0", port=8000)
