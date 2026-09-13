param(
    [switch]$SkipInno,
    [string]$CertificatePath,
    [string]$CertificatePassword,
    [string]$TimestampUrl
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot ".." )).Path
$dist = Join-Path $repo "dist\windows"
$entrypoints = Join-Path $repo "installer\entrypoints"

function Find-SignTool {
    $command = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    $kitsRoots = @(
        (Join-Path ${env:ProgramFiles(x86)} "Windows Kits\10\bin"),
        (Join-Path $env:ProgramFiles "Windows Kits\10\bin")
    )
    foreach ($kitsRoot in $kitsRoots) {
        if (Test-Path -LiteralPath $kitsRoot) {
            $candidate = Get-ChildItem -LiteralPath $kitsRoot -Filter signtool.exe -File -Recurse |
                Where-Object { $_.FullName -match "\\x64\\signtool\.exe$" } |
                Sort-Object FullName -Descending | Select-Object -First 1
            if ($candidate) { return $candidate.FullName }
        }
    }
    return $null
}

function Sign-Artifact([string]$Path, [string]$SignTool, [string]$Password) {
    $arguments = @("sign", "/f", $CertificatePath, "/fd", "SHA256", "/d", "MemoIdx", "/p", $Password)
    if ($TimestampUrl) { $arguments += @("/tr", $TimestampUrl, "/td", "SHA256") }
    $arguments += $Path
    & $SignTool @arguments
    if ($LASTEXITCODE -ne 0) { throw "Code signing failed for $Path with exit code $LASTEXITCODE" }
}

if ($CertificatePath) {
    if (-not (Test-Path -LiteralPath $CertificatePath -PathType Leaf)) {
        throw "Certificate file not found: $CertificatePath"
    }
    $signTool = Find-SignTool
    if (-not $signTool) {
        throw "signtool.exe is required when -CertificatePath is specified. Install the Windows SDK or put signtool.exe on PATH."
    }
    if (-not $CertificatePassword) {
        $securePassword = Read-Host "PFX password" -AsSecureString
        $CertificatePassword = [System.Net.NetworkCredential]::new('', $securePassword).Password
    }
}

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
    --collect-data memoidx (Join-Path $entrypoints "memoidx_cli.py")
python -m PyInstaller --noconfirm --clean --onefile --name memoidx-init `
    --distpath $dist --workpath (Join-Path $repo "build\pyinstaller-init") `
    --specpath (Join-Path $repo "build\pyinstaller-init") `
    --collect-data memoidx (Join-Path $entrypoints "memoidx_init.py")

if ($CertificatePath) {
    Sign-Artifact (Join-Path $dist "memoidx.exe") $signTool $CertificatePassword
    Sign-Artifact (Join-Path $dist "memoidx-init.exe") $signTool $CertificatePassword
}

if (-not $SkipInno) {
    $isccPath = (Get-Command iscc -ErrorAction SilentlyContinue).Source
    if (-not $isccPath) {
        $isccPath = @(
            (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
            (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
            (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe")
        ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
    }
    if (-not $isccPath) {
        throw "Inno Setup is required to create install.exe. Install it or put iscc.exe on PATH."
    }
    & $isccPath (Join-Path $repo "installer\MemoIdx.iss")
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed with exit code $LASTEXITCODE" }
    if ($CertificatePath) {
        Sign-Artifact (Join-Path $repo "dist\installer\install.exe") $signTool $CertificatePassword
    }
}

Write-Host "Portable executables: $dist"
if (-not $SkipInno) { Write-Host "Installer: $(Join-Path $repo 'dist\installer\install.exe')" }
