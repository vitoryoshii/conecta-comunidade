"""Contrato CORS da PWA: allowlist HTTPS e Bearer sem cookies."""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from backend.cors import configurar_cors


ORIGEM_AUTORIZADA = "https://preview.conecta.exemplo"
ORIGEM_NEGADA = "https://nao-autorizada.exemplo"


@pytest.fixture(name="cliente_cors")
def fixture_cliente_cors() -> TestClient:
    app = FastAPI()
    configurar_cors(app, [ORIGEM_AUTORIZADA])

    @app.get("/categorias")
    def categorias() -> list[dict[str, str]]:
        return [{"nome": "Água"}]

    @app.get("/ofertas")
    def ofertas() -> list[dict[str, str]]:
        return []

    @app.get("/auth/me")
    def usuario_atual() -> None:
        raise HTTPException(status_code=401, detail="Token ausente")

    @app.patch("/solicitacoes/1")
    def solicitacao_protegida() -> None:
        raise HTTPException(status_code=403, detail="Sem permissão")

    return TestClient(app)


def _cabecalhos_preflight(origem: str) -> dict[str, str]:
    return {
        "Origin": origem,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization",
    }


def test_preflight_autorizado_libera_bearer_sem_credentials(cliente_cors: TestClient) -> None:
    resposta = cliente_cors.options("/categorias", headers=_cabecalhos_preflight(ORIGEM_AUTORIZADA))

    assert resposta.status_code == 200
    assert resposta.headers["access-control-allow-origin"] == ORIGEM_AUTORIZADA
    assert "authorization" in resposta.headers["access-control-allow-headers"].lower()
    assert "access-control-allow-credentials" not in resposta.headers


def test_preflight_recusa_origem_fora_da_allowlist(cliente_cors: TestClient) -> None:
    resposta = cliente_cors.options("/categorias", headers=_cabecalhos_preflight(ORIGEM_NEGADA))

    assert resposta.status_code == 400
    assert "access-control-allow-origin" not in resposta.headers


def test_leituras_publicas_respeitam_allowlist(cliente_cors: TestClient) -> None:
    for caminho in ("/categorias", "/ofertas"):
        resposta = cliente_cors.get(caminho, headers={"Origin": ORIGEM_AUTORIZADA})
        assert resposta.status_code == 200
        assert resposta.headers["access-control-allow-origin"] == ORIGEM_AUTORIZADA
        assert "access-control-allow-credentials" not in resposta.headers


@pytest.mark.parametrize("caminho,metodo", [("/auth/me", "get"), ("/solicitacoes/1", "patch")])
def test_erros_autenticados_mantem_cors_sem_credentials(
    cliente_cors: TestClient, caminho: str, metodo: str
) -> None:
    resposta = getattr(cliente_cors, metodo)(caminho, headers={"Origin": ORIGEM_AUTORIZADA})

    assert resposta.status_code in {401, 403}
    assert resposta.headers["access-control-allow-origin"] == ORIGEM_AUTORIZADA
    assert "access-control-allow-credentials" not in resposta.headers
