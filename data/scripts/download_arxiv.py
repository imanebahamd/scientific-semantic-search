#!/usr/bin/env python3
"""
Télécharge les articles scientifiques de l'API arXiv.
Permet de télécharger par lots avec gestion d'erreurs robuste.
"""

import os
import json
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import sys

# ----------------------------------------------------------
# Configuration
# ----------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
OUTPUT_FILE = DATA_DIR / "arxiv_cs.json"

# Créer les répertoires si nécessaire
RAW_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------
# Paramètres de l'API arXiv
# ----------------------------------------------------------
CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.NE", "cs.SE", "cs.CR", "cs.DC"]  # Catégories CS
TOTAL_RESULTS = 500  # Réduit pour tester, mettre 500 pour production
BATCH_SIZE = 100     # Taille des lots (arXiv recommande max 2000/jour)
RETRIES = 5          # Nombre de tentatives en cas d'échec
DELAY_BETWEEN_REQUESTS = 3  # Délai entre les requêtes (éviter le rate limiting)

BASE_URL = "http://export.arxiv.org/api/query"

print("=" * 60)
print("📡 Téléchargement d'articles scientifiques depuis arXiv")
print("=" * 60)

# ----------------------------------------------------------
# Fonctions utilitaires
# ----------------------------------------------------------
def safe_request(params, attempt=1):
    """
    Effectue une requête HTTP sécurisée avec gestion des erreurs.
    """
    if attempt > RETRIES:
        raise Exception(f"❌ Échec après {RETRIES} tentatives pour start={params.get('start', 0)}")
    
    try:
        print(f"   → Tentative {attempt}/{RETRIES}: start={params['start']}")
        response = requests.get(
            BASE_URL,
            params=params,
            timeout=180,  # Timeout long pour les gros lots
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        if response.status_code == 200:
            return response.text
        elif response.status_code == 429:  # Too Many Requests
            wait_time = 30 * attempt  # Backoff exponentiel
            print(f"⚠ Rate limit atteint. Attente de {wait_time} secondes...")
            time.sleep(wait_time)
            return safe_request(params, attempt + 1)
        else:
            print(f"⚠ HTTP Error {response.status_code}: {response.reason}")
            time.sleep(5)
            return safe_request(params, attempt + 1)
            
    except requests.exceptions.Timeout:
        print(f"⏳ Timeout, nouvelle tentative dans 10 secondes...")
        time.sleep(10)
        return safe_request(params, attempt + 1)
    except requests.exceptions.ConnectionError:
        print(f"🔌 Erreur de connexion, nouvelle tentative dans 15 secondes...")
        time.sleep(15)
        return safe_request(params, attempt + 1)
    except Exception as e:
        print(f"⚠ Erreur inattendue: {type(e).__name__}: {e}")
        time.sleep(5)
        return safe_request(params, attempt + 1)

def parse_arxiv_xml(xml_content, batch_num):
    """
    Parse le XML d'arXiv et extrait les informations des articles.
    """
    docs = []
    
    try:
        root = ET.fromstring(xml_content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        
        # Vérifier s'il y a des erreurs
        error = root.find("atom:error", ns)
        if error is not None:
            print(f"⚠ Erreur dans le XML du batch {batch_num}: {error.text}")
            return docs
        
        entries = root.findall("atom:entry", ns)
        if not entries:
            print(f"⚠ Batch {batch_num}: Aucune entrée trouvée dans le XML")
            return docs
        
        for entry in entries:
            try:
                # Titre (nettoyage)
                title_elem = entry.find("atom:title", ns)
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                
                # Résumé
                summary_elem = entry.find("atom:summary", ns)
                summary = summary_elem.text.strip() if summary_elem is not None and summary_elem.text else ""
                
                # Date de publication
                published_elem = entry.find("atom:published", ns)
                published = published_elem.text if published_elem is not None else ""
                
                # Auteurs
                authors = []
                for author in entry.findall("atom:author", ns):
                    name_elem = author.find("atom:name", ns)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text.strip())
                
                # ID arXiv
                id_elem = entry.find("atom:id", ns)
                arxiv_id = ""
                if id_elem is not None and id_elem.text:
                    # Extraire juste l'ID de l'URL
                    arxiv_id = id_elem.text.split("/")[-1].split("v")[0]
                
                # Catégories (subjects)
                categories = []
                for category in entry.findall("atom:category", ns):
                    if category.get("term"):
                        categories.append(category.get("term"))
                
                # Vérifier que l'article a au moins un titre et un résumé
                if title and summary and len(summary) > 50:  # Exclure les résumés trop courts
                    doc = {
                        "arxiv_id": arxiv_id,
                        "title": title.replace("\n", " "),
                        "abstract": summary.replace("\n", " "),
                        "published": published,
                        "authors": authors,
                        "categories": categories,
                        "source": "arXiv",
                        "batch": batch_num
                    }
                    docs.append(doc)
                    
            except Exception as e:
                print(f"   ⚠ Erreur lors du parsing d'une entrée: {e}")
                continue
        
        return docs
        
    except ET.ParseError as e:
        print(f"❌ Erreur de parsing XML pour le batch {batch_num}: {e}")
        # Sauvegarder le XML problématique pour débogage
        debug_file = RAW_DIR / f"arxiv_debug_batch_{batch_num}.xml"
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(xml_content[:1000])  # Sauvegarder juste le début
        return []
    except Exception as e:
        print(f"❌ Erreur inattendue lors du parsing batch {batch_num}: {e}")
        return []

# ----------------------------------------------------------
# Fonction principale
# ----------------------------------------------------------
def download_arxiv():
    """
    Télécharge les articles depuis arXiv par lots.
    """
    all_docs = []
    downloaded_count = 0
    start_time = time.time()
    
    print(f"📊 Catégories: {', '.join(CATEGORIES)}")
    print(f"📊 Nombre total cible: {TOTAL_RESULTS} articles")
    print(f"📊 Taille des lots: {BATCH_SIZE} articles")
    print(f"📊 Répertoire de sortie: {RAW_DIR}")
    print("-" * 60)
    
    # Construire la requête de recherche combinée
    search_query = " OR ".join([f"cat:{cat}" for cat in CATEGORIES])
    
    for start in range(0, TOTAL_RESULTS, BATCH_SIZE):
        batch_num = start // BATCH_SIZE + 1
        remaining = min(BATCH_SIZE, TOTAL_RESULTS - start)
        
        print(f"\n📦 Lot {batch_num}: {start+1}-{start+remaining}")
        
        params = {
            "search_query": search_query,
            "start": start,
            "max_results": BATCH_SIZE,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        
        try:
            # Récupérer les données XML
            xml_data = safe_request(params)
            
            # Sauvegarder le XML brut
            raw_file = RAW_DIR / f"arxiv_raw_{start}.xml"
            with open(raw_file, "w", encoding="utf-8") as f:
                f.write(xml_data)
            print(f"   💾 Fichier brut sauvegardé: {raw_file.name}")
            
            # Parser le XML
            batch_docs = parse_arxiv_xml(xml_data, batch_num)
            
            if batch_docs:
                all_docs.extend(batch_docs)
                downloaded_count += len(batch_docs)
                print(f"   ✅ {len(batch_docs)} articles extraits (Total: {downloaded_count})")
            else:
                print(f"   ⚠ Aucun article valide dans ce lot")
            
            # Sauvegarde intermédiaire toutes les 200 entrées
            if len(all_docs) > 0 and (start + BATCH_SIZE) % 200 == 0:
                temp_file = DATA_DIR / f"arxiv_intermediate_{start+BATCH_SIZE}.json"
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(all_docs, f, indent=2, ensure_ascii=False)
                print(f"   💾 Sauvegarde intermédiaire: {temp_file.name}")
            
            # Délai pour éviter le rate limiting
            if start + BATCH_SIZE < TOTAL_RESULTS:
                print(f"   ⏳ Attente de {DELAY_BETWEEN_REQUESTS} secondes...")
                time.sleep(DELAY_BETWEEN_REQUESTS)
                
        except KeyboardInterrupt:
            print("\n⚠ Téléchargement interrompu par l'utilisateur.")
            break
        except Exception as e:
            print(f"❌ Erreur critique pour le lot {batch_num}: {e}")
            print("   Passage au lot suivant...")
            time.sleep(10)
            continue
    
    # ----------------------------------------------------------
    # Sauvegarde finale
    # ----------------------------------------------------------
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DU TÉLÉCHARGEMENT")
    print("=" * 60)
    print(f"Articles téléchargés: {downloaded_count}/{TOTAL_RESULTS}")
    print(f"Durée totale: {elapsed_time:.1f} secondes")
    print(f"Articles par seconde: {downloaded_count/elapsed_time:.2f}")
    
    if all_docs:
        # Supprimer les doublons basés sur arXiv_id
        unique_docs = []
        seen_ids = set()
        
        for doc in all_docs:
            if doc["arxiv_id"] and doc["arxiv_id"] not in seen_ids:
                seen_ids.add(doc["arxiv_id"])
                unique_docs.append(doc)
        
        # Statistiques par catégorie
        category_stats = {}
        for doc in unique_docs:
            for cat in doc["categories"]:
                if cat.startswith("cs."):
                    category_stats[cat] = category_stats.get(cat, 0) + 1
        
        print(f"\n📈 Répartition par catégorie:")
        for cat, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {cat}: {count} articles")
        
        # Sauvegarder en JSON
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(unique_docs, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Données sauvegardées dans: {OUTPUT_FILE}")
        
        # Créer également un fichier simplifié pour le nettoyage
        simplified_docs = [
            {
                "title": doc["title"],
                "abstract": doc["abstract"],
                "arxiv_id": doc["arxiv_id"],
                "categories": doc["categories"]
            }
            for doc in unique_docs
        ]
        
        simplified_file = DATA_DIR / "arxiv_simplified.json"
        with open(simplified_file, "w", encoding="utf-8") as f:
            json.dump(simplified_docs, f, indent=2, ensure_ascii=False)
        
        print(f"📁 Version simplifiée: {simplified_file}")
        
        # Générer un rapport
        report_file = DATA_DIR / "download_report.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"Rapport de téléchargement arXiv - {datetime.now()}\n")
            f.write("=" * 50 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total articles: {len(unique_docs)}\n")
            f.write(f"Durée: {elapsed_time:.1f}s\n")
            f.write(f"Taux: {len(unique_docs)/elapsed_time:.2f} articles/s\n\n")
            f.write("Catégories:\n")
            for cat, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
                f.write(f"  {cat}: {count}\n")
        
        print(f"📄 Rapport généré: {report_file}")
        
        return unique_docs
        
    else:
        print("❌ Aucun article téléchargé. Vérifiez votre connexion ou les paramètres.")
        return None

# ----------------------------------------------------------
# Fonction de secours : données d'exemple
# ----------------------------------------------------------
def create_sample_data():
    """
    Crée des données d'exemple si le téléchargement échoue.
    """
    print("\n🔄 Création de données d'exemple...")
    
    sample_docs = [
        {
            "arxiv_id": "1706.03762",
            "title": "Attention Is All You Need",
            "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.",
            "published": "2017-06-12T00:00:00Z",
            "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit", "Llion Jones", "Aidan N. Gomez", "Łukasz Kaiser", "Illia Polosukhin"],
            "categories": ["cs.CL", "cs.LG", "cs.AI"],
            "source": "sample",
            "batch": 0
        },
        {
            "arxiv_id": "1810.04805",
            "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
            "abstract": "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers. As a result, the pre-trained BERT model can be fine-tuned with just one additional output layer to create state-of-the-art models for a wide range of tasks, such as question answering and language inference, without substantial task-specific architecture modifications.",
            "published": "2018-10-11T00:00:00Z",
            "authors": ["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee", "Kristina Toutanova"],
            "categories": ["cs.CL", "cs.AI"],
            "source": "sample",
            "batch": 0
        },
        {
            "arxiv_id": "2005.14165",
            "title": "Language Models are Few-Shot Learners",
            "abstract": "Recent work has demonstrated substantial gains on many NLP tasks and benchmarks by pre-training on a large corpus of text followed by fine-tuning on the specific task. While typically task-agnostic in architecture, this method still requires task-specific fine-tuning datasets of thousands or tens of thousands of examples. By contrast, humans can generally perform a new language task from only a few examples or from simple instructions - something which current NLP systems still largely struggle to do. Here we show that scaling up language models greatly improves task-agnostic, few-shot performance, sometimes even reaching competitiveness with prior state-of-the-art fine-tuning approaches.",
            "published": "2020-05-28T00:00:00Z",
            "authors": ["Tom B. Brown", "Benjamin Mann", "Nick Ryder", "Melanie Subbiah", "Jared Kaplan", "Prafulla Dhariwal", "Arvind Neelakantan", "Pranav Shyam", "Girish Sastry", "Amanda Askell"],
            "categories": ["cs.CL", "cs.LG", "cs.AI"],
            "source": "sample",
            "batch": 0
        },
        {
            "arxiv_id": "2106.04566",
            "title": "Learning Transferable Visual Models From Natural Language Supervision",
            "abstract": "State-of-the-art computer vision systems are trained to predict a fixed set of predetermined object categories. This restricted form of supervision limits their generality and usability since additional labeled data is needed to specify any other visual concept. Learning directly from raw text about images is a promising alternative which leverages a much broader source of supervision. We demonstrate that the simple pre-training task of predicting which caption goes with which image is an efficient and scalable way to learn SOTA image representations from scratch on a dataset of 400 million (image, text) pairs collected from the internet.",
            "published": "2021-06-08T00:00:00Z",
            "authors": ["Alec Radford", "Jong Wook Kim", "Chris Hallacy", "Aditya Ramesh", "Gabriel Goh", "Sandhini Agarwal", "Girish Sastry", "Amanda Askell", "Pamela Mishkin", "Jack Clark"],
            "categories": ["cs.CV", "cs.LG", "cs.CL"],
            "source": "sample",
            "batch": 0
        },
        {
            "arxiv_id": "1910.10683",
            "title": "Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer",
            "abstract": "Transfer learning, where a model is first pre-trained on a data-rich task before being fine-tuned on a downstream task, has emerged as a powerful technique in natural language processing (NLP). The effectiveness of transfer learning has given rise to a diversity of approaches, methodology, and practice. In this paper, we explore the landscape of transfer learning techniques for NLP by introducing a unified framework that converts every language problem into a text-to-text format. Our systematic study compares pre-training objectives, architectures, unlabeled datasets, transfer approaches, and other factors on dozens of language understanding tasks.",
            "published": "2019-10-23T00:00:00Z",
            "authors": ["Colin Raffel", "Noam Shazeer", "Adam Roberts", "Katherine Lee", "Sharan Narang", "Michael Matena", "Yanqi Zhou", "Wei Li", "Peter J. Liu"],
            "categories": ["cs.CL", "cs.LG"],
            "source": "sample",
            "batch": 0
        }
    ]
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(sample_docs, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Données d'exemple créées: {OUTPUT_FILE}")
    return sample_docs

# ----------------------------------------------------------
# Point d'entrée
# ----------------------------------------------------------
if __name__ == "__main__":
    try:
        result = download_arxiv()
        if not result:
            create_sample_data()
    except KeyboardInterrupt:
        print("\n\n⏹ Téléchargement arrêté par l'utilisateur.")
        create_sample_data()
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        print("Création de données d'exemple...")
        create_sample_data()
    
    print("\n✨ Script terminé!")
