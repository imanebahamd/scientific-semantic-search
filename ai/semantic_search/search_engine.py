import numpy as np
import pandas as pd
from ai.semantic_search.similarity_calculator import calculate_similarity
from ai.embeddings.sentence_bert_handler import SentenceBERTHandler

class SemanticSearchEngine:

    def __init__(self, embeddings_file, df_file):
        print("📥 Loading embeddings:", embeddings_file)
        self.embeddings = np.load(embeddings_file)

        print("📥 Loading dataset:", df_file)
        self.df = pd.read_json(df_file)

        self.model = SentenceBERTHandler()

    def search(self, query, k=5, threshold=50, category=None, year_min=None):

        print(f"🔎 Searching top-{k} for:", query)

        query_emb = self.model.encode([query])[0]
        sims = calculate_similarity(query_emb, self.embeddings)

        top_k_idx = sims.argsort()[-k:][::-1]
        top_k_scores = sims[top_k_idx]

        scores_percent = ((top_k_scores + 1) / 2) * 100

        keep_idx = []
        keep_scores = []

        for idx, score in zip(top_k_idx, scores_percent):
            if score >= threshold:
                keep_idx.append(idx)
                keep_scores.append(score)

        if len(keep_idx) == 0:
            print("⚠ Aucun résultat pertinent trouvé.")
            return pd.DataFrame()

        results = self.df.iloc[keep_idx].copy()
        results["score_percent"] = keep_scores

        if category:
            results = results[results["categories"].apply(lambda cats: category in cats)]

        if year_min:
            results = results[results["year"] >= year_min]

        return results.reset_index(drop=True)
