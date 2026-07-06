# stop_demo.ps1
# Stops uvicorn and node/vite processes associated with CampusGPT X

Write-Host "Stopping CampusGPT X development server processes..." -ForegroundColor Yellow

# Kill Uvicorn (FastAPI)
$uvicornProcs = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" }
if ($uvicornProcs) {
    $uvicornProcs | Stop-Process -Force
    Write-Host "  [+] Stopped Uvicorn process(es)." -ForegroundColor Green
} else {
    Write-Host "  [-] No active Uvicorn dev process found."
}

# Kill Node/Vite
$nodeProcs = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcs) {
    $nodeProcs | Stop-Process -Force
    Write-Host "  [+] Stopped Node/Vite process(es)." -ForegroundColor Green
} else {
    Write-Host "  [-] No active Node process found."
}

Write-Host "Cleanup completed successfully!" -ForegroundColor Green
