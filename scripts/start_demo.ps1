# start_demo.ps1
# CampusGPT X Demo Startup Script

Clear-Host
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "          CAMPUSGPT X OS - DEMO STARTUP DESK            " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Prerequisite check
Write-Host "[1/5] Verifying System Prerequisites..." -ForegroundColor Yellow
$nodeVer = node -v 2>$null
$pythonVer = python --version 2>$null

if ($null -eq $nodeVer) {
    Write-Host "[-] Node.js is missing. Please install Node.js." -ForegroundColor Red
    Exit 1
}
if ($null -eq $pythonVer) {
    Write-Host "[-] Python is missing. Please install Python 3.11." -ForegroundColor Red
    Exit 1
}
Write-Host "  Node.js: $nodeVer"
Write-Host "  Python: $pythonVer"

# 2. Database check
Write-Host "[2/5] Checking Database Port Availability..." -ForegroundColor Yellow
$portCheck = Get-NetTCPConnection -LocalPort 3306 -ErrorAction SilentlyContinue
if ($null -eq $portCheck) {
    Write-Host "  [!] Port 3306 (MySQL) is offline. Database connection will be mocked/skipped." -ForegroundColor Magenta
    Write-Host "  To run with a live MySQL db, please start Docker desktop or local MySQL." -ForegroundColor Yellow
} else {
    Write-Host "  [+] Database port 3306 is active!" -ForegroundColor Green
}

# 3. Start Backend
Write-Host "[3/5] Starting FastAPI Backend..." -ForegroundColor Yellow
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd apps/backend; venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000" -WindowStyle Normal

# 4. Start Frontend
Write-Host "[4/5] Starting Vite Frontend..." -ForegroundColor Yellow
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "npm run dev:frontend" -WindowStyle Normal

# 5. Wait for readiness
Write-Host "[5/5] Waiting for servers to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host "          CAMPUSGPT X OS RUNNING SUCCESSFULLY!          " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  Frontend URL : http://localhost:5174/" -ForegroundColor Cyan
Write-Host "  Backend URL  : http://127.0.0.1:8000/" -ForegroundColor Cyan
Write-Host "  Swagger Docs : http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "  Health API   : http://127.0.0.1:8000/api/v1/health" -ForegroundColor Cyan
Write-Host "--------------------------------------------------------"
Write-Host "  Local Demo Accounts Configured (Demo password logic):" -ForegroundColor Yellow
Write-Host "  1. Master Admin        : admin.demo@campusgpt.local"
Write-Host "  2. Admission Officer   : admission.demo@campusgpt.local"
Write-Host "  3. Finance Officer     : finance.demo@campusgpt.local"
Write-Host "  4. Teacher             : teacher.demo@campusgpt.local"
Write-Host "  5. Student             : student.demo@campusgpt.local"
Write-Host "  6. Parent              : parent.demo@campusgpt.local"
Write-Host "========================================================" -ForegroundColor Green
Write-Host "Keep this window open to maintain backend/frontend loops."
