from sklearn.cluster import KMeans
import numpy as np

def cluster_embeddings(embeddings_file, n_clusters=10):
    """
    Applique K-Means pour regrouper les articles par thèmes
    """
    print("📥 Loading embeddings:", embeddings_file)
    embeddings = np.load(embeddings_file)

    print(f"🧪 Running KMeans with {n_clusters} clusters...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    labels = kmeans.fit_predict(embeddings)

    print("✔ Clustering done.")
    return labels
