$ErrorActionPreference = "Stop"
$root = Resolve-Path "$PSScriptRoot\..\.."

$services = @(
    @{ name = "auth";             context = "services\auth" }
    @{ name = "account";          context = "services\account" }
    @{ name = "transaction";      context = "services\transaction" }
    @{ name = "history";          context = "services\history" }
    @{ name = "card-management";  context = "services\card-management" }
    @{ name = "gateway";          context = "services\gateway" }
    @{ name = "background-load";  context = "services\background-load" }
    @{ name = "frontend";         context = "frontend" }
)

Write-Host ""
Write-Host "==> Building all ATM SRE images..." -ForegroundColor Cyan

foreach ($svc in $services) {
    $image = "atm-sre/$($svc.name):latest"
    $ctx   = Join-Path $root $svc.context
    Write-Host ""
    Write-Host "--- $image" -ForegroundColor Yellow
    docker build -t $image $ctx
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to build $image" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "==> All images built successfully." -ForegroundColor Green
