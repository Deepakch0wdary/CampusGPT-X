Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "CampusGPT X - Foundation Workspace Installer" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Check Node
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVer = node -v
    Write-Host "[✔] Node.js is installed ($nodeVer)" -ForegroundColor Green
} else {
    Write-Warning "[✘] Node.js not detected. Please install Node.js from https://nodejs.org"
}

# 2. Check Python
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pyVer = python --version
    Write-Host "[✔] Python is installed ($pyVer)" -ForegroundColor Green
} else {
    Write-Warning "[✘] Python not detected. Please install Python 3.11+ from https://python.org and make sure to check 'Add Python to PATH'"
}

# 3. Check Git
if (Get-Command git -ErrorAction SilentlyContinue) {
    $gitVer = git --version
    Write-Host "[✔] Git is installed ($gitVer)" -ForegroundColor Green
} else {
    Write-Warning "[✘] Git not detected. Please install Git from https://git-scm.com"
}

# 4. Install Workspace Dependencies
Write-Host "`n[i] Installing npm workspace dependencies..." -ForegroundColor Yellow
npm install

# 5. Instructions
Write-Host "`nSetup complete! To run the application:" -ForegroundColor Green
Write-Host "1. Start Docker services: docker compose up -d db"
Write-Host "2. Sync database schema: npx prisma db push"
Write-Host "3. Start Python backend: cd apps/backend ; python -m venv venv ; .\\venv\\Scripts\\activate ; pip install -r requirements.txt ; uvicorn app.main:app --reload"
Write-Host "4. Start Frontend UI: npm run dev:frontend"
Write-Host "==========================================" -ForegroundColor Cyan
