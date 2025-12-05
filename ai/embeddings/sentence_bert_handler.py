from sentence_transformers import SentenceTransformer

class SentenceBERTHandler:
    """
    Wrapper pour SBERT afin d'encoder les textes en embeddings.
    """

    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        print(f"📌 Loading SBERT model: {model_name}")
        self.model = SentenceTransformer(model_name)

    def encode(self, texts):
        """
        Encode une liste de textes en embeddings NumPy (384 dims)
        """
        return self.model.encode(texts, convert_to_numpy=True)
