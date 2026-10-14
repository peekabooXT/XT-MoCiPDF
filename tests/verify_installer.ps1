param([string]$Setup,[string]$Payload)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not $Setup) { $Setup = Join-Path $root 'dist\installer\XT-ReadTrace-1.13.2-Setup-x64.exe' }
$installer = (Resolve-Path -LiteralPath $Setup).Path
if (-not $Payload) { $Payload = $root }
$Payload = (Resolve-Path -LiteralPath $Payload).Path
$qaRoot = Join-Path $root 'work\installer-qa'
$installDir = Join-Path $qaRoot 'app'
$desktopShortcut = Join-Path ([Environment]::GetFolderPath('Desktop')) 'XT 阅迹.lnk'
$backupShortcut = Join-Path $qaRoot 'original-desktop.lnk'
$uninstallKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{D7E6B964-0F14-45C2-8572-4378D6CDB513}_is1'
if (Test-Path -LiteralPath $uninstallKey) { throw 'Existing installer registration found; stop before changing it' }
New-Item -ItemType Directory -Path (Join-Path $installDir 'data\pdfs'),(Join-Path $installDir 'exports') -Force | Out-Null
$hadShortcut = Test-Path -LiteralPath $desktopShortcut
if ($hadShortcut) { Copy-Item -LiteralPath $desktopShortcut -Destination $backupShortcut -Force }
$library = @{version=1;last='installer-qa-doc';documents=@(@{id='installer-qa-doc';title='Keep my reading notes';page=0;ocr=@{};marks=@(@{id='saved-mark';term='research';page=0;rects=@();order=0;created='2026-10-13T12:00:00'})})}
$library | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $installDir 'data\library.json') -Encoding utf8
Copy-Item -LiteralPath (Join-Path $Payload 'Example.pdf') -Destination (Join-Path $installDir 'data\pdfs\installer-qa-doc.pdf') -Force
Set-Content -LiteralPath (Join-Path $installDir 'exports\my-vocabulary.txt') -Value "#Keep my reading notes`nresearch" -Encoding utf8
$savedFiles = @(
    'data\library.json', 'data\pdfs\installer-qa-doc.pdf', 'exports\my-vocabulary.txt'
) | ForEach-Object { [pscustomobject]@{Relative=$_;Hash=(Get-FileHash -LiteralPath (Join-Path $installDir $_)).Hash} }
function CheckSavedData {
    foreach ($file in $savedFiles) {
        if ((Get-FileHash -LiteralPath (Join-Path $installDir $file.Relative)).Hash -ne $file.Hash) { throw ('User data changed: '+$file.Relative) }
    }
}
function RunSetup([string]$name) {
    $arguments = @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/NOICONS','/TASKS=desktopicon',('/DIR="'+$installDir+'"'),('/LOG="'+(Join-Path $qaRoot ($name+'.log'))+'"'))
    $process = Start-Process -FilePath $installer -ArgumentList $arguments -WindowStyle Hidden -PassThru
    if (-not $process.WaitForExit(30000)) { throw 'Installer test timed out' }
    if ($process.ExitCode -ne 0) { throw ('Installer failed: '+$process.ExitCode) }
    CheckSavedData
}
try {
    RunSetup 'fresh-install'
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($desktopShortcut)
    if ($shortcut.TargetPath -ne (Join-Path $installDir 'XT阅迹.exe')) { throw 'Desktop shortcut does not launch installed app' }
    if (-not (Test-Path -LiteralPath $uninstallKey)) { throw 'Windows uninstall registration missing' }
    $installedEntry = Get-ItemProperty -LiteralPath $uninstallKey
    if ($installedEntry.DisplayVersion -ne '1.13.2') { throw 'Installed version incorrect' }
    foreach ($file in @('XT阅迹.exe','dictionary\ecdict.sqlite','_internal\tessdata\eng.traineddata')) {
        if ((Get-FileHash -LiteralPath (Join-Path $installDir $file)).Hash -ne (Get-FileHash -LiteralPath (Join-Path $Payload $file)).Hash) { throw ('Installed payload differs: '+$file) }
    }
    $env:READTRACE_VERIFY_DIR = Join-Path $qaRoot ('native-qa-' + [Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $env:READTRACE_VERIFY_DIR -Force | Out-Null
    Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
    $app = Start-Process -FilePath (Join-Path $installDir 'XT阅迹.exe') -WindowStyle Hidden -PassThru
    if (-not $app.WaitForExit(25000)) { throw 'Installed app verification timed out' }
    $result = Get-Content -LiteralPath (Join-Path $env:READTRACE_VERIFY_DIR 'result.json') -Raw | ConvertFrom-Json
    if (-not $result.ok -or -not $result.offline_lookup -or -not $result.reading_background -or $result.vocabulary_export.terms -ne 2 -or $result.annotations -ne 5 -or -not $result.tool_shortcuts -or $result.visible_tools -ne 7 -or -not $result.personal_dictionary -or -not $result.visible_notes -or -not $result.merge_export -or $result.languages -ne 12 -or -not $result.default_english -or -not $result.author_statement) { throw ('Installed app test failed: '+$result.error) }
    Remove-Item Env:READTRACE_VERIFY_DIR -ErrorAction SilentlyContinue
    CheckSavedData
    RunSetup 'upgrade-install'
    $uninstaller = Join-Path $installDir 'unins000.exe'
    $remove = Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',('/LOG="'+(Join-Path $qaRoot 'uninstall.log')+'"')) -WindowStyle Hidden -PassThru
    if (-not $remove.WaitForExit(30000)) { throw 'Uninstaller timed out' }
    if ($remove.ExitCode -ne 0) { throw 'Uninstaller failed' }
    CheckSavedData
    if (Test-Path -LiteralPath (Join-Path $installDir 'XT阅迹.exe')) { throw 'Uninstaller did not remove program' }
    if (Test-Path -LiteralPath $uninstallKey) { throw 'Uninstaller registration left behind' }
    if (Test-Path -LiteralPath $desktopShortcut) { throw 'Test desktop shortcut left behind' }
    [pscustomobject]@{ok=$true;fresh_install=$true;upgrade_preserves_data=$true;uninstall_preserves_data=$true;desktop_shortcut=$true;windows_uninstall_entry=$true;offline_dictionary=$true;ocr=$true;reading_export=$true;app=$result} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $qaRoot 'result.json') -Encoding utf8
    Write-Output 'PASS: real installer, upgrade, desktop, uninstall registry, full offline app, and uninstall data preservation'
} finally {
    Remove-Item Env:READTRACE_VERIFY_DIR -ErrorAction SilentlyContinue
    if ($hadShortcut) { Copy-Item -LiteralPath $backupShortcut -Destination $desktopShortcut -Force }
}
