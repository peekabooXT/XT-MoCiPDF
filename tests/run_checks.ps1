param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
$packageRoot = Split-Path -Parent $PSScriptRoot
New-Item -ItemType Directory -Path (Join-Path $packageRoot 'work') -Force | Out-Null
Push-Location $packageRoot
try {
    foreach ($file in @('verify_app.py', 'verify_reading.py', 'verify_double_click.py', 'verify_dictionary.py', 'verify_reading_export.py', 'verify_vocabulary_export.py', 'verify_annotations.py', 'verify_tool_settings.py', 'verify_personal_dictionary.py', 'verify_visible_notes.py', 'verify_merge_export.py', 'verify_languages.py', 'verify_editor_behavior.py')) {
        & $Python (Join-Path $PSScriptRoot $file)
        if ($LASTEXITCODE -ne 0) { throw "Verification failed: $file" }
    }
} finally {
    Pop-Location
}
