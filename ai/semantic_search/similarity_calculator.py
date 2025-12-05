from sklearn.metrics.pairwise import cosine_similarity

def calculate_similarity(query_embedding, docs_embeddings):
    """
    Calcule la similarité cosinus entre la requête et tous les documents
    """
    sims = cosine_similarity([query_embedding], docs_embeddings)[0]
    return sims
