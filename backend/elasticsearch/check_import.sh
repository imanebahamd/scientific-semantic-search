#!/bin/bash
echo "🔍 VÉRIFICATION APRÈS IMPORTATION"
echo "=" * 50

echo -e "\n1. Elasticsearch:"
curl -s "http://localhost:9200/_cat/indices?v"

echo -e "\n2. Nombre de documents:"
curl -s "http://localhost:9200/arxiv_papers/_count" | python3 -c "
import json, sys
data = json.load(sys.stdin)
count = data['count']
print(f'   Documents: {count:,}')

if count > 1000:
    print('   ✅ Bon volume pour développement')
elif count > 5000:
    print('   🎉 Excellent volume!')
else:
    print('   ⚠ Volume modeste')
"

echo -e "\n3. Test API:"
echo "   Health check:"
curl -s "http://localhost:8000/health" | python3 -m json.tool | grep -A1 -B1 "elasticsearch"

echo -e "\n   Test recherche:"
curl -s "http://localhost:8000/search?query=deep+learning&size=2" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'     • Requête: {data[\"query\"]}')
print(f'     • Résultats: {data[\"total\"]}')
print(f'     • Temps: {data[\"execution_time\"]}')
"

echo -e "\n4. Performance:"
time curl -s "http://localhost:8000/search?query=test&size=1" > /dev/null

echo -e "\n✅ Vérification terminée!"
