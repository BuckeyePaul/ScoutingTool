$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    throw 'Expected virtual environment at .venv. Create it first with: python -m venv .venv'
}

Write-Host 'Installing packaging dependencies...'
& $python -m pip install --upgrade pip | Out-Host
& $python -m pip install pyinstaller waitress flask requests beautifulsoup4 urllib3 | Out-Host

Write-Host 'Cleaning previous build artifacts...'
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $projectRoot 'build')
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $projectRoot 'dist')
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $projectRoot 'release')
Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $projectRoot 'ScoutingApp.spec')

Write-Host 'Building one-file executable...'
& $python -m PyInstaller `
    --noconfirm `
    --onefile `
    --name ScoutingApp `
    --add-data "templates;templates" `
    --add-data "static;static" `
    launcher.py | Out-Host

$releaseDir = Join-Path $projectRoot 'release\ScoutingApp'
New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null

Copy-Item (Join-Path $projectRoot 'dist\ScoutingApp.exe') -Destination (Join-Path $releaseDir 'ScoutingApp.exe') -Force
Copy-Item (Join-Path $projectRoot 'README.md') -Destination (Join-Path $releaseDir 'README.md') -Force

$runInstructions = @'
Double-click ScoutingApp.exe to launch the app.
The app opens at http://127.0.0.1:5000 in your browser.
Use the top-right "Stop App" button in the UI to shut down the process.
'@
Set-Content -Path (Join-Path $releaseDir 'RUN.txt') -Value $runInstructions -Encoding UTF8

$zipPath = Join-Path $projectRoot 'release\ScoutingApp-Windows.zip'
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}
Compress-Archive -Path (Join-Path $releaseDir '*') -DestinationPath $zipPath

Write-Host "Build complete: $zipPath"
