# Script PowerShell pour démarrer l'application Docker
# Encodage: UTF-8 with BOM

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  SCIENTIFIC SEMANTIC SEARCH - DOCKER STARTUP  " -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Etape 1 : Verifier Docker
Write-Host "[1/6] Verification de Docker..." -ForegroundColor Yellow
docker --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERREUR: Docker n'est pas installe ou ne fonctionne pas!" -ForegroundColor Red
    exit 1
}
Write-Host "SUCCESS: Docker detecte" -ForegroundColor Green
Write-Host ""

# Etape 2 : Nettoyer les anciens conteneurs
Write-Host "[2/6] Nettoyage des anciens conteneurs..." -ForegroundColor Yellow
docker-compose down -v 2>$null
Write-Host "SUCCESS: Nettoyage termine" -ForegroundColor Green
Write-Host ""

# Etape 3 : Construire les images
Write-Host "[3/6] Construction des images Docker..." -ForegroundColor Yellow
Write-Host "Cela peut prendre 10-15 minutes..." -ForegroundColor Cyan
docker-compose build --no-cache
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERREUR: Echec de la construction!" -ForegroundColor Red
    exit 1
}
Write-Host "SUCCESS: Images construites avec succes" -ForegroundColor Green
Write-Host ""

# Etape 4 : Demarrer les services
Write-Host "[4/6] Demarrage des services..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERREUR: Echec du demarrage!" -ForegroundColor Red
    exit 1
}
Write-Host "SUCCESS: Services demarres" -ForegroundColor Green
Write-Host ""

# Etape 5 : Attendre le demarrage
Write-Host "[5/6] Attente du demarrage des services (30s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Etape 6 : Verifier l'etat
Write-Host "[6/6] Etat des services:" -ForegroundColor Cyan
docker-compose ps
Write-Host ""

# Afficher les informations
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  SERVICES DISPONIBLES" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Elasticsearch:  http://localhost:9200" -ForegroundColor White
Write-Host "Backend API:    http://localhost:8000" -ForegroundColor White
Write-Host "API Docs:       http://localhost:8000/docs" -ForegroundColor White
Write-Host "Frontend:       http://localhost:3000" -ForegroundColor White
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Commandes utiles:" -ForegroundColor Yellow
Write-Host "  Voir les logs:        docker-compose logs -f" -ForegroundColor White
Write-Host "  Arreter:              docker-compose down" -ForegroundColor White
Write-Host "  Redemarrer:           docker-compose restart" -ForegroundColor White
Write-Host "  Logs d'un service:    docker-compose logs -f backend" -ForegroundColor White
Write-Host ""

# Tester les services
Write-Host "Test des services..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "Testing Elasticsearch..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9200" -TimeoutSec 5 -UseBasicParsing
    Write-Host "SUCCESS: Elasticsearch OK" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Elasticsearch en attente..." -ForegroundColor Yellow
}

Write-Host "Testing Backend API..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
    Write-Host "SUCCESS: Backend API OK" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Backend API en attente..." -ForegroundColor Yellow
}

Write-Host "Testing Frontend..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -UseBasicParsing
    Write-Host "SUCCESS: Frontend OK" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Frontend en attente..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Demarrage termine!" -ForegroundColor Green
Write-Host "Consultez la documentation sur http://localhost:8000/docs" -ForegroundColor Cyan