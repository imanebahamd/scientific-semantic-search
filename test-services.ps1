# Script de test complet des services
# Encodage: UTF-8 with BOM

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  TEST DES SERVICES DOCKER" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$testsPassed = 0
$testsFailed = 0

function Test-Service {
    param (
        [string]$Name,
        [string]$Url,
        [int]$Timeout = 10
    )
    
    Write-Host "Testing $Name..." -NoNewline
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec $Timeout -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host " PASS" -ForegroundColor Green
            return $true
        } else {
            Write-Host " FAIL (Status: $($response.StatusCode))" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host " FAIL" -ForegroundColor Red
        return $false
    }
}

# Test 1 : Elasticsearch
Write-Host ""
Write-Host "TEST ELASTICSEARCH" -ForegroundColor Yellow
Write-Host "--------------------------------------------"
if (Test-Service "Elasticsearch Health" "http://localhost:9200") { $testsPassed++ } else { $testsFailed++ }
if (Test-Service "Cluster Health" "http://localhost:9200/_cluster/health") { $testsPassed++ } else { $testsFailed++ }

# Test 2 : Backend API
Write-Host ""
Write-Host "TEST BACKEND API" -ForegroundColor Yellow
Write-Host "--------------------------------------------"
if (Test-Service "Root Endpoint" "http://localhost:8000/") { $testsPassed++ } else { $testsFailed++ }
if (Test-Service "Health Check" "http://localhost:8000/health") { $testsPassed++ } else { $testsFailed++ }
if (Test-Service "Stats Endpoint" "http://localhost:8000/stats") { $testsPassed++ } else { $testsFailed++ }
if (Test-Service "Categories" "http://localhost:8000/categories") { $testsPassed++ } else { $testsFailed++ }

# Test 3 : Recherche
Write-Host ""
Write-Host "TEST RECHERCHE" -ForegroundColor Yellow
Write-Host "--------------------------------------------"
if (Test-Service "Text Search" "http://localhost:8000/search?query=machine+learning&k=5") { $testsPassed++ } else { $testsFailed++ }

# Test 4 : Frontend
Write-Host ""
Write-Host "TEST FRONTEND" -ForegroundColor Yellow
Write-Host "--------------------------------------------"
if (Test-Service "Frontend Page" "http://localhost:3000") { $testsPassed++ } else { $testsFailed++ }

# Resume
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  RESUME DES TESTS" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Tests reussis: $testsPassed" -ForegroundColor Green
Write-Host "Tests echoues: $testsFailed" -ForegroundColor Red
Write-Host "Total: $($testsPassed + $testsFailed)" -ForegroundColor White
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "Tous les tests sont passes!" -ForegroundColor Green
} else {
    Write-Host "Certains tests ont echoue. Verifiez les logs:" -ForegroundColor Yellow
    Write-Host "   docker-compose logs" -ForegroundColor White
}

Write-Host ""
Write-Host "Logs des services:" -ForegroundColor Yellow
Write-Host "  docker-compose logs elasticsearch" -ForegroundColor White
Write-Host "  docker-compose logs backend" -ForegroundColor White
Write-Host "  docker-compose logs frontend" -ForegroundColor White