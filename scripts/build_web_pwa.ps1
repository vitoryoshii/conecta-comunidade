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

function Assert-WebArtifact([string]$Directory, [switch]$IncludeBrandAssets) {
    $RequiredPaths = @(
        "index.html",
        "python.js",
        "python-worker.js",
        "pyodide/pyodide.mjs",
        "assets/app/app.zip"
    )
    if ($IncludeBrandAssets) {
        $RequiredPaths += @(
        "favicon.ico",
        "favicon-16x16.png",
        "favicon-32x32.png",
        "apple-touch-icon.png",
        "icons/Icon-192.png",
        "icons/Icon-512.png",
        "icons/Icon-maskable-192.png",
        "icons/Icon-maskable-512.png"
        )
    }
    foreach ($RelativePath in $RequiredPaths) {
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

# O Flet expõe assets no host HTTP, mas o Python Web lê arquivos pelo
# filesystem extraído de assets/app/app.zip. Duplica somente os dois Markdown
# oficiais nesse filesystem para que pathlib funcione no Pyodide, sem criar
# outra fonte de conteúdo jurídico.
$WebAppZip = Join-Path $TemporaryOutputDir "assets\app\app.zip"
$LegalAssets = Join-Path $StagingDir "assets\legal"
& $PythonExecutable (Join-Path $RepositoryRoot "scripts\embed_web_legal_assets.py") $WebAppZip $LegalAssets
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao incluir os documentos legais no app.zip Web."
}

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

# Flet 0.86.5 só conclui de forma confiável a transição do primeiro frame em
# apps complexos quando o contrato do splash Web gerado permanece presente:
# ``#splash``, ``#splash-branding`` e ``removeSplashFromWeb()``. Não use
# --no-web-splash aqui. Em vez disso, mantenha o contrato e substitua apenas a
# apresentação padrão (que contém a identidade do Flet) por uma tela neutra.
$Index = Get-Content -Raw $IndexPath
$NeutralLoadingStyle = @'
<style id="conecta-loading-style">
  html, body { margin: 0; min-height: 100%; background: #F5F7F6; }
  #splash { position: fixed; inset: 0; display: grid; place-items: center; background: #F5F7F6; color: #0E6B42; font-family: Arial, sans-serif; font-size: 14px; letter-spacing: .01em; }
  #splash::after { content: ""; width: 22px; height: 22px; margin-left: 10px; border: 3px solid #BFE8D5; border-top-color: #0E6B42; border-radius: 50%; animation: conecta-loading-spin .8s linear infinite; }
  @keyframes conecta-loading-spin { to { transform: rotate(360deg); } }
  @media (prefers-color-scheme: dark) { html, body, #splash { background: #0E2A47; color: #E9FBF4; } #splash::after { border-color: #285B69; border-top-color: #F5A623; } }
</style>
'@
$NeutralLoadingMarkup = @'
<div id="splash" role="status" aria-live="polite">Carregando</div>
'@
if ($Index -notmatch '<picture id="splash">[\s\S]*?</picture>') {
    throw "Não foi possível localizar a estrutura de splash gerada pelo Flet."
}
$Index = [regex]::Replace($Index, '<picture id="splash">[\s\S]*?</picture>', $NeutralLoadingMarkup.Trim(), 1)
if ($Index -notmatch '<style id="splash-screen-style">[\s\S]*?</style>') {
    throw "Não foi possível localizar os estilos de splash gerados pelo Flet."
}
$Index = [regex]::Replace($Index, '<style id="splash-screen-style">[\s\S]*?</style>', $NeutralLoadingStyle.Trim(), 1)
if ($Index -notmatch 'function removeSplashFromWeb\(\)') {
    throw "O contrato removeSplashFromWeb() do Flet não está presente."
}
if ($Index -match 'splash/img/' -or $Index -match 'flet-logo' -or $Index -match 'flutter_native_splash') {
    throw "O template Web ainda contém referência ao splash padrão do Flet."
}
Set-Content -Path $IndexPath -Value $Index -Encoding utf8NoBOM

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

# Substitui somente os ícones padrão do template Flet por variantes oficiais
# já versionadas. O script também produz favicon.ico determinístico, sem usar
# assets de cache, CDN ou ferramentas de imagem globais.
& $PythonExecutable (Join-Path $RepositoryRoot "scripts/prepare_web_icon_assets.py") $TemporaryOutputDir
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao preparar os ícones oficiais Web/PWA."
}

# O template aponta para favicon.png genérico. Declare explicitamente os
# tamanhos oficiais e o ícone Apple para evitar que navegadores reutilizem o
# ícone do Flutter/Flet em cache.
$Index = Get-Content -Raw $IndexPath
$DefaultFaviconPattern = '<link\s+rel="icon"\s+type="image/png"\s+href="favicon\.png"\s*/?>'
$OfficialFavicons = @'
<link rel="icon" href="favicon.ico" sizes="any">
  <link rel="icon" type="image/png" sizes="32x32" href="favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="favicon-16x16.png">
  <link rel="icon" type="image/svg+xml" href="favicon.svg">
'@
if ($Index -notmatch $DefaultFaviconPattern) {
    throw "Não foi possível localizar o favicon padrão do template Flet."
}
$Index = [regex]::Replace($Index, $DefaultFaviconPattern, $OfficialFavicons.Trim(), 1)
$Index = $Index.Replace('href="icons/apple-touch-icon-192.png"', 'href="apple-touch-icon.png"')
Set-Content -Path $IndexPath -Value $Index -Encoding utf8NoBOM

# A configuração acompanha o artefato enviado com `vercel --cwd build/web`.
Copy-Item (Join-Path $RepositoryRoot "deploy/web/vercel.json") (Join-Path $TemporaryOutputDir "vercel.json") -Force
Assert-WebArtifact $TemporaryOutputDir -IncludeBrandAssets

# Só promove uma saída completa. A anterior é preservada para diagnóstico e
# rollback local, nunca confundida com a compilação recém-validada.
if (Test-Path -LiteralPath $OutputPath) {
    $PreviousOutputDir = "$OutputPath.__previous-$([guid]::NewGuid().ToString('N'))"
    Move-Item -LiteralPath $OutputPath -Destination $PreviousOutputDir
}
Move-Item -LiteralPath $TemporaryOutputDir -Destination $OutputPath
$BuildDuration = (Get-Date) - $BuildStartedAt
Write-Output "PWA pronta em $OutputPath (Flet exit code 0; duração $([math]::Round($BuildDuration.TotalSeconds, 1)) s)"
