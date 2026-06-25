# Gera o executável do Assistente Jarvis (Windows)
# Uso: .\build.ps1

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

function Get-Python {
    $candidates = @(
        "py",
        "python",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
    )
    foreach ($cmd in $candidates) {
        try {
            if ($cmd -match "\\") {
                if (Test-Path $cmd) { return $cmd }
            } else {
                $null = & $cmd --version 2>$null
                if ($LASTEXITCODE -eq 0) { return $cmd }
            }
        } catch {}
    }
    throw "Python não encontrado. Instale Python 3.12+ e tente novamente."
}

$Python = Get-Python
Write-Host "Python: $Python" -ForegroundColor Cyan

Write-Host "`n[1/4] Instalando dependências do backend..." -ForegroundColor Yellow
& $Python -m pip install -r "$Root\backend\requirements.txt" -q
& $Python -m pip install -r "$Root\backend\requirements-build.txt" -q

Write-Host "`n[2/4] Instalando dependências do frontend..." -ForegroundColor Yellow
Push-Location $Root
npm install
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }

Write-Host "`n[3/4] Gerando build do frontend (dist/)..." -ForegroundColor Yellow
npm run build
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

if (-not (Test-Path "$Root\dist\index.html")) {
    throw "Build do frontend falhou: dist\index.html não encontrado."
}

Write-Host "`n[4/4] Empacotando com PyInstaller..." -ForegroundColor Yellow
& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --distpath "$Root\release" `
    --workpath "$Root\build\jarvis-work" `
    "$Root\jarvis.spec"

if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "`nPronto! Executável gerado em:" -ForegroundColor Green
Write-Host "  $Root\release\Jarvis\Jarvis.exe" -ForegroundColor Green
Write-Host "`nDistribua a pasta inteira 'release\Jarvis' (não só o .exe)." -ForegroundColor Cyan
