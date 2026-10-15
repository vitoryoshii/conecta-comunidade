param(
    [string]$OutputDir = "build/web"
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

# O Flet muda o diretório de trabalho para a app em staging durante partes do
# build. Resolva todos os caminhos a partir do repositório para que ``-o`` não
# seja interpretado em relação ao staging.
$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ([System.IO.Path]::IsPathRooted($OutputDir)) {
    $OutputPath = [System.IO.Path]::GetFullPath($OutputDir)
} else {
    $OutputPath = [System.IO.Path]::GetFullPath((Join-Path $RepositoryRoot $OutputDir))
}
$OutputParent = Split-Path -Parent $OutputPath
$TemporaryOutputDir = "$OutputPath.__building-$([guid]::NewGuid().ToString('N'))"

function Assert-WebArtifact([string]$Directory) {
    foreach ($RelativePath in @(
        "index.html",
        "python.js",
        "python-worker.js",
        "pyodide/pyodide.mjs",
        "assets/app/app.zip"
    )) {
        $Candidate = Join-Path $Directory $RelativePath
        if (-not (Test-Path -LiteralPath $Candidate -PathType Leaf)) {
            throw "Artefato web obrigatório ausente: $Candidate"
        }
    }
}

New-Item -ItemType Directory -Force -Path $OutputParent | Out-Null
if (Test-Path -LiteralPath $TemporaryOutputDir) {
    throw "Diretório temporário de build já existe: $TemporaryOutputDir"
}

# Web usa staging próprio: não conflita com Gradle/Flet do APK.
$StagingDir = Join-Path $RepositoryRoot "build/web-distribution-app"
$PythonExecutable = Join-Path $RepositoryRoot ".venv/Scripts/python.exe"
$FletExecutable = Join-Path $RepositoryRoot ".venv/Scripts/flet.exe"
& $PythonExecutable -c "from pathlib import Path; from scripts.prepare_mobile_distribution import preparar_staging; print(preparar_staging(Path(r'$StagingDir')))"
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao preparar o staging da PWA."
}

$FletArguments = @(
    "build", "web", "`"$StagingDir`"", "--no-rich-output", "--yes",
    "-o", "`"$TemporaryOutputDir`""
)
$BuildStartedAt = Get-Date
$FletProcess = Start-Process -FilePath $FletExecutable -ArgumentList $FletArguments -Wait -PassThru -NoNewWindow
if ($FletProcess.ExitCode -ne 0) {
    throw "Falha ao gerar a PWA estática (Flet exit code $($FletProcess.ExitCode))."
}
Assert-WebArtifact $TemporaryOutputDir

# O template atual do Flet 0.86.5 inclui Pyodide local com ``cdn = false``,
# mas ainda preenche uma URL jsDelivr no index. `python.js` usa essa URL antes
# do fallback local; anulá-la faz o worker carregar `pyodide/pyodide.mjs`.
$IndexPath = Join-Path $TemporaryOutputDir "index.html"
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
$PythonLoaderPath = Join-Path $TemporaryOutputDir "python.js"
$PythonLoader = Get-Content -Raw $PythonLoaderPath
$PythonLoaderAjustado = $PythonLoader -replace 'pyodideUrl: flet\.pyodideUrl \|\| "pyodide/pyodide\.mjs",', 'pyodideUrl: flet.pyodideUrl || new URL("pyodide/pyodide.mjs", _documentUrl).href,'
if ($PythonLoaderAjustado -eq $PythonLoader) {
    throw "Não foi possível normalizar a URL local do worker Pyodide."
}
Set-Content -Path $PythonLoaderPath -Value $PythonLoaderAjustado -Encoding utf8NoBOM

# Flet aplica as cores PWA, mas 0.86.5 não propaga pwa_short_name para este
# template. Corrigimos o manifest gerado sem introduzir dependências.
$ManifestPath = Join-Path $TemporaryOutputDir "manifest.json"
$Manifest = Get-Content -Raw $ManifestPath | ConvertFrom-Json
$Manifest.short_name = "Conecta"
$Manifest.description = "Conecta pessoas, doadores, voluntários e ONGs."
$Manifest | ConvertTo-Json -Depth 16 | Set-Content -Path $ManifestPath -Encoding utf8NoBOM

# A configuração acompanha o artefato enviado com `vercel --cwd build/web`.
Copy-Item (Join-Path $RepositoryRoot "deploy/web/vercel.json") (Join-Path $TemporaryOutputDir "vercel.json") -Force
Assert-WebArtifact $TemporaryOutputDir

# Só promove uma saída completa. A anterior é preservada para diagnóstico e
# rollback local, nunca confundida com a compilação recém-validada.
if (Test-Path -LiteralPath $OutputPath) {
    $PreviousOutputDir = "$OutputPath.__previous-$([guid]::NewGuid().ToString('N'))"
    Move-Item -LiteralPath $OutputPath -Destination $PreviousOutputDir
}
Move-Item -LiteralPath $TemporaryOutputDir -Destination $OutputPath
$BuildDuration = (Get-Date) - $BuildStartedAt
Write-Output "PWA pronta em $OutputPath (Flet exit code 0; duração $([math]::Round($BuildDuration.TotalSeconds, 1)) s)"
