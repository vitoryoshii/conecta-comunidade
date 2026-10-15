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

# O template atual do Flet 0.86.5 inclui Pyodide local com ``cdn = false``,
# mas ainda preenche uma URL jsDelivr no index. `python.js` usa essa URL antes
# do fallback local; anulá-la faz o worker carregar `pyodide/pyodide.mjs`.
$IndexPath = Join-Path $OutputDir "index.html"
$Index = Get-Content -Raw $IndexPath
$IndexAjustado = $Index -replace 'pyodideUrl: "https://[^"]+",', 'pyodideUrl: null,'
if ($IndexAjustado -eq $Index) {
    throw "Não foi possível remover a URL CDN do runtime Pyodide."
}
Set-Content -Path $IndexPath -Value $IndexAjustado -Encoding utf8NoBOM

# `python.js` cria um Module Worker. Um specifier como
# "pyodide/pyodide.mjs" é *bare* nesse contexto e o navegador não o resolve
# em relação ao worker. Passe uma URL absoluta, calculada a partir da página,
# para preservar o runtime Pyodide local em qualquer host estático.
$PythonLoaderPath = Join-Path $OutputDir "python.js"
$PythonLoader = Get-Content -Raw $PythonLoaderPath
$PythonLoaderAjustado = $PythonLoader -replace 'pyodideUrl: flet\.pyodideUrl \|\| "pyodide/pyodide\.mjs",', 'pyodideUrl: flet.pyodideUrl || new URL("pyodide/pyodide.mjs", _documentUrl).href,'
if ($PythonLoaderAjustado -eq $PythonLoader) {
    throw "Não foi possível normalizar a URL local do worker Pyodide."
}
Set-Content -Path $PythonLoaderPath -Value $PythonLoaderAjustado -Encoding utf8NoBOM

# Flet aplica as cores PWA, mas 0.86.5 não propaga pwa_short_name para este
# template. Corrigimos o manifest gerado sem introduzir dependências.
$ManifestPath = Join-Path $OutputDir "manifest.json"
$Manifest = Get-Content -Raw $ManifestPath | ConvertFrom-Json
$Manifest.short_name = "Conecta"
$Manifest.description = "Conecta pessoas, doadores, voluntários e ONGs."
$Manifest | ConvertTo-Json -Depth 16 | Set-Content -Path $ManifestPath -Encoding utf8NoBOM

# A configuração acompanha o artefato enviado com `vercel --cwd build/web`.
Copy-Item deploy\web\vercel.json (Join-Path $OutputDir "vercel.json") -Force
Write-Output "PWA pronta em $OutputDir"
