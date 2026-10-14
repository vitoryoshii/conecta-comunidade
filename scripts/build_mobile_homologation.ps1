param(
    [string]$OutputDir = "build/apk-homologation"
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

& .\.venv\Scripts\python.exe scripts\prepare_mobile_distribution.py
& .\.venv\Scripts\flet.exe build apk build\distribution-app --no-rich-output --yes -o $OutputDir
