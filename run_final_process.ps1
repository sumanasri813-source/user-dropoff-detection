param(
    [switch]$SkipInstall
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

if (-not $SkipInstall) {
    Write-Host 'Installing dependencies...'
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
}

Write-Host 'Running database migration...'
python mlops/deployment/db/migrate.py

Write-Host 'Running core contract tests...'
python -m pytest tests/contract/test_predict_contract.py tests/contract/test_crud_operations.py -q

Write-Host 'Starting API server in the background...'
$env:APP_ENV = $env:APP_ENV
if (-not $env:APP_ENV) { $env:APP_ENV = 'dev' }
if (-not $env:API_KEY) { $env:API_KEY = 'dev-local-key' }

$logDir = Join-Path $repoRoot 'logs'
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

$stdoutLog = Join-Path $logDir 'demo_api.out.log'
$stderrLog = Join-Path $logDir 'demo_api.err.log'
$pidFile = Join-Path $logDir 'demo_api.pid'

if (Test-Path $pidFile) {
    $previousPid = (Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    if ($previousPid) {
        Stop-Process -Id $previousPid -Force -ErrorAction SilentlyContinue
    }
}

$apiProcess = Start-Process -FilePath 'python' -ArgumentList '-m src.api.app' -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog
Set-Content -Path $pidFile -Value $apiProcess.Id

Write-Host 'Waiting for health endpoint...'
$healthUrl = 'http://127.0.0.1:5000/health'
$headers = @{ 'X-API-Key' = $env:API_KEY }
$ready = $false
for ($attempt = 1; $attempt -le 30; $attempt++) {
    try {
        $response = Invoke-RestMethod -Uri $healthUrl -Headers $headers -Method Get -TimeoutSec 5
        if ($response) {
            $ready = $true
            break
        }
    }
    catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $ready) {
    Write-Host 'API did not become ready. Check logs/demo_api.err.log.'
    exit 1
}

Write-Host 'API is ready.'
Write-Host 'Health endpoint:'
$response | ConvertTo-Json -Depth 6
Write-Host ''
Write-Host 'Demo process complete. API is still running in the background.'
Write-Host "PID saved to $pidFile"
