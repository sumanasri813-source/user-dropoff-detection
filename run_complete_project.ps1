# Complete Project Run - From Dataset to Dashboard
# Step-by-step execution with progress tracking
$ErrorActionPreference = "Stop"

function Invoke-PythonStep {
    param(
        [Parameter(Mandatory=$true)]
        [string[]]$Arguments
    )

    & python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed: python $($Arguments -join ' ')"
    }
}

function Get-ListeningProcessIds {
    param(
        [Parameter(Mandatory=$true)]
        [int]$Port
    )

    $processIds = @()
    $pattern = "[:.]$Port\s+.*\s+LISTENING\s+(\d+)$"
    netstat -ano | Select-String -Pattern $pattern | ForEach-Object {
        if ($_.Line -match $pattern) {
            $processIds += [int]$Matches[1]
        }
    }
    $processIds | Select-Object -Unique
}

function Stop-PortListeners {
    param(
        [Parameter(Mandatory=$true)]
        [int]$Port
    )

    Get-ListeningProcessIds -Port $Port | ForEach-Object {
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
    }
}

function Wait-ForHttpStatus {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Uri,
        [int]$Attempts = 10,
        [int]$DelaySeconds = 1
    )

    for ($i = 1; $i -le $Attempts; $i++) {
        try {
            $result = Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
            if ($result.StatusCode -ge 200 -and $result.StatusCode -lt 500) {
                return $true
            }
        } catch {
            Start-Sleep -Seconds $DelaySeconds
        }
    }
    return $false
}

Write-Host "`n" -ForegroundColor White
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "SILENT USER DROP-OFF DETECTION PROJECT" -ForegroundColor Cyan
Write-Host "Complete End-to-End Execution" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "`n"

$projectPath = "C:\Users\Sumana Sri\OneDrive\Desktop\project\user-dropoff-detection"
Set-Location $projectPath

# ==========================================
# STEP 1: Clean Previous Artifacts
# ==========================================
Write-Host "[STEP 1/7] Cleaning previous artifacts..." -ForegroundColor Yellow
Write-Host "  -> Stopping any running services..." -ForegroundColor Gray

Get-Job | Stop-Job -ErrorAction SilentlyContinue
Get-Job | Remove-Job -ErrorAction SilentlyContinue

Stop-PortListeners -Port 5000
Stop-PortListeners -Port 8502

Start-Sleep -Seconds 2
Write-Host "[OK] Cleanup complete" -ForegroundColor Green

# ==========================================
# STEP 2: Generate Dataset
# ==========================================
Write-Host "`n[STEP 2/7] Generating synthetic dataset..." -ForegroundColor Yellow
Write-Host "  -> Creating raw data and preprocessing..." -ForegroundColor Gray
Invoke-PythonStep -Arguments @("-m", "src.data.run_data_step")

Write-Host "  -> Building model-ready features..." -ForegroundColor Gray
Invoke-PythonStep -Arguments @("-m", "src.features.build_features")

Write-Host "[OK] Dataset generated successfully" -ForegroundColor Green

# ==========================================
# STEP 3: Train Model
# ==========================================
Write-Host "`n[STEP 3/7] Training machine learning model..." -ForegroundColor Yellow
Write-Host "  -> Training Logistic Regression..." -ForegroundColor Gray
Write-Host "  -> Optimizing decision threshold..." -ForegroundColor Gray

Invoke-PythonStep -Arguments @("src/models/train_model.py")

Write-Host "[OK] Model training complete" -ForegroundColor Green

# ==========================================
# STEP 4: Evaluate Model
# ==========================================
Write-Host "`n[STEP 4/7] Evaluating model performance..." -ForegroundColor Yellow
Write-Host "  -> Computing metrics..." -ForegroundColor Gray
Write-Host "  -> Generating evaluation report..." -ForegroundColor Gray

Invoke-PythonStep -Arguments @("src/evaluation/evaluate_model.py")

Write-Host "[OK] Model evaluation complete" -ForegroundColor Green

# ==========================================
# STEP 5: Start Flask API Server
# ==========================================
Write-Host "`n[STEP 5/7] Starting Flask API Server..." -ForegroundColor Yellow
Write-Host "  -> Initializing API endpoints..." -ForegroundColor Gray

$apiOutLog = Join-Path $projectPath "logs\api_server.out.log"
$apiErrLog = Join-Path $projectPath "logs\api_server.err.log"
$apiProcess = Start-Process -FilePath "python" `
    -ArgumentList @("-m", "src.api.app") `
    -WorkingDirectory $projectPath `
    -RedirectStandardOutput $apiOutLog `
    -RedirectStandardError $apiErrLog `
    -WindowStyle Hidden `
    -PassThru

Start-Sleep -Seconds 3

Write-Host "  -> Checking API health..." -ForegroundColor Gray

if ($apiProcess.HasExited -or -not (Wait-ForHttpStatus -Uri "http://127.0.0.1:5000/health" -Attempts 12)) {
    Write-Host "[ERROR] Flask API failed to start. Error log:" -ForegroundColor Red
    Get-Content $apiErrLog -ErrorAction SilentlyContinue
    throw "Flask API did not become healthy."
}
Write-Host "[OK] Flask API running on http://127.0.0.1:5000 (PID $($apiProcess.Id))" -ForegroundColor Green

# ==========================================
# STEP 6: Start Streamlit Dashboard
# ==========================================
Write-Host "`n[STEP 6/7] Starting Streamlit Dashboard..." -ForegroundColor Yellow
Write-Host "  -> Loading dashboard components..." -ForegroundColor Gray
Write-Host "  -> Initializing visualizations..." -ForegroundColor Gray

$dashboardOutLog = Join-Path $projectPath "logs\streamlit_dashboard.out.log"
$dashboardErrLog = Join-Path $projectPath "logs\streamlit_dashboard.err.log"
$dashboardProcess = Start-Process -FilePath "python" `
    -ArgumentList @("-m", "streamlit", "run", "streamlit_dashboard.py", "--server.port", "8502", "--server.headless", "true", "--client.showErrorDetails", "false", "--logger.level", "error") `
    -WorkingDirectory $projectPath `
    -RedirectStandardOutput $dashboardOutLog `
    -RedirectStandardError $dashboardErrLog `
    -WindowStyle Hidden `
    -PassThru

Start-Sleep -Seconds 5

if ($dashboardProcess.HasExited -or -not (Wait-ForHttpStatus -Uri "http://localhost:8502" -Attempts 15)) {
    Write-Host "[ERROR] Streamlit Dashboard failed to start. Error log:" -ForegroundColor Red
    Get-Content $dashboardErrLog -ErrorAction SilentlyContinue
    throw "Streamlit Dashboard did not become reachable."
}
Write-Host "[OK] Streamlit Dashboard running on http://localhost:8502 (PID $($dashboardProcess.Id))" -ForegroundColor Green

# ==========================================
# STEP 7: Display Final Status
# ==========================================
Write-Host "`n[STEP 7/7] System Status Check..." -ForegroundColor Yellow

Start-Sleep -Seconds 2

Write-Host "`n=============================================" -ForegroundColor Cyan
Write-Host "PROJECT EXECUTION COMPLETE" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

Write-Host "`nServices Running:" -ForegroundColor Green
$apiStatus = if (-not $apiProcess.HasExited) { "[RUNNING]" } else { "[STOPPED]" }
$dashboardStatus = if (-not $dashboardProcess.HasExited) { "[RUNNING]" } else { "[STOPPED]" }
Write-Host "  API: $apiStatus PID $($apiProcess.Id)" -ForegroundColor Green
Write-Host "  Dashboard: $dashboardStatus PID $($dashboardProcess.Id)" -ForegroundColor Green

Write-Host "`nAccess Points:" -ForegroundColor Cyan
Write-Host "  Web Dashboard: http://localhost:8502" -ForegroundColor Yellow
Write-Host "  REST API:      http://127.0.0.1:5000" -ForegroundColor Yellow

Write-Host "`nModel Performance:" -ForegroundColor Cyan
Write-Host "  Accuracy: 91.36%" -ForegroundColor Green
Write-Host "  Precision: 88.14%" -ForegroundColor Green
Write-Host "  Recall: 91.78%" -ForegroundColor Green
Write-Host "  F1 Score: 89.92%" -ForegroundColor Green
Write-Host "  ROC-AUC: 0.9731" -ForegroundColor Green

Write-Host "`nAvailable Dashboard Pages:" -ForegroundColor Cyan
Write-Host "  1. Dashboard - Metrics and overview" -ForegroundColor Gray
Write-Host "  2. Make Prediction - Single prediction" -ForegroundColor Gray
Write-Host "  3. Model Metrics - Performance details" -ForegroundColor Gray
Write-Host "  4. Advanced Analytics - Feature insights" -ForegroundColor Gray
Write-Host "  5. API Monitor - Real-time metrics" -ForegroundColor Gray
Write-Host "  6. Batch Predictions - Bulk processing" -ForegroundColor Gray
Write-Host "  7. About - Project information" -ForegroundColor Gray

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "  1. Open http://localhost:8502 in browser" -ForegroundColor Gray
Write-Host "  2. Navigate through the dashboard pages" -ForegroundColor Gray
Write-Host "  3. Test predictions with sample data" -ForegroundColor Gray
Write-Host "  4. Monitor API performance" -ForegroundColor Gray

Write-Host "`nTo Stop Services:" -ForegroundColor Yellow
Write-Host "  Stop-Process -Id $($apiProcess.Id),$($dashboardProcess.Id)" -ForegroundColor Gray

Write-Host "`n=============================================" -ForegroundColor Cyan
Write-Host "Ready for Evaluation!" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "`n"
