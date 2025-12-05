import numpy as np
import pandas as pd
from ai.embeddings.sentence_bert_handler import SentenceBERTHandler

def generate_article_embeddings(input_file, output_file):
    """
    - Charge le dataset nettoyé
    - Concatène title + abstract
    - Génère les embeddings SBERT
    - Sauvegarde en .npy
    """
    print("📥 Loading cleaned dataset:", input_file)
    df = pd.read_json(input_file)

    model = SentenceBERTHandler()
    texts = (df["title"] + " " + df["abstract"]).tolist()

    print("🧠 Generating embeddings...")
    embeddings = model.encode(texts)

    print("💾 Saving embeddings:", output_file)
    np.save(output_file, embeddings)

    print("✔ Embeddings saved successfully!")
    return embeddings
