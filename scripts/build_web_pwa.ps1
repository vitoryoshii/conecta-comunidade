param(
    [string]$OutputDir = "build/web"
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

# Web usa staging próprio: não conflita com Gradle/Flet do APK.
$StagingDir = "build/web-distribution-app"
& .\.venv\Scripts\python.exe -c "from pathlib import Path; from scripts.prepare_mobile_distribution import preparar_staging; print(preparar_staging(Path('$StagingDir')))"
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao preparar o staging da PWA."
}

& .\.venv\Scripts\flet.exe build web $StagingDir --no-rich-output --yes -o $OutputDir
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao gerar a PWA estática."
}

# A configuração acompanha o artefato enviado com `vercel --cwd build/web`.
Copy-Item deploy\web\vercel.json (Join-Path $OutputDir "vercel.json") -Force
Write-Output "PWA pronta em $OutputDir"
