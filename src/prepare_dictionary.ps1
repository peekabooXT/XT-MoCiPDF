param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
$packageRoot = Split-Path -Parent $PSScriptRoot
$dictionaryRoot = Join-Path $packageRoot 'dictionary'
$databasePath = Join-Path $dictionaryRoot 'ecdict.sqlite'
if (Test-Path -LiteralPath $databasePath) { Write-Output 'Offline dictionary already available'; exit 0 }
$sourceInfo = Get-Content -LiteralPath (Join-Path $dictionaryRoot 'source.json') -Raw | ConvertFrom-Json
$sourceRoot = Join-Path $packageRoot 'work\dictionary-source'
New-Item -ItemType Directory -Path $sourceRoot -Force | Out-Null
$baseUrl = 'https://raw.githubusercontent.com/skywind3000/ECDICT/' + $sourceInfo.revision
$csvPath = Join-Path $sourceRoot 'ecdict.csv'
if (-not (Test-Path -LiteralPath $csvPath)) {
    Invoke-WebRequest -Uri ($baseUrl + '/ecdict.csv') -OutFile $csvPath
}
if ((Get-FileHash -LiteralPath $csvPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sourceInfo.csv_sha256) {
    throw 'ECDICT source checksum mismatch. Do not use this download.'
}
Copy-Item -LiteralPath (Join-Path $dictionaryRoot 'LICENSE.txt') -Destination (Join-Path $sourceRoot 'LICENSE') -Force
Copy-Item -LiteralPath (Join-Path $dictionaryRoot 'source.json') -Destination (Join-Path $sourceRoot 'source.json') -Force
& $Python (Join-Path $PSScriptRoot 'build_dictionary.py') $csvPath $dictionaryRoot
if ($LASTEXITCODE -ne 0) { throw 'Cannot build offline dictionary' }
