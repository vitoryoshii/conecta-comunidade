# Assinatura Android para distribuição

## Homologação atual

O pipeline de homologação é o único comando recomendado para gerar APK local:

```powershell
.\scripts\build_mobile_homologation.ps1 -OutputDir build\apk-homologacao
```

Ele cria um staging com allowlist, usa um único worker Gradle, limita memória,
preserva as variáveis `SERIOUS_PYTHON_*` no fallback JNI e gera o ícone
adaptativo oficial. O resultado deve ser tratado como APK de teste até a
verificação de hash, scanner e certificado.

O APK de homologação pode ser criado sem credenciais de release e será assinado
com a chave de debug do Android. Ele não deve ser enviado à Play Store nem
declarado como build de produção.

Para uma distribuição, crie e guarde o keystore fora do repositório. Em uma
máquina de release ou no cofre de segredos do CI, informe os quatro valores ao
Flet por variáveis de ambiente:

```powershell
$env:FLET_ANDROID_SIGNING_KEY_STORE = 'C:\caminho-fora-do-repositorio\conecta-release.jks'
$env:FLET_ANDROID_SIGNING_KEY_STORE_PASSWORD = '<senha-do-keystore>'
$env:FLET_ANDROID_SIGNING_KEY_PASSWORD = '<senha-da-chave>'
$env:FLET_ANDROID_SIGNING_KEY_ALIAS = '<alias-da-chave>'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\flet.exe build apk --no-rich-output
```

Não registre o keystore, senhas, alias de produção ou variáveis de assinatura
em `pyproject.toml`, `.env`, commits, logs ou arquivos do projeto.

Valide que o APK de distribuição não usa certificado debug antes da publicação:

```powershell
keytool -printcert -jarfile .\build\apk-homologacao\conecta-comunidade.apk
```

Também valide a assinatura instalada:

```powershell
apksigner verify --print-certs .\build\apk-homologacao\conecta-comunidade.apk
```

Não apague ou desinstale uma instalação existente ao encontrar incompatibilidade
de assinatura: isso pode remover dados locais. Confirme a estratégia de upgrade
antes de qualquer desinstalação.
