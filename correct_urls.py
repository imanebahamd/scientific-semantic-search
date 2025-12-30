with open('backend/api/routes_simple.py', 'r') as f:
    lines = f.readlines()

for i in range(len(lines)):
    line = lines[i]
    
    # 1. Corriger "ELASTICSEARCH_URL" seul (ligne 224)
    if '"ELASTICSEARCH_URL"' in line:
        lines[i] = line.replace('"ELASTICSEARCH_URL"', 'ELASTICSEARCH_URL')
    
    # 2. Corriger "ELASTICSEARCH_URL/..." (fichier comme ligne 292)
    elif '"ELASTICSEARCH_URL/' in line:
        lines[i] = line.replace('"ELASTICSEARCH_URL/', 'f"{ELASTICSEARCH_URL}/')
    
    # 3. Corriger f"ELASTICSEARCH_URL/... (ligne 469, 784)
    elif 'f"ELASTICSEARCH_URL/' in line:
        lines[i] = line.replace('f"ELASTICSEARCH_URL/', 'f"{ELASTICSEARCH_URL}/')
    
    # 4. Corriger 'ELASTICSEARCH_URL/... (si présent)
    elif "'ELASTICSEARCH_URL/" in line:
        lines[i] = line.replace("'ELASTICSEARCH_URL/", "f'{ELASTICSEARCH_URL}/")

with open('backend/api/routes_simple.py', 'w') as f:
    f.writelines(lines)

print("✅ Corrections appliquées !")
