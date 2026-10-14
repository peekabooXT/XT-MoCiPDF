# Run with a standalone Python 3.12+ installation (avoid Anaconda Qt DLL conflicts).
param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
$packageRoot = Split-Path -Parent $PSScriptRoot
$buildRoot = Join-Path $env:TEMP 'readtrace-build'
New-Item -ItemType Directory -Path $buildRoot -Force | Out-Null
& $Python -m venv (Join-Path $buildRoot 'venv')
if ($LASTEXITCODE -ne 0) { throw 'Cannot create Python environment' }
$pythonExe = Join-Path $buildRoot 'venv\Scripts\python.exe'
& $pythonExe -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Cannot install dependencies' }
& (Join-Path $PSScriptRoot 'prepare_dictionary.ps1') -Python $pythonExe
if ($LASTEXITCODE -ne 0) { throw 'Cannot prepare offline dictionary' }
& $pythonExe -m PyInstaller --noconfirm --clean --onedir --windowed --name 'XT阅迹' --version-file (Join-Path $PSScriptRoot 'version_info.txt') --icon (Join-Path $packageRoot 'icon.ico') --add-data "$(Join-Path $packageRoot 'tessdata');tessdata" --add-data "$(Join-Path $packageRoot 'icon.ico');." --distpath (Join-Path $buildRoot 'dist') --workpath (Join-Path $buildRoot 'build') --specpath $buildRoot (Join-Path $PSScriptRoot 'app.py')
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
# Qt 6.12 uses Windows' unversioned ICU API. A Python-distribution ICU DLL
# can be collected by PyInstaller from PATH and shadow the system ICU.
$distRoot = Join-Path $buildRoot 'dist\XT阅迹\_internal'
foreach ($fileName in @('icuuc.dll', 'icudt78.dll')) {
    $filePath = Join-Path $distRoot $fileName
    if (Test-Path -LiteralPath $filePath) { Remove-Item -LiteralPath $filePath }
}
$dictionarySource = Join-Path $packageRoot 'dictionary'
if (-not (Test-Path -LiteralPath (Join-Path $dictionarySource 'ecdict.sqlite'))) {
    throw 'Offline dictionary missing; first build it with src/build_dictionary.py'
}
$dictionaryTarget = Join-Path $buildRoot 'dist\XT阅迹\dictionary'
New-Item -ItemType Directory -Path $dictionaryTarget -Force | Out-Null
foreach ($file in @('ecdict.sqlite', 'source.json', 'LICENSE.txt')) {
    Copy-Item -LiteralPath (Join-Path $dictionarySource $file) -Destination $dictionaryTarget -Force
}
$finalRoot = Join-Path $buildRoot 'dist\XT阅迹'
foreach ($folder in @('src', 'licenses', 'tessdata', 'tests', 'installer')) {
    $destination = Join-Path $finalRoot $folder
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    Get-ChildItem -LiteralPath (Join-Path $packageRoot $folder) -File | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
    }
}
foreach ($file in @('README.md', 'NAMING.md', 'LICENSE', '使用说明.md', '第三方说明.txt', 'Example.pdf', '精读导出示例.pdf', '单词释义表导出示例.pdf', '论文批注导出示例.pdf', 'icon.ico')) {
    Copy-Item -LiteralPath (Join-Path $packageRoot $file) -Destination $finalRoot -Force
}
Write-Output "Build ready in $buildRoot\dist\XT阅迹"
