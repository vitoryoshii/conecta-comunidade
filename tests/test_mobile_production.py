"""Regressões da configuração, transporte e segurança do APK mobile."""

import io
import json
from pathlib import Path
import tomllib
from typing import Iterator
import zipfile

import httpx
import pytest

from mobile.api_client import ApiClient, ErroApi
from mobile.config import AMBIENTE_DESENVOLVIMENTO, AMBIENTE_PRODUCAO, obter_configuracao


RAIZ = Path(__file__).resolve().parent.parent
APK_DE_HOMOLOGACAO = RAIZ / "build" / "apk" / "conecta-comunidade.apk"

# O APK é um ZIP que contém outros ZIPs (especialmente assets/app.zip). A
# inspeção usa nomes e padrões de segredos, nunca valores reais, para impedir
# que uma configuração local do backend volte a ser distribuída no aplicativo.
NOMES_SENSIVEIS = {".env", ".env.local", ".env.production"}
SUFIXOS_SENSIVEIS = {".db", ".sqlite", ".sqlite3", ".pem", ".key", ".p12", ".pfx", ".jks"}
# A cadeia pública da CA é necessária ao httpx para validar HTTPS; não é uma
# chave privada nem uma credencial da aplicação.
ARQUIVOS_PUBLICOS_PERMITIDOS = {"certifi/cacert.pem"}
PADROES_DE_SEGREDO = (
    b"DATABASE_URL=",
    b"SECRET_KEY=",
    b"PRIVATE_KEY=",
    b"AWS_SECRET_ACCESS_KEY=",
    b"OPENAI_API_KEY=",
)


def _entradas_do_zip(
    arquivo: Path | io.BytesIO, origem: str = ""
) -> Iterator[tuple[str, bytes]]:
    """Lista entradas, inclusive ZIPs aninhados, sem extrair no disco."""
    with zipfile.ZipFile(arquivo) as pacote:
        for entrada in pacote.infolist():
            if entrada.is_dir():
                continue
            caminho = f"{origem}!{entrada.filename}" if origem else entrada.filename
            conteudo = pacote.read(entrada)
            yield caminho, conteudo
            if entrada.filename.lower().endswith((".zip", ".apk", ".jar")):
                yield from _entradas_do_zip(io.BytesIO(conteudo), caminho)


def _nome_interno(caminho: str) -> str:
    """Devolve o nome da entrada, removendo os prefixos de ZIP aninhado."""
    return caminho.rsplit("!", maxsplit=1)[-1].lower()


def _cliente(status: int, corpo: object = None) -> ApiClient:
    app = ApiClient("https://api.teste")
    app._http = httpx.Client(
        base_url="https://api.teste",
        transport=httpx.MockTransport(lambda _: httpx.Response(status, json=corpo)),
    )
    return app


def test_configuracoes_de_ambiente_sao_explicitas() -> None:
    assert obter_configuracao(AMBIENTE_DESENVOLVIMENTO).api_base_url == "http://127.0.0.1:8000"
    producao = obter_configuracao(AMBIENTE_PRODUCAO)
    assert producao.api_base_url == "https://conecta-comunidade-wheat.vercel.app"
    assert "localhost" not in producao.api_base_url


def test_bearer_e_enviado_automaticamente() -> None:
    recebido: dict[str, str] = {}
    app = ApiClient("https://api.teste")
    app.definir_token("jwt-de-teste")
    app._http = httpx.Client(
        base_url="https://api.teste",
        transport=httpx.MockTransport(
            lambda request: (recebido.update(request.headers), httpx.Response(200, json=[]))[1]
        ),
    )
    app.listar_categorias()
    assert recebido["authorization"] == "Bearer jwt-de-teste"


@pytest.mark.parametrize("status", [403, 404, 409, 422, 500])
def test_status_http_tem_erro_para_interface(status: int) -> None:
    with pytest.raises(ErroApi) as erro:
        _cliente(status, {"detail": "detalhe útil"}).listar_categorias()
    assert erro.value.status == status
    assert erro.value.mensagem


def test_401_limpa_token_e_sinaliza_sessao_invalida() -> None:
    app = _cliente(401, {"detail": "Token inválido"})
    app.definir_token("jwt")
    chamadas: list[bool] = []
    app.ao_sessao_invalida = lambda: chamadas.append(True)
    with pytest.raises(ErroApi) as erro:
        app.listar_categorias()
    assert erro.value.status == 401
    assert app.token is None
    assert chamadas == [True]


def test_timeout_e_rede_recebem_mensagem_amigavel() -> None:
    app = ApiClient("https://api.teste")
    app._http = httpx.Client(
        base_url="https://api.teste",
        transport=httpx.MockTransport(lambda _: (_ for _ in ()).throw(httpx.ConnectTimeout("timeout"))),
    )
    with pytest.raises(ErroApi, match="demorou"):
        app.listar_categorias()


def test_mobile_nao_contem_segredos_ou_imports_backend() -> None:
    fontes = "\n".join(path.read_text(encoding="utf-8") for path in Path("mobile").rglob("*.py"))
    assert "DATABASE_URL" not in fontes
    assert "SECRET_KEY" not in fontes
    assert "from backend" not in fontes
    assert "import backend" not in fontes


def test_entrada_do_flet_usa_staging_allowlist_com_pacote_mobile() -> None:
    """O APK parte do staging público e mantém `mobile` para imports absolutos."""
    configuracao = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    app = configuracao["tool"]["flet"]["app"]
    assert app["path"] == "build/distribution-app"
    assert app["module"] == "main"
    entrypoint = Path("main.py").read_text(encoding="utf-8")
    assert "from mobile.main import ASSETS_DIR, main" in entrypoint
    assert "ft.run(main, assets_dir=str(ASSETS_DIR))" in entrypoint


def test_staging_configura_pwa_estatica_autonoma() -> None:
    """A web build embute seus runtimes e funciona em host estático."""
    from scripts.prepare_mobile_distribution import PYPROJECT_MOBILE

    configuracao = tomllib.loads(PYPROJECT_MOBILE)
    web = configuracao["tool"]["flet"]["web"]
    assert web["route_url_strategy"] == "hash"
    assert web["cdn"] is False
    assert web["pwa_theme_color"] == "#1F3A5F"


def test_script_de_build_web_remove_cdn_do_pyodide_e_normaliza_manifest() -> None:
    """Evita regressão no workaround do template Flet 0.86.5."""
    script = Path("scripts/build_web_pwa.ps1").read_text(encoding="utf-8")
    assert "pyodideUrl: null" in script
    assert 'new URL("pyodide/pyodide.mjs", _documentUrl).href' in script
    assert '$Manifest.short_name = "Conecta"' in script


def test_vercel_pwa_preserva_arquivos_estaticos_antes_do_fallback_spa() -> None:
    """O fallback SPA não pode capturar módulos Pyodide nem o app.zip."""
    configuracao = json.loads(Path("deploy/web/vercel.json").read_text(encoding="utf-8"))

    assert configuracao["rewrites"] == [
        {"source": "/(.*)", "destination": "/index.html"}
    ]


def test_configuracao_do_flet_exclui_dados_locais_e_credenciais() -> None:
    """Impede que arquivos locais voltem ao staging do Flet."""
    configuracao = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    exclusoes = set(configuracao["tool"]["flet"]["app"]["exclude"])

    assert {
        ".env",
        ".env.*",
        "*.db",
        "*.sqlite",
        "*.sqlite3",
        "*.pem",
        "*.key",
        "*.p12",
        "*.pfx",
        "*.jks",
        "mobile/assets/avatars",
    } <= exclusoes


def test_apk_de_homologacao_nao_contem_arquivos_ou_segredos_sensiveis() -> None:
    """Valida o APK final, inclusive app.zip e recursos ZIP aninhados."""
    assert APK_DE_HOMOLOGACAO.is_file(), (
        "APK de homologação ausente. Gere-o antes de executar a validação de artefato: "
        f"{APK_DE_HOMOLOGACAO}"
    )

    app_zip_encontrado = False
    violacoes: list[str] = []
    for caminho, conteudo in _entradas_do_zip(APK_DE_HOMOLOGACAO):
        app_zip_encontrado = app_zip_encontrado or caminho.endswith("assets/app.zip")
        nome = _nome_interno(caminho)
        arquivo = Path(nome).name
        if (
            arquivo in NOMES_SENSIVEIS
            or arquivo.startswith(".env.")
            or (
                Path(nome).suffix in SUFIXOS_SENSIVEIS
                and nome not in ARQUIVOS_PUBLICOS_PERMITIDOS
            )
            or "/mobile/assets/avatars/" in f"/{nome}"
        ):
            violacoes.append(f"arquivo sensível: {caminho}")
            continue

        # Não expõe o conteúdo encontrado: apenas informa que a entrada violou
        # a política. Os padrões têm '=' para evitar falsos positivos em textos
        # que apenas explicam nomes de variáveis.
        # Arquivos ZIP são validados recursivamente por ``_entradas_do_zip``.
        # Inspecionar também os bytes compactados pode gerar um falso positivo
        # ou apontar para o contêiner em vez da entrada responsável.
        if arquivo.endswith((".zip", ".apk", ".jar")):
            continue

        conteudo_normalizado = conteudo.upper()
        if any(padrao in conteudo_normalizado for padrao in PADROES_DE_SEGREDO):
            violacoes.append(f"padrão de credencial: {caminho}")

    assert app_zip_encontrado, "APK inválido: assets/app.zip não foi encontrado."
    assert not violacoes, "APK contém dados proibidos:\n" + "\n".join(violacoes)
