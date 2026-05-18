$ErrorActionPreference = "Stop"
$root = Resolve-Path "$PSScriptRoot\..\.."

$images = @(
    @{ name = "auth";            context = "services\auth" }
    @{ name = "account";         context = "services\account" }
    @{ name = "transaction";     context = "services\transaction" }
    @{ name = "history";         context = "services\history" }
    @{ name = "card-management"; context = "services\card-management" }
    @{ name = "gateway";         context = "services\gateway" }
    @{ name = "background-load"; context = "services\background-load" }
    @{ name = "frontend";        context = "frontend" }
)

Write-Host ""
Write-Host "==> Step 1: Building images..." -ForegroundColor Cyan

foreach ($svc in $images) {
    $image = "atm-sre/$($svc.name):latest"
    $ctx   = Join-Path $root $svc.context
    Write-Host "--- Building $image" -ForegroundColor Yellow
    docker build -t $image $ctx
    if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: build failed for $image" -ForegroundColor Red; exit 1 }
}

Write-Host ""
Write-Host "==> Step 2: Loading images into kind cluster..." -ForegroundColor Cyan

foreach ($svc in $images) {
    $image = "atm-sre/$($svc.name):latest"
    Write-Host "--- Loading $image" -ForegroundColor Yellow
    kind load docker-image $image
    if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: kind load failed for $image" -ForegroundColor Red; exit 1 }
}

Write-Host ""
Write-Host "==> Step 3: Pulling and loading infrastructure images..." -ForegroundColor Cyan

$infra = @(
    "postgres:15-alpine"
    "redis:7-alpine"
    "mongo:7"
    "prom/prometheus:v2.51.2"
    "grafana/grafana:10.4.2"
    "nginx:alpine"
)

foreach ($img in $infra) {
    Write-Host "--- $img" -ForegroundColor Yellow
    docker pull $img
    kind load docker-image $img
}


Write-Host ""
Write-Host "==> Step 4: Deploying to Kubernetes..." -ForegroundColor Cyan

kubectl apply -k "$root\orchestration\kubernetes"
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: kubectl apply failed" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "==> Step 5: Waiting for pods to start (60s)..." -ForegroundColor Cyan
Start-Sleep -Seconds 60
kubectl get pods -n atm-banking

Write-Host ""
Write-Host "==> Done! Access the app at:" -ForegroundColor Green
Write-Host "    Frontend:   http://localhost:30300"
Write-Host "    Gateway:    http://localhost:30800"
Write-Host "    Prometheus: http://localhost:30900"
Write-Host "    Grafana:    http://localhost:30309  (admin/admin)"
