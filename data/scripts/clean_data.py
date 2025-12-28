#!/usr/bin/env python3
"""
Nettoie les données arXiv téléchargées.
Convertit les fichiers XML bruts en JSON nettoyé.
"""

import json
from pathlib import Path
import xml.etree.ElementTree as ET
import re

# ----------------------------------------------------------
# Configuration
# ----------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CLEANED_DIR = DATA_DIR / "cleaned"

# Créer le répertoire cleaned s'il n'existe pas
CLEANED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = CLEANED_DIR / "cleaned_cs.json"

def clean_text(text):
    """
    Nettoie un texte en enlevant les espaces multiples et les sauts de ligne.
    """
    if not text:
        return ""
    
    # Remplacer les sauts de ligne et retours chariot
    text = text.replace('\n', ' ').replace('\r', ' ')
    
    # Remplacer les espaces multiples par un seul espace
    text = re.sub(r'\s+', ' ', text)
    
    # Supprimer les espaces en début et fin
    text = text.strip()
    
    return text

def clean_arxiv_xml(file_path):
    """
    Nettoie un fichier XML ArXiv.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        docs = []
        
        # Namespace pour arXiv
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        
        entries = root.findall("atom:entry", ns)
        print(f"    {len(entries)} entrées trouvées")
        
        for entry in entries:
            try:
                # Titre
                title_elem = entry.find("atom:title", ns)
                title = clean_text(title_elem.text) if title_elem is not None and title_elem.text else ""
                
                # Résumé
                summary_elem = entry.find("atom:summary", ns)
                abstract = clean_text(summary_elem.text) if summary_elem is not None and summary_elem.text else ""
                
                # ID arXiv
                id_elem = entry.find("atom:id", ns)
                arxiv_id = ""
                if id_elem is not None and id_elem.text:
                    arxiv_id = id_elem.text.split("/")[-1].split("v")[0]
                
                # Auteurs
                authors = []
                for author in entry.findall("atom:author", ns):
                    name_elem = author.find("atom:name", ns)
                    if name_elem is not None and name_elem.text:
                        authors.append(clean_text(name_elem.text))
                
                # Catégories
                categories = []
                for category in entry.findall("atom:category", ns):
                    if category.get("term"):
                        categories.append(category.get("term"))
                
                # Date de publication
                published_elem = entry.find("atom:published", ns)
                published = published_elem.text if published_elem is not None else ""
                
                if title and abstract and len(abstract) > 50:  # Ne garder que les documents complets
                    doc = {
                        "arxiv_id": arxiv_id,
                        "title": title,
                        "abstract": abstract,
                        "authors": authors,
                        "categories": categories,
                        "published": published,
                        "source_file": file_path.name
                    }
                    docs.append(doc)
                    
            except Exception as e:
                print(f"    ⚠ Erreur avec une entrée: {e}")
                continue
        
        return docs
    except Exception as e:
        print(f"❌ Erreur avec {file_path.name}: {e}")
        return []

def create_sample_data():
    """
    Crée des données d'exemple si aucun fichier XML n'existe.
    """
    print("📝 Aucun fichier XML trouvé dans data/raw/")
    print("💡 Création de données d'exemple...")
    
    sample_docs = [
        {
            "arxiv_id": "1706.03762",
            "title": "Attention Is All You Need",
            "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.",
            "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
            "categories": ["cs.CL", "cs.LG"],
            "published": "2017-06-12T00:00:00Z"
        },
        {
            "arxiv_id": "1810.04805",
            "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
            "abstract": "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers. As a result, the pre-trained BERT model can be fine-tuned with just one additional output layer to create state-of-the-art models for a wide range of tasks, such as question answering and language inference, without substantial task-specific architecture modifications.",
            "authors": ["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee"],
            "categories": ["cs.CL"],
            "published": "2018-10-11T00:00:00Z"
        }
    ]
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(sample_docs, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Données d'exemple créées: {OUTPUT_FILE}")
    return sample_docs

def clean_from_json(input_file):
    """
    Nettoie les données à partir d'un fichier JSON déjà téléchargé.
    """
    try:
        print(f"  Lecture de {input_file.name}...")
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        cleaned_docs = []
        
        for i, doc in enumerate(data):
            if isinstance(doc, dict):
                # Extraire les champs nécessaires
                title = clean_text(doc.get("title", doc.get("Title", "")))
                abstract = clean_text(doc.get("abstract", doc.get("abstract", doc.get("summary", ""))))
                arxiv_id = doc.get("arxiv_id", doc.get("id", f"doc_{i}"))
                authors = doc.get("authors", [])
                categories = doc.get("categories", [])
                published = doc.get("published", "")
                
                if title and abstract and len(abstract) > 50:
                    cleaned_docs.append({
                        "arxiv_id": arxiv_id,
                        "title": title,
                        "abstract": abstract,
                        "authors": authors if isinstance(authors, list) else [],
                        "categories": categories if isinstance(categories, list) else [],
                        "published": published
                    })
        
        print(f"✅ Nettoyé {len(cleaned_docs)} documents depuis {input_file.name}")
        return cleaned_docs
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage depuis JSON: {e}")
        return []

def main():
    """
    Nettoie tous les fichiers XML dans data/raw ou crée des données d'exemple.
    """
    print("=" * 60)
    print("🧹 Nettoyage des données arXiv")
    print("=" * 60)
    
    all_docs = []
    
    # Option 1: Nettoyer depuis les fichiers XML dans raw/
    xml_files = list(RAW_DIR.glob("*.xml"))
    
    if xml_files:
        print(f"📁 Trouvé {len(xml_files)} fichiers XML dans {RAW_DIR}")
        
        for xml_file in xml_files:
            print(f"  Traitement de {xml_file.name}...")
            docs = clean_arxiv_xml(xml_file)
            all_docs.extend(docs)
            print(f"    {len(docs)} documents extraits")
    
    # Option 2: Vérifier si un fichier JSON existe déjà (arxiv_cs.json)
    json_file = DATA_DIR / "arxiv_cs.json"
    if json_file.exists():
        print(f"\n📁 Fichier JSON trouvé: {json_file.name}")
        json_docs = clean_from_json(json_file)
        if json_docs:
            all_docs.extend(json_docs)
    
    # Option 3: Vérifier le fichier simplifié
    simplified_file = DATA_DIR / "arxiv_simplified.json"
    if simplified_file.exists():
        print(f"\n📁 Fichier simplifié trouvé: {simplified_file.name}")
        simplified_docs = clean_from_json(simplified_file)
        if simplified_docs:
            all_docs.extend(simplified_docs)
    
    if all_docs:
        # Supprimer les doublons basés sur arXiv_id
        unique_docs = []
        seen_ids = set()
        
        for doc in all_docs:
            doc_id = doc.get("arxiv_id", "")
            if doc_id and doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_docs.append(doc)
        
        print(f"\n📊 Après déduplication: {len(unique_docs)} documents uniques")
        
        # Statistiques par catégorie
        category_stats = {}
        for doc in unique_docs:
            for cat in doc.get("categories", []):
                if isinstance(cat, str) and cat.startswith("cs."):
                    category_stats[cat] = category_stats.get(cat, 0) + 1
        
        print("\n📈 Répartition par catégorie (top 10):")
        for cat, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {cat}: {count} articles")
        
        # Sauvegarder
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(unique_docs, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ {len(unique_docs)} documents nettoyés et sauvegardés")
        print(f"📁 Fichier de sortie: {OUTPUT_FILE}")
        
        # Afficher quelques exemples
        print("\n📋 Exemples de documents nettoyés:")
        for i, doc in enumerate(unique_docs[:3]):
            print(f"   {i+1}. {doc['title'][:60]}...")
            print(f"      ID: {doc.get('arxiv_id', 'N/A')}")
            print(f"      Catégories: {', '.join(doc.get('categories', [])[:3])}")
            print()
        
        return unique_docs
        
    else:
        print(f"⚠ Aucun document nettoyé")
        print("💡 Création de données d'exemple...")
        return create_sample_data()

if __name__ == "__main__":
    result = main()
    print(f"\n✨ Nettoyage terminé! {len(result) if result else 0} documents disponibles.")
