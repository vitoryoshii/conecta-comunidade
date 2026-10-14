"""Gera o staging allowlist do aplicativo mobile antes do build Flet."""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
STAGING_PADRAO = ROOT / "build" / "distribution-app"
ARQUIVOS_RAIZ = ("main.py",)
DIRETORIOS_DE_ASSETS_PUBLICOS = (
    Path("brand"),
    Path("legal"),
)
NOMES_PROIBIDOS = {".env", ".env.example", ".env.local", ".env.production"}
SUFIXOS_PROIBIDOS = {".db", ".sqlite", ".sqlite3", ".pem", ".key", ".p12", ".pfx", ".jks"}
PADROES_DE_SEGREDO = (
    b"DATABASE_URL=",
    b"SECRET_KEY=",
    b"PRIVATE_KEY=",
    b"AWS_SECRET_ACCESS_KEY=",
    b"OPENAI_API_KEY=",
)
PYPROJECT_MOBILE = '''[project]
name = "conecta-comunidade-mobile"
version = "1.0.0"
requires-python = ">=3.12,<3.15"
dependencies = ["flet==0.86.5", "httpx==0.28.1"]

[tool.flet]
product = "Conecta Comunidade"
bundle_id = "br.edu.conectacomunidade.app"
company = "VyteTech Solutions LTDA"
icon = "assets/brand/logo/app-icon-512.png"
splash_color = "#F5F7F6"
splash_dark_color = "#0E2A47"

[tool.flet.app]
path = "."
module = "main"

[tool.flet.web]
# URLs com hash funcionam em host estático sem envolver a API em roteamento.
route_url_strategy = "hash"
renderer = "canvaskit"
# Empacota Pyodide, fontes e CanvasKit no artefato; não depende de CDN externo.
cdn = false
pwa_background_color = "#F4F7FA"
pwa_theme_color = "#1F3A5F"
pwa_short_name = "Conecta"

[tool.flet.android.permission]
"android.permission.INTERNET" = true
'''


def _copiar(origem: Path, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origem, destino)


def _validar(staging: Path) -> None:
    violacoes: list[str] = []
    for arquivo in staging.rglob("*"):
        if not arquivo.is_file():
            continue
        relativo = arquivo.relative_to(staging)
        if (
            arquivo.name.lower() in NOMES_PROIBIDOS
            or arquivo.suffix.lower() in SUFIXOS_PROIBIDOS
            or "avatars" in relativo.parts
            or arquivo.name.lower() in {"readme.md", ".gitignore"}
        ):
            violacoes.append(str(relativo))
            continue
        if any(padrao in arquivo.read_bytes().upper() for padrao in PADROES_DE_SEGREDO):
            violacoes.append(str(relativo))
    if violacoes:
        raise RuntimeError("staging contém arquivos proibidos: " + ", ".join(sorted(violacoes)))


def _remover_staging(destino: Path) -> None:
    """Isola o staging anterior antes de removê-lo no Windows."""
    # A etapa anterior do Flutter pode ainda estar liberando subdiretórios no
    # momento em que a próxima homologação começa. Renomear a raiz é atômico
    # no mesmo volume, permitindo recriar o staging limpo mesmo se o Gradle
    # ainda estiver liberando arquivos do build anterior.
    anterior = destino.with_name(f"{destino.name}-stale-{uuid4().hex}")
    destino.replace(anterior)

    # Limpeza é apenas de artefato regenerável. Se um antivírus/Gradle ainda
    # prender um arquivo, o diretório permanece ignorado e será tentado de
    # novo em uma próxima execução, sem bloquear a homologação atual.
    for tentativa in range(5):
        try:
            shutil.rmtree(anterior)
            return
        except OSError:
            if tentativa == 4:
                return
            time.sleep(0.25 * (tentativa + 1))


def preparar_staging(destino: Path = STAGING_PADRAO) -> Path:
    """Reconstrói o staging exclusivamente a partir da allowlist pública."""
    destino = destino.resolve()
    if destino != STAGING_PADRAO.resolve() and STAGING_PADRAO.resolve() in destino.parents:
        raise ValueError("destino de staging inválido")
    if destino.exists():
        _remover_staging(destino)
    destino.mkdir(parents=True)

    for nome in ARQUIVOS_RAIZ:
        _copiar(ROOT / nome, destino / nome)

    for arquivo in (ROOT / "mobile").rglob("*.py"):
        _copiar(arquivo, destino / arquivo.relative_to(ROOT))

    for relativo in DIRETORIOS_DE_ASSETS_PUBLICOS:
        # O Flet Android 0.86 publica somente o diretório ``assets`` da raiz
        # da aplicação. A origem continua sob mobile/assets no repositório,
        # mas o staging usa o layout esperado pelo runtime.
        shutil.copytree(ROOT / "mobile" / "assets" / relativo, destino / "assets" / relativo)

    # O Flet resolve dependências pelo pyproject do diretório da aplicação.
    # Este manifesto evita que dependências do FastAPI/Vercel sejam incluídas
    # em futuros APKs, sem esconder essas dependências do serviço backend.
    (destino / "pyproject.toml").write_text(PYPROJECT_MOBILE, encoding="utf-8")

    _validar(destino)
    return destino


if __name__ == "__main__":
    print(preparar_staging())
