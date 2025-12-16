#!/usr/bin/env python3
"""
Enrichit les données avec plus d'informations depuis arXiv.
"""

import json
from pathlib import Path
import re
from datetime import datetime
from collections import Counter

def extract_year_from_id(arxiv_id):
    """Extrait l'année de publication depuis l'ID arXiv"""
    if not arxiv_id:
        return None
    
    # Format arXiv: YYMM.NNNNN ou YYMM.NNNNNvN
    try:
        if '.' in arxiv_id:
            year_part = arxiv_id.split('.')[0]
            if len(year_part) >= 4 and year_part.isdigit():
                year_two_digit = int(year_part[:2])
                # Supposition: après 2000
                if year_two_digit < 50:
                    return 2000 + year_two_digit
                else:
                    return 1900 + year_two_digit
    except:
        pass
    
    return None

def extract_month_from_id(arxiv_id):
    """Extrait le mois de publication depuis l'ID arXiv"""
    if not arxiv_id:
        return None
    
    try:
        if '.' in arxiv_id:
            month_part = arxiv_id.split('.')[0]
            if len(month_part) >= 4 and month_part.isdigit():
                month = int(month_part[2:4])
                if 1 <= month <= 12:
                    return month
    except:
        pass
    
    return None

def extract_main_category(categories):
    """Extrait la catégorie principale"""
    if not categories:
        return None
    
    # Préférer les catégories CS
    cs_categories = [cat for cat in categories if isinstance(cat, str) and cat.startswith('cs.')]
    if cs_categories:
        return cs_categories[0]
    
    # Sinon, prendre la première catégorie
    return categories[0] if categories else None

def extract_keywords_from_text(text, max_keywords=10):
    """Extrait les mots-clés les plus fréquents d'un texte"""
    if not text:
        return []
    
    # Tokenisation simple
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    
    # Liste de mots vides (stop words) en anglais
    stop_words = {
        'the', 'and', 'for', 'with', 'using', 'based', 'from', 'this', 'that',
        'which', 'have', 'been', 'were', 'will', 'can', 'could', 'would',
        'should', 'about', 'their', 'there', 'what', 'when', 'where', 'why',
        'how', 'then', 'than', 'also', 'more', 'most', 'less', 'least',
        'very', 'such', 'some', 'any', 'all', 'both', 'each', 'every',
        'these', 'those', 'other', 'another', 'same', 'different',
        'between', 'among', 'through', 'during', 'before', 'after',
        'above', 'below', 'under', 'over', 'into', 'onto', 'upon'
    }
    
    # Filtrer les stop words et les mots courts
    filtered_words = [word for word in words if word not in stop_words]
    
    # Compter les fréquences
    word_counter = Counter(filtered_words)
    
    # Retourner les mots-clés les plus fréquents
    return [word for word, _ in word_counter.most_common(max_keywords)]

def enhance_arxiv_data():
    """Enrichit les données arXiv avec plus d'informations"""
    data_dir = Path(__file__).parent.parent
    input_file = data_dir / "cleaned" / "cleaned_cs.json"
    output_file = data_dir / "cleaned" / "enhanced_cs.json"
    
    if not input_file.exists():
        print(f"❌ Fichier introuvable: {input_file}")
        return None
    
    print("📖 Chargement des données...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"🔍 Enrichissement de {len(data)} articles...")
    
    enhanced_data = []
    stats = {
        'with_year': 0,
        'with_month': 0,
        'with_main_category': 0,
        'with_keywords': 0
    }
    
    for i, article in enumerate(data):
        enhanced = article.copy()
        
        # Extraire l'année de publication
        year = extract_year_from_id(article.get('arxiv_id', ''))
        if year:
            enhanced['publication_year'] = year
            stats['with_year'] += 1
        
        # Extraire le mois de publication
        month = extract_month_from_id(article.get('arxiv_id', ''))
        if month:
            enhanced['publication_month'] = month
            stats['with_month'] += 1
        
        # Extraire la catégorie principale
        categories = article.get('categories', [])
        main_category = extract_main_category(categories)
        if main_category:
            enhanced['main_category'] = main_category
            stats['with_main_category'] += 1
        
        # Nombre d'auteurs
        authors = article.get('authors', [])
        if authors:
            enhanced['author_count'] = len(authors)
        
        # Statistiques de texte
        abstract = article.get('abstract', '')
        if abstract:
            enhanced['abstract_length'] = len(abstract)
            enhanced['abstract_word_count'] = len(abstract.split())
            
            # Extraire les mots-clés du résumé
            keywords = extract_keywords_from_text(abstract, max_keywords=5)
            if keywords:
                enhanced['abstract_keywords'] = keywords
                stats['with_keywords'] += 1
        
        # Mots-clés du titre
        title = article.get('title', '')
        if title:
            title_keywords = extract_keywords_from_text(title, max_keywords=3)
            if title_keywords:
                enhanced['title_keywords'] = title_keywords
        
        # Date de mise à jour
        enhanced['last_updated'] = datetime.now().isoformat()
        
        # Source
        enhanced['source'] = 'arXiv'
        
        enhanced_data.append(enhanced)
        
        if (i + 1) % 100 == 0:
            print(f"  ✓ {i + 1}/{len(data)} articles traités")
    
    # Sauvegarder
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Données enrichies sauvegardées: {output_file}")
    print(f"📊 Statistiques d'enrichissement:")
    print(f"   - Articles avec année: {stats['with_year']}/{len(data)} ({stats['with_year']/len(data)*100:.1f}%)")
    print(f"   - Articles avec mois: {stats['with_month']}/{len(data)} ({stats['with_month']/len(data)*100:.1f}%)")
    print(f"   - Articles avec catégorie principale: {stats['with_main_category']}/{len(data)} ({stats['with_main_category']/len(data)*100:.1f}%)")
    print(f"   - Articles avec mots-clés: {stats['with_keywords']}/{len(data)} ({stats['with_keywords']/len(data)*100:.1f}%)")
    
    # Afficher un échantillon
    print("\n📋 Exemple d'article enrichi:")
    if enhanced_data:
        sample = enhanced_data[0]
        print(f"   Titre: {sample.get('title', '')[:60]}...")
        print(f"   Année: {sample.get('publication_year', 'N/A')}")
        print(f"   Catégorie principale: {sample.get('main_category', 'N/A')}")
        print(f"   Mots-clés: {', '.join(sample.get('abstract_keywords', []))}")
    
    return enhanced_data

if __name__ == "__main__":
    print("🔄 ENRICHISSEMENT DES DONNÉES ARXIV")
    print("=" * 50)
    result = enhance_arxiv_data()
    print(f"\n✨ Enrichissement terminé! {len(result) if result else 0} articles enrichis.")
