#!/bin/bash

echo "🚀 Configuration d'Elasticsearch pour Scientific Semantic Search"

# Créer l'index
echo "1. Création de l'index arxiv_papers..."
curl -X PUT "localhost:9200/arxiv_papers" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "title": {"type": "text"},
      "abstract": {"type": "text"},
      "authors": {"type": "keyword"},
      "categories": {"type": "keyword"},
      "year": {"type": "integer"},
      "primary_category": {"type": "keyword"},
      "date": {"type": "date"},
      "source": {"type": "keyword"}
    }
  }
}'

echo ""
echo "2. Ajout de documents de test..."

# Fonction pour ajouter un document
add_doc() {
    local id=$1
    local title=$2
    local abstract=$3
    local authors=$4
    local categories=$5
    local year=$6
    
    curl -X POST "localhost:9200/arxiv_papers/_doc/$id" -H 'Content-Type: application/json' -d"
    {
      \"title\": \"$title\",
      \"abstract\": \"$abstract\",
      \"authors\": [$authors],
      \"categories\": [$categories],
      \"year\": $year,
      \"primary_category\": \"${categories%,*}\",
      \"date\": \"$year-01-15\",
      \"source\": \"arXiv\"
    }" > /dev/null 2>&1
    
    echo "   ✅ Document $id ajouté"
}

# Ajouter plusieurs documents
add_doc "1" "Deep Learning for Natural Language Processing" "This paper explores deep learning techniques for NLP tasks." "\"Alex Johnson\", \"Sarah Miller\"" "\"cs.CL\", \"cs.LG\", \"cs.AI\"" "2023"

add_doc "2" "Transformer Models in Computer Vision" "Application of transformer architectures to computer vision problems." "\"Maria Garcia\", \"David Lee\"" "\"cs.CV\", \"cs.LG\"" "2024"

add_doc "3" "Machine Learning for Scientific Discovery" "Using ML to accelerate scientific research in various domains." "\"Robert Brown\"" "\"cs.LG\", \"stat.ML\"" "2023"

add_doc "4" "Reinforcement Learning in Robotics" "Survey of RL methods applied to robotic control tasks." "\"Wei Zhang\", \"Chen Li\"" "\"cs.RO\", \"cs.LG\"" "2024"

add_doc "5" "Federated Learning for Privacy-Preserving AI" "Federated learning enables training on decentralized data." "\"Sarah Taylor\"" "\"cs.LG\", \"cs.CR\"" "2024"

echo ""
echo "3. Vérification..."
sleep 2

echo "   📊 Nombre de documents:"
curl -s "localhost:9200/arxiv_papers/_count" | grep -o '"count":[0-9]*'

echo ""
echo "✅ Configuration terminée !"
echo "🌐 API: http://localhost:8000"
echo "🔍 Test: curl 'http://localhost:8000/search?query=machine+learning'"
