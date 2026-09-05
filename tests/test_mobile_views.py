"""
Testes de renderização das telas Flet.

Não abrem janela: montam cada view em memória, contra a API real servida pelo
`TestClient` do FastAPI (sem rede e sem Uvicorn). Isso garante que nenhuma tela quebre por um controle mal
construído ou por um campo que a API deixou de devolver — a falha aparece aqui,
e não durante a apresentação.
"""

from collections.abc import Generator
from types import SimpleNamespace
from typing import Any

import flet as ft
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.database import get_session
from backend.main import app as api_fastapi
from backend.models import ONG, Categoria, Usuario
from mobile.api_client import ApiClient
from mobile.main import ROTAS, App


class PaginaFalsa(SimpleNamespace):
    """Dublê da `ft.Page`: só precisa aceitar as chamadas feitas nos handlers."""

    def update(self) -> None:
        """Nenhuma renderização real acontece nos testes."""

    def show_dialog(self, dialogo: Any) -> None:
        """Registra o último diálogo/aviso exibido."""
        self.ultimo_dialogo = dialogo

    def pop_dialog(self) -> None:
        """Fecha o diálogo aberto."""


@pytest.fixture(name="app_mobile")
def fixture_app_mobile(
    session: Session,
    usuario_ana: Usuario,
    categorias: dict[str, Categoria],
    ong_verificada: ONG,
) -> Generator[App, None, None]:
    """App Flet conectado à API de teste, já autenticado como Ana."""

    def obter_sessao_de_teste() -> Generator[Session, None, None]:
        yield session

    api_fastapi.dependency_overrides[get_session] = obter_sessao_de_teste

    aplicacao = App(PaginaFalsa())
    # O TestClient do FastAPI é um `httpx.Client` que fala direto com o app,
    # sem rede: trocando o transporte do ApiClient por ele, as telas rodam
    # contra a API de verdade sem precisar subir o Uvicorn.
    aplicacao.api = ApiClient("http://teste")
    aplicacao.api._http = TestClient(api_fastapi, base_url="http://teste")

    resposta = aplicacao.api.login(usuario_ana.email, "senha123")
    aplicacao.api.definir_token(resposta["access_token"])
    aplicacao.state.entrar(resposta["access_token"], resposta["usuario"])

    yield aplicacao

    aplicacao.api.fechar()
    api_fastapi.dependency_overrides.clear()


def _parametros_da_rota(nome: str, app_mobile: App) -> dict[str, Any]:
    """Parâmetros mínimos exigidos por cada rota que depende de contexto."""
    if nome == "detalhe_solicitacao":
        return {"id": _id_da_primeira_solicitacao(app_mobile)}
    if nome == "quero_ajudar":
        return {
            "solicitacao": app_mobile.api.obter_solicitacao(
                _id_da_primeira_solicitacao(app_mobile)
            )
        }
    if nome == "chat":
        return {"com": app_mobile.state.usuario_id, "nome": "Conversa de teste"}
    if nome == "perfil_ong":
        return {"id": _id_da_primeira_ong(app_mobile)}
    return {}


def _id_da_primeira_solicitacao(app_mobile: App) -> int:
    """Cria (se preciso) e devolve o id de uma solicitação para os testes."""
    existentes = app_mobile.api.listar_solicitacoes()
    if existentes:
        return existentes[0]["id"]

    categoria = app_mobile.api.listar_categorias()[0]
    criada = app_mobile.api.criar_solicitacao(
        {
            "titulo": "Pedido para renderização",
            "descricao": "Criado pelo teste de views.",
            "categoria_id": categoria["id"],
            "urgencia": "alta",
            "emergencia": True,
        }
    )
    return criada["id"]


def _id_da_primeira_ong(app_mobile: App) -> int | None:
    """Id da primeira ONG cadastrada, ou `None` quando não houver nenhuma."""
    ongs = app_mobile.api.listar_ongs()
    return ongs[0]["id"] if ongs else None


@pytest.mark.parametrize("nome_da_rota", sorted(ROTAS))
def test_todas_as_telas_sao_construidas(app_mobile: App, nome_da_rota: str) -> None:
    """Cada rota registrada precisa devolver um controle Flet válido."""
    if nome_da_rota == "perfil_ong" and _id_da_primeira_ong(app_mobile) is None:
        pytest.skip("Sem ONG cadastrada neste cenário.")

    construtor, _ = ROTAS[nome_da_rota]
    app_mobile.state.reiniciar(nome_da_rota, **_parametros_da_rota(nome_da_rota, app_mobile))

    controle = construtor(app_mobile)

    assert isinstance(controle, ft.Control)


def test_navegacao_empilha_e_volta(app_mobile: App) -> None:
    """A pilha de rotas precisa suportar abrir e voltar telas."""
    app_mobile.state.reiniciar("home")
    app_mobile.state.empilhar("detalhe_solicitacao", id=1)

    assert app_mobile.state.rota_atual.nome == "detalhe_solicitacao"
    assert app_mobile.state.desempilhar() is True
    assert app_mobile.state.rota_atual.nome == "home"
    # Na raiz, não há mais para onde voltar.
    assert app_mobile.state.desempilhar() is False


def test_abas_principais_reiniciam_a_pilha(app_mobile: App) -> None:
    """Trocar de aba não deve acumular telas na pilha de navegação."""
    app_mobile.state.reiniciar("home")
    app_mobile.state.empilhar("detalhe_solicitacao", id=1)
    app_mobile.state.reiniciar("explorar")

    assert len(app_mobile.state.pilha) == 1
    assert app_mobile.state.rota_atual.nome == "explorar"


def test_sair_limpa_a_sessao(app_mobile: App) -> None:
    """Logout precisa apagar token, usuário e pilha."""
    app_mobile.state.sair()

    assert app_mobile.state.autenticado is False
    assert app_mobile.state.token is None
    assert app_mobile.state.pilha == []
