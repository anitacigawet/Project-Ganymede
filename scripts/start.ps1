param(
    [switch]$Showcase,
    [switch]$Lan
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$uiRoot = Join-Path $projectRoot 'ganymede-ui'
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$hostAddress = if ($Lan) { '0.0.0.0' } else { '127.0.0.1' }

if (-not (Test-Path -LiteralPath (Join-Path $uiRoot 'node_modules'))) {
    throw 'Frontend dependencies are not installed. Run .\scripts\setup.ps1 first.'
}

if ($Showcase) {
    Push-Location $uiRoot
    try {
        & npm.cmd run dev:showcase -- --hostname $hostAddress
    } finally {
        Pop-Location
    }
    exit $LASTEXITCODE
}

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw 'Dependencies are not installed. Run .\scripts\setup.ps1 first.'
}
Push-Location (Join-Path $projectRoot 'ganymede-backend')
try {
    & $python -m app.cli_preflight
    if ($LASTEXITCODE -ne 0) { throw 'Claude Code CLI preflight failed. See the error above.' }
} finally {
    Pop-Location
}

$backend = Start-Process -FilePath $python -ArgumentList @(
    '-m', 'uvicorn', 'app.main:app', '--host', $hostAddress, '--port', '8000'
) -WorkingDirectory (Join-Path $projectRoot 'ganymede-backend') -WindowStyle Hidden -PassThru

$frontend = $null
try {
    $frontend = Start-Process -FilePath 'npm.cmd' -ArgumentList @(
        'run', 'dev', '--', '--hostname', $hostAddress
    ) -WorkingDirectory $uiRoot -WindowStyle Hidden -PassThru

    Write-Host "Project Ganymede: http://$hostAddress`:3000"
    Write-Host 'Press Ctrl+C to stop both processes.'
    Wait-Process -Id $frontend.Id
} finally {
    foreach ($process in @($frontend, $backend)) {
        if ($process -and -not $process.HasExited) {
            Stop-Process -Id $process.Id -Force
        }
    }
}
