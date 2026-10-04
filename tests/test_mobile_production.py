"""Regressões da configuração e do transporte do aplicativo mobile."""

from pathlib import Path
import tomllib

import httpx
import pytest

from mobile.api_client import ApiClient, ErroApi
from mobile.config import AMBIENTE_DESENVOLVIMENTO, AMBIENTE_PRODUCAO, obter_configuracao


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


def test_entrada_do_flet_mantem_o_pacote_mobile_no_bundle() -> None:
    """A raiz do app mantém `mobile` disponível para os imports absolutos."""
    configuracao = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    app = configuracao["tool"]["flet"]["app"]
    assert app["path"] == "."
    assert app["module"] == "main"
    assert Path("main.py").read_text(encoding="utf-8").strip().endswith(
        "from mobile.main import main"
    )
