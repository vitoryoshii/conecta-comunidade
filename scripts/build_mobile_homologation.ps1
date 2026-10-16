param(
    [string]$OutputDir = "build/apk-homologation"
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
# O Flet/Rich pode receber nomes de arquivos com caracteres fora da página de
# código cp1252. Força UTF-8 também nos subprocessos Python chamados pelo CLI.
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

# O template Flutter do Flet pode gerar gradle.properties com heap de 8 GiB.
# Para a homologação local, limite o Gradle por ambiente: não altera o
# template gerado, evita daemon residual entre o build Flet e o fallback JNI
# e mantém o ajuste reproduzível em máquinas com 16 GiB de RAM.
$GradleWorkers = 1
$GradleHeapMb = 1024
$GradleOptions = @(
    "-Dorg.gradle.workers.max=$GradleWorkers",
    "-Dorg.gradle.parallel=false",
    "-Dorg.gradle.daemon=false",
    "-Dorg.gradle.vfs.watch=false",
    "-Dkotlin.compiler.execution.strategy=in-process",
    "-Dorg.gradle.jvmargs=-Xmx$($GradleHeapMb)m -XX:MaxMetaspaceSize=384m -XX:ReservedCodeCacheSize=128m"
) -join " "
if ([string]::IsNullOrWhiteSpace($env:GRADLE_OPTS)) {
    $env:GRADLE_OPTS = $GradleOptions
}
else {
    $env:GRADLE_OPTS = "$($env:GRADLE_OPTS) $GradleOptions"
}

& .\.venv\Scripts\python.exe scripts\prepare_mobile_distribution.py
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao preparar o staging do aplicativo mobile."
}

& .\.venv\Scripts\flet.exe build apk build\distribution-app --no-rich-output --yes `
    --android-adaptive-icon-background "#0E6B42" -o $OutputDir
if ($LASTEXITCODE -eq 0) {
    exit 0
}

# Flet 0.86.5 fixa ``jni`` em 1.0.0 no template Flutter. O resolvedor do Pub
# pode selecionar jni_flutter 1.0.4+1, que requer jni 1.1.0 e interrompe o
# Gradle. A versão 1.0.3 é compatível com a fixação do template. Só aplicamos
# o fallback quando os dois sinais estão presentes; outras falhas do Flet
# continuam sendo falhas do build.
$FlutterDir = "build\distribution-app\build\flutter"
$Pubspec = Join-Path $FlutterDir "pubspec.yaml"
$PubspecLock = Join-Path $FlutterDir "pubspec.lock"
$CompativelComFallback = (Test-Path $Pubspec) -and (Test-Path $PubspecLock) -and `
    ((Get-Content -Raw $Pubspec) -match '(?m)^  jni: 1\.0\.0\s*$') -and `
    ((Get-Content -Raw $PubspecLock) -match '(?s)jni_flutter:.*?version: "1\.0\.4\+1"')

if (-not $CompativelComFallback) {
    throw "Falha ao gerar o APK de homologação."
}

$ConteudoPubspec = Get-Content -Raw $Pubspec
$ConteudoPubspec = $ConteudoPubspec -replace '(?m)^  jni: 1\.0\.0\s*$', "  jni: 1.0.0`r`n  jni_flutter: 1.0.3"
Set-Content -Path $Pubspec -Value $ConteudoPubspec -Encoding utf8NoBOM

# Reutiliza exatamente o Flutter gerenciado pelo Flet, mesmo quando ele não
# estiver no PATH do terminal que iniciou este script.
$FlutterExe = & .\.venv\Scripts\python.exe -c "from pathlib import Path; import flet.version; from flet_cli.utils.flutter import get_flutter_dir; print(Path(get_flutter_dir(flet.version.flutter_version)) / 'bin' / 'flutter.bat')"
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $FlutterExe)) {
    throw "Não foi possível localizar o Flutter gerenciado pelo Flet."
}

$BuildDir = Join-Path (Resolve-Path "build\distribution-app") "build"
$SitePackages = Join-Path $BuildDir "site-packages"
$PythonApp = Join-Path $BuildDir "python-app"
$PythonVersionFile = Join-Path $BuildDir ".python-version"
if (-not (Test-Path $SitePackages) -or -not (Test-Path $PythonApp) -or -not (Test-Path $PythonVersionFile)) {
    throw "O Flet não preparou os diretórios Python necessários para a recuperação do build."
}

$PythonVersion = (Get-Content -Raw $PythonVersionFile).Trim()
$BundleId = & .\.venv\Scripts\python.exe -c "import tomllib; from pathlib import Path; print(tomllib.loads(Path('build/distribution-app/pyproject.toml').read_text(encoding='utf-8'))['tool']['flet']['bundle_id'])"
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($PythonVersion) -or [string]::IsNullOrWhiteSpace($BundleId)) {
    throw "Não foi possível recuperar a configuração Python preparada pelo Flet."
}

# A chamada original do Flet exporta estes valores em `_serious_python_build_env`.
# O fallback precisa propagá-los para a segunda chamada de `flutter build`, caso
# contrário o plugin serious_python_android não encontra o app e os pacotes
# previamente empacotados.
$EnvAnterior = @{
    SERIOUS_PYTHON_VERSION = $env:SERIOUS_PYTHON_VERSION
    SERIOUS_PYTHON_SITE_PACKAGES = $env:SERIOUS_PYTHON_SITE_PACKAGES
    SERIOUS_PYTHON_APP = $env:SERIOUS_PYTHON_APP
    SERIOUS_PYTHON_BUNDLE_ID = $env:SERIOUS_PYTHON_BUNDLE_ID
}
$env:SERIOUS_PYTHON_VERSION = $PythonVersion
$env:SERIOUS_PYTHON_SITE_PACKAGES = $SitePackages
$env:SERIOUS_PYTHON_APP = $PythonApp
$env:SERIOUS_PYTHON_BUNDLE_ID = $BundleId

Push-Location $FlutterDir
try {
    & $FlutterExe pub get
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao resolver as dependências Flutter compatíveis."
    }

    & $FlutterExe build apk --release
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao gerar o APK de homologação após corrigir a dependência JNI."
    }
}
finally {
    Pop-Location
    foreach ($Nome in $EnvAnterior.Keys) {
        if ($null -eq $EnvAnterior[$Nome]) {
            Remove-Item "Env:$Nome" -ErrorAction SilentlyContinue
        }
        else {
            Set-Item "Env:$Nome" $EnvAnterior[$Nome]
        }
    }
}

$ApkGerado = Join-Path $FlutterDir "build\app\outputs\flutter-apk\app-release.apk"
if (-not (Test-Path $ApkGerado)) {
    throw "O Flutter concluiu sem produzir o APK esperado."
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
Copy-Item -Path $ApkGerado -Destination (Join-Path $OutputDir "conecta-comunidade.apk") -Force
