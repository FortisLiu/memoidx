param(
    [switch]$SkipInno
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot ".." )).Path
$dist = Join-Path $repo "dist\windows"
$entrypoints = Join-Path $repo "installer\entrypoints"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python is required only to build the installer. End users do not need Python."
}

python -m pip install --upgrade pyinstaller
if (Test-Path -LiteralPath $dist) {
    Remove-Item -LiteralPath $dist -Recurse -Force
}
New-Item -ItemType Directory -Path $dist | Out-Null

python -m PyInstaller --noconfirm --clean --onefile --name memoidx `
    --distpath $dist --workpath (Join-Path $repo "build\pyinstaller") `
    --specpath (Join-Path $repo "build\pyinstaller") `
    --collect-data memoidx (Join-Path $entrypoints "memoidx.py")
python -m PyInstaller --noconfirm --clean --onefile --name memoidx-init `
    --distpath $dist --workpath (Join-Path $repo "build\pyinstaller-init") `
    --specpath (Join-Path $repo "build\pyinstaller-init") `
    --collect-data memoidx (Join-Path $entrypoints "memoidx_init.py")

if (-not $SkipInno) {
    $iscc = Get-Command iscc -ErrorAction SilentlyContinue
    if (-not $iscc) {
        throw "Inno Setup is required to create install.exe. Install it, then rerun with iscc on PATH."
    }
    & $iscc.Source (Join-Path $repo "installer\MemoIdx.iss")
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed with exit code $LASTEXITCODE" }
}

Write-Host "Portable executables: $dist"
if (-not $SkipInno) { Write-Host "Installer: $(Join-Path $repo 'dist\installer\MemoIdx-Setup.exe')" }
