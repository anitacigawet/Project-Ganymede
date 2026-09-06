$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$venvPath = Join-Path $projectRoot '.venv'

if (-not (Test-Path -LiteralPath $venvPath)) {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv $venvPath
        if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed (exit $LASTEXITCODE)." }
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv $venvPath
        if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed (exit $LASTEXITCODE)." }
    } else {
        throw 'Python 3.11 or newer was not found.'
    }
}

$python = Join-Path $venvPath 'Scripts\python.exe'
& $python -m pip install --disable-pip-version-check --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed (exit $LASTEXITCODE)." }
& $python -m pip install --disable-pip-version-check -r (Join-Path $projectRoot 'ganymede-backend\requirements.txt')
if ($LASTEXITCODE -ne 0) { throw "Backend dependency installation failed (exit $LASTEXITCODE)." }

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw 'Node.js 22 or newer and npm 10.5.1 or newer are required.'
}
Push-Location (Join-Path $projectRoot 'ganymede-ui')
try {
    & npm.cmd ci
    if ($LASTEXITCODE -ne 0) { throw "Frontend dependency installation failed (exit $LASTEXITCODE)." }
} finally {
    Pop-Location
}

Write-Host 'Project Ganymede dependencies are installed.'
Write-Host 'Run .\scripts\start.ps1 for the full local edition.'
Write-Host 'Run .\scripts\start.ps1 -Showcase for the deterministic showcase.'
