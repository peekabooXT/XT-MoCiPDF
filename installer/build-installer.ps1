param(
    [string]$ISCC = 'ISCC.exe',
    [string]$Payload,
    [string]$Output,
    [string]$Version = '1.13.2'
)
$ErrorActionPreference = 'Stop'
$packageRoot = Split-Path -Parent $PSScriptRoot
if (-not $Payload) { $Payload = $packageRoot }
if (-not $Output) { $Output = Join-Path $packageRoot 'dist\installer' }
$Payload = (Resolve-Path -LiteralPath $Payload).Path
foreach ($file in @('XT阅迹.exe', '_internal\python312.dll', 'dictionary\ecdict.sqlite', 'tessdata\eng.traineddata', 'icon.ico')) {
    if (-not (Test-Path -LiteralPath (Join-Path $Payload $file))) { throw "Payload missing: $file" }
}
New-Item -ItemType Directory -Path $Output -Force | Out-Null
$Output = (Resolve-Path -LiteralPath $Output).Path
& $ISCC ("/DPayloadDir=$Payload") ("/DBuildVersion=$Version") ("/O$Output") (Join-Path $PSScriptRoot 'XT-ReadTrace.iss')
if ($LASTEXITCODE -ne 0) { throw 'Installer compilation failed' }
$installer = Join-Path $Output "XT-ReadTrace-$Version-Setup-x64.exe"
if (-not (Test-Path -LiteralPath $installer)) { throw 'Installer output missing' }
Write-Output "Installer ready: $installer"
