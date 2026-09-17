"""Testes de favoritos: guardar, listar, remover e não vazar entre usuários."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.models import Categoria, Solicitacao, Usuario
from tests.conftest import cabecalho_autenticado


@pytest.fixture(name="pedido")
def fixture_pedido(
    session: Session, usuario_ana: Usuario, categorias: dict[str, Categoria]
) -> Solicitacao:
    """Uma solicitação da Ana, para ser favoritada pelos outros."""
    solicitacao = Solicitacao(
        usuario_id=usuario_ana.id,  # type: ignore[arg-type]
        titulo="Água potável para 4 famílias",
        descricao="Descrição de teste.",
        categoria_id=categorias["agua"].id,  # type: ignore[arg-type]
        latitude=-23.5545,
        longitude=-46.6896,
    )
    session.add(solicitacao)
    session.commit()
    session.refresh(solicitacao)
    return solicitacao


def _cabecalho(client: TestClient, usuario: Usuario) -> dict[str, str]:
    """Token do usuário indicado, no formato do header."""
    return cabecalho_autenticado(client, usuario.email)


def test_favoritar_guarda_e_listar_devolve_a_solicitacao(
    client: TestClient, usuario_carlos: Usuario, pedido: Solicitacao
) -> None:
    """Favoritar faz a solicitação aparecer na lista, inteira."""
    cabecalho = _cabecalho(client, usuario_carlos)

    criado = client.post("/favoritos", json={"solicitacao_id": pedido.id}, headers=cabecalho)
    assert criado.status_code == 201, criado.text
    assert criado.json()["solicitacao_id"] == pedido.id

    lista = client.get("/favoritos", headers=cabecalho)
    assert lista.status_code == 200
    corpo = lista.json()
    assert [item["id"] for item in corpo] == [pedido.id]
    # Vem no mesmo formato da Home: com categoria, autor e distância.
    assert corpo[0]["titulo"] == pedido.titulo
    assert corpo[0]["categoria_nome"]
    assert corpo[0]["favoritada"] is True


def test_favoritar_duas_vezes_nao_duplica(
    client: TestClient, usuario_carlos: Usuario, pedido: Solicitacao
) -> None:
    """O coração é um botão que alterna: dois toques não viram dois favoritos."""
    cabecalho = _cabecalho(client, usuario_carlos)
    corpo = {"solicitacao_id": pedido.id}

    assert client.post("/favoritos", json=corpo, headers=cabecalho).status_code == 201
    assert client.post("/favoritos", json=corpo, headers=cabecalho).status_code == 201

    assert len(client.get("/favoritos", headers=cabecalho).json()) == 1


def test_desfavoritar_remove_da_lista(
    client: TestClient, usuario_carlos: Usuario, pedido: Solicitacao
) -> None:
    """Desfavoritar tira da lista; repetir não vira erro."""
    cabecalho = _cabecalho(client, usuario_carlos)
    client.post("/favoritos", json={"solicitacao_id": pedido.id}, headers=cabecalho)

    assert client.delete(f"/favoritos/{pedido.id}", headers=cabecalho).status_code == 204
    assert client.get("/favoritos", headers=cabecalho).json() == []

    # Remover o que já não está guardado: o estado desejado já é o atual.
    assert client.delete(f"/favoritos/{pedido.id}", headers=cabecalho).status_code == 204


def test_favorito_de_um_nao_aparece_para_o_outro(
    client: TestClient,
    usuario_carlos: Usuario,
    usuario_ana: Usuario,
    pedido: Solicitacao,
) -> None:
    """Favorito é de quem favoritou — não vaza para outra conta."""
    client.post(
        "/favoritos",
        json={"solicitacao_id": pedido.id},
        headers=_cabecalho(client, usuario_carlos),
    )

    de_ana = client.get("/favoritos", headers=_cabecalho(client, usuario_ana))
    assert de_ana.json() == []


def test_listagem_marca_o_que_o_usuario_favoritou(
    client: TestClient, usuario_carlos: Usuario, pedido: Solicitacao
) -> None:
    """`favoritada` acende só para quem guardou, e some ao desfavoritar."""
    cabecalho = _cabecalho(client, usuario_carlos)

    def na_listagem() -> dict:
        itens = client.get("/solicitacoes", headers=cabecalho).json()
        return next(item for item in itens if item["id"] == pedido.id)

    assert na_listagem()["favoritada"] is False

    client.post("/favoritos", json={"solicitacao_id": pedido.id}, headers=cabecalho)
    assert na_listagem()["favoritada"] is True
    # O detalhe conta a mesma história.
    detalhe = client.get(f"/solicitacoes/{pedido.id}", headers=cabecalho)
    assert detalhe.json()["favoritada"] is True

    client.delete(f"/favoritos/{pedido.id}", headers=cabecalho)
    assert na_listagem()["favoritada"] is False


def test_visitante_ve_tudo_sem_coracao(client: TestClient, pedido: Solicitacao) -> None:
    """Sem sessão não há favorito: a listagem pública nem tenta consultar."""
    itens = client.get("/solicitacoes").json()

    assert all(item["favoritada"] is False for item in itens)


def test_favoritar_pedido_inexistente_responde_404(
    client: TestClient, usuario_carlos: Usuario
) -> None:
    """Guardar o que não existe é erro, não um favorito órfão."""
    resposta = client.post(
        "/favoritos", json={"solicitacao_id": 9999}, headers=_cabecalho(client, usuario_carlos)
    )

    assert resposta.status_code == 404


def test_favoritos_exigem_sessao(client: TestClient) -> None:
    """As três rotas são do dono da conta: sem token, 401."""
    assert client.get("/favoritos").status_code == 401
    assert client.post("/favoritos", json={"solicitacao_id": 1}).status_code == 401
    assert client.delete("/favoritos/1").status_code == 401
