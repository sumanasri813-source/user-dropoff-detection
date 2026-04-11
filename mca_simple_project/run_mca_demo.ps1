# ============================================================================
# MCA Student Project - One-Click Demo Runner
# ============================================================================
# This script automates the entire pipeline:
# 1. Sets up virtual environment
# 2. Installs dependencies
# 3. Auto-detects Python syntax errors
# 4. Generates synthetic data
# 5. Trains the model
# 6. Starts Flask API (port 5050)
# 7. Launches Streamlit dashboard (port 8501)
# ============================================================================

param(
    [switch]$SelfHeal,
    [int]$StartupRetries = 2,
    [int]$StartupWaitSeconds = 25
)

$ErrorActionPreference = "Stop"

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "MCA Student Project - Automated Demo Runner" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = $PSScriptRoot
$venvPython = Join-Path $projectRoot "venv\Scripts\python.exe"
$requirementsFile = Join-Path $projectRoot "requirements.txt"

if ($StartupRetries -lt 1) {
    $StartupRetries = 1
}

if ($StartupWaitSeconds -lt 5) {
    $StartupWaitSeconds = 5
}

function Exit-WithError {
    param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

function Find-SystemPython {
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) {
        return "py -3"
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        return "python"
    }

    return $null
}

function Test-UrlReachable {
    param(
        [string]$Url,
        [int]$TimeoutSec = 3
    )

    try {
        $null = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec $TimeoutSec
        return $true
    } catch {
        return $false
    }
}

function Wait-ForUrl {
    param(
        [string]$Url,
        [int]$WaitSeconds = 15
    )

    $endTime = (Get-Date).AddSeconds($WaitSeconds)
    while ((Get-Date) -lt $endTime) {
        if (Test-UrlReachable -Url $Url) {
            return $true
        }
        Start-Sleep -Seconds 1
    }
    return $false
}

function Start-ServiceWithRetry {
    param(
        [string]$ServiceName,
        [scriptblock]$StartAction,
        [scriptblock]$FallbackAction,
        [string]$HealthUrl,
        [int]$Attempts,
        [int]$WaitSeconds,
        [switch]$EnableRetry
    )

    $maxAttempts = if ($EnableRetry) { $Attempts } else { 1 }

    for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
        Write-Host "  - Starting $ServiceName (attempt $attempt/$maxAttempts)..."

        if ($attempt -eq 1 -or -not $EnableRetry -or -not $FallbackAction) {
            & $StartAction
        } else {
            Write-Host "    [INFO] Using self-heal fallback launcher for $ServiceName." -ForegroundColor Yellow
            & $FallbackAction
        }

        if (Wait-ForUrl -Url $HealthUrl -WaitSeconds $WaitSeconds) {
            Write-Host "    [OK] $ServiceName is reachable at $HealthUrl" -ForegroundColor Green
            return $true
        }

        Write-Host "    [WARN] $ServiceName did not become reachable in time." -ForegroundColor Yellow
    }

    return $false
}

Write-Host "Mode: $($(if ($SelfHeal) { 'Self-healing ON' } else { 'Normal mode' }))" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create/repair virtual environment
Write-Host "[STEP 1/6] Setting up Python virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path $venvPython)) {
    $pythonBootstrap = Find-SystemPython
    if (-not $pythonBootstrap) {
        Exit-WithError "Python is not installed or not on PATH. Install Python first."
    }

    Write-Host "  Creating virtual environment..."
    if ($pythonBootstrap -eq "py -3") {
        & py -3 -m venv (Join-Path $projectRoot "venv")
    } else {
        & python -m venv (Join-Path $projectRoot "venv")
    }

    if (-not (Test-Path $venvPython)) {
        Exit-WithError "Virtual environment creation failed."
    }
} else {
    Write-Host "  Virtual environment detected (reusing)."
}

# Step 2: Install dependencies using venv python directly
Write-Host "[STEP 2/6] Installing dependencies..." -ForegroundColor Yellow
& $venvPython -m pip install -q -r $requirementsFile
if ($LASTEXITCODE -ne 0) {
    Exit-WithError "Failed to install dependencies."
}
Write-Host "  Dependencies installed successfully."

# Step 3: Auto-detect syntax issues before runtime
Write-Host "[STEP 3/6] Checking Python files for syntax errors..." -ForegroundColor Yellow
$filesToCheck = @(
    (Join-Path $projectRoot "generate_data.py"),
    (Join-Path $projectRoot "train_model.py"),
    (Join-Path $projectRoot "api_app.py"),
    (Join-Path $projectRoot "dashboard_app.py")
)

& $venvPython -m py_compile $filesToCheck
if ($LASTEXITCODE -ne 0) {
    Exit-WithError "Syntax check failed. Fix the file shown above, then re-run this script."
}
Write-Host "  Syntax check passed."

# Step 4: Generate synthetic data
Write-Host "[STEP 4/6] Generating synthetic data..." -ForegroundColor Yellow
& $venvPython (Join-Path $projectRoot "generate_data.py")
if ($LASTEXITCODE -ne 0) {
    Exit-WithError "Failed to generate data."
}

# Step 5: Train model
Write-Host "[STEP 5/6] Training the ML model..." -ForegroundColor Yellow
& $venvPython (Join-Path $projectRoot "train_model.py")
if ($LASTEXITCODE -ne 0) {
    Exit-WithError "Failed to train model."
}

# Step 6: Start API and dashboard in separate windows
Write-Host "[STEP 6/6] Starting services..." -ForegroundColor Yellow
Write-Host "  - Launching Flask API (port 5050) in a new terminal..."

$apiScriptPath = Join-Path $env:TEMP "run_api_mca.ps1"
$apiScript = @"
Set-Location "$projectRoot"
Write-Host "Starting Flask API..." -ForegroundColor Green
& "$venvPython" "$projectRoot\api_app.py"
Write-Host "Flask API stopped." -ForegroundColor Yellow
Read-Host "Press Enter to close this window"
"@
$apiScript | Out-File -FilePath $apiScriptPath -Encoding UTF8
$apiStartAction = {
    Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-NoExit", "-File", $apiScriptPath | Out-Null
}
$apiFallbackAction = {
    Start-Process -FilePath $venvPython -WorkingDirectory $projectRoot -ArgumentList "$projectRoot\api_app.py" -WindowStyle Minimized | Out-Null
}

$apiStarted = Start-ServiceWithRetry -ServiceName "Flask API" -StartAction $apiStartAction -FallbackAction $apiFallbackAction -HealthUrl "http://127.0.0.1:5050/health" -Attempts $StartupRetries -WaitSeconds $StartupWaitSeconds -EnableRetry:$SelfHeal
if (-not $apiStarted) {
    Exit-WithError "Flask API startup failed after retry attempts."
}

Write-Host "  - Launching Streamlit dashboard (port 8501) in a new terminal..."
$dashScriptPath = Join-Path $env:TEMP "run_dashboard_mca.ps1"
$dashScript = @"
Set-Location "$projectRoot"
Write-Host "Starting Streamlit dashboard..." -ForegroundColor Green
& "$venvPython" -m streamlit run "$projectRoot\dashboard_app.py"
"@
$dashScript | Out-File -FilePath $dashScriptPath -Encoding UTF8
$dashboardStartAction = {
    Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-NoExit", "-File", $dashScriptPath | Out-Null
}
$dashboardFallbackAction = {
    Start-Process -FilePath $venvPython -WorkingDirectory $projectRoot -ArgumentList "-m", "streamlit", "run", "$projectRoot\dashboard_app.py" -WindowStyle Minimized | Out-Null
}

$dashboardStarted = Start-ServiceWithRetry -ServiceName "Streamlit Dashboard" -StartAction $dashboardStartAction -FallbackAction $dashboardFallbackAction -HealthUrl "http://127.0.0.1:8501" -Attempts $StartupRetries -WaitSeconds $StartupWaitSeconds -EnableRetry:$SelfHeal
if (-not $dashboardStarted) {
    Write-Host "WARNING: Streamlit dashboard did not pass reachability checks. You can still access the API and retry dashboard manually." -ForegroundColor Yellow
}

Start-Process "http://localhost:8501" | Out-Null

$apiReachable = Test-UrlReachable -Url "http://127.0.0.1:5050/health"
$dashboardReachable = Test-UrlReachable -Url "http://127.0.0.1:8501"

Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
if ($apiReachable -and $dashboardReachable) {
    Write-Host "DEMO STARTED SUCCESSFULLY!" -ForegroundColor Green
} else {
    Write-Host "DEMO STARTED WITH WARNINGS" -ForegroundColor Yellow
}
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services running:" -ForegroundColor Cyan
Write-Host "  Flask API:           http://localhost:5050/health" -ForegroundColor White
Write-Host "  Streamlit Dashboard: http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "Reachability checks:" -ForegroundColor Cyan
Write-Host "  API reachable:       $($(if ($apiReachable) { 'YES' } else { 'NO' }))" -ForegroundColor $(if ($apiReachable) { 'Green' } else { 'Red' })
Write-Host "  Dashboard reachable: $($(if ($dashboardReachable) { 'YES' } else { 'NO' }))" -ForegroundColor $(if ($dashboardReachable) { 'Green' } else { 'Red' })
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Use the opened dashboard in your browser" -ForegroundColor White
Write-Host "  2. Adjust sliders and click 'Predict Drop-Off Risk'" -ForegroundColor White
Write-Host "  3. Close the two service terminals when done" -ForegroundColor White
Write-Host ""
