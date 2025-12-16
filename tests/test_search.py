import sys
sys.path.append('.')
from ai.semantic_search.search_engine import SemanticSearchEngine

# Initialiser
engine = SemanticSearchEngine()

# Recherches de test
queries = [
    "machine learning",
    "neural networks",
    "natural language processing",
    "computer vision",
    "deep learning"
]

for query in queries:
    print(f"\n🔍 Recherche: '{query}'")
    print("=" * 60)
    results = engine.search_with_scores(query, 3)
    if results:
        for i, r in enumerate(results, 1):
            print(f"{i}. Score: {r['score']:.4f}")
            print(f"   Titre: {r['title'][:70]}")
            if r['abstract']:
                print(f"   Résumé: {r['abstract'][:100]}...")
            print()
    else:
        print("❌ Aucun résultat trouvé")
