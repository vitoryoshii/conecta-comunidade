"""Testes das ofertas, do chat, das entregas, das ONGs e do mapa."""

from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.models import ONG, Categoria, Oferta, Solicitacao, StatusSolicitacao, Usuario
from backend.services.seed_service import (
    _criar_categorias,
    _criar_ofertas,
    _criar_ongs,
    _criar_solicitacoes,
    _criar_usuarios,
)
from tests.conftest import cabecalho_autenticado


def _pedido_da_ana(session: Session, usuario_ana: Usuario, categoria: Categoria) -> Solicitacao:
    """Cria o pedido de água usado como contexto dos cenários abaixo."""
    solicitacao = Solicitacao(
        usuario_id=usuario_ana.id,  # type: ignore[arg-type]
        titulo="Água potável para 4 famílias",
        categoria_id=categoria.id,  # type: ignore[arg-type]
        latitude=usuario_ana.latitude,
        longitude=usuario_ana.longitude,
        pessoas_beneficiadas=16,
    )
    session.add(solicitacao)
    session.commit()
    session.refresh(solicitacao)
    return solicitacao


# --------------------------------------------------------------------------- #
# Ofertas
# --------------------------------------------------------------------------- #
def test_criar_oferta_exige_autenticacao(
    client: TestClient, categorias: dict[str, Categoria]
) -> None:
    """Enviar proposta sem token deve resultar em 401."""
    resposta = client.post(
        "/ofertas", json={"titulo": "Tenho água", "categoria_id": categorias["agua"].id}
    )

    assert resposta.status_code == 401


def test_criar_oferta_avulsa(
    client: TestClient, usuario_carlos: Usuario, categorias: dict[str, Categoria]
) -> None:
    """Oferta sem vínculo com pedido é criada normalmente."""
    headers = cabecalho_autenticado(client, usuario_carlos.email)

    resposta = client.post(
        "/ofertas",
        json={
            "titulo": "Ponto de retirada em Pinheiros",
            "categoria_id": categorias["agua"].id,
            "tipo_ajuda": "ponto_retirada",
        },
        headers=headers,
    )

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["tipo_ajuda"] == "ponto_retirada"
    assert corpo["status"] == "disponivel"
    assert corpo["autor_nome"] == "Carlos Mendes"


def test_oferta_para_pedido_abre_chat_e_move_status(
    client: TestClient,
    session: Session,
    usuario_ana: Usuario,
    usuario_carlos: Usuario,
    categorias: dict[str, Categoria],
) -> None:
    """A tela *Quero ajudar* cria a oferta, a 1ª mensagem e muda o pedido."""
    solicitacao = _pedido_da_ana(session, usuario_ana, categorias["agua"])
    headers_carlos = cabecalho_autenticado(client, usuario_carlos.email)

    resposta = client.post(
        "/ofertas",
        json={
            "titulo": "Tenho 60 litros de água",
            "categoria_id": categorias["agua"].id,
            "tipo_ajuda": "tenho_item",
            "solicitacao_id": solicitacao.id,
            "mensagem": "Consigo levar hoje à tarde!",
        },
        headers=headers_carlos,
    )
    assert resposta.status_code == 201, resposta.text

    # O pedido saiu de "ativa".
    detalhe = client.get(f"/solicitacoes/{solicitacao.id}").json()
    assert detalhe["status"] == StatusSolicitacao.EM_ANDAMENTO.value

    # E a conversa já nasceu com a mensagem enviada junto da proposta.
    chat = client.get(f"/mensagens?com={usuario_ana.id}", headers=headers_carlos).json()
    assert [m["texto"] for m in chat] == ["Consigo levar hoje à tarde!"]


def test_filtro_de_ofertas_por_tipo_de_ajuda(
    client: TestClient, usuario_carlos: Usuario, categorias: dict[str, Categoria]
) -> None:
    """O filtro `tipo_ajuda` separa item, entrega e ponto de retirada."""
    headers = cabecalho_autenticado(client, usuario_carlos.email)
    for titulo, tipo in [("Tenho item", "tenho_item"), ("Posso levar", "posso_entregar")]:
        client.post(
            "/ofertas",
            json={"titulo": titulo, "categoria_id": categorias["agua"].id, "tipo_ajuda": tipo},
            headers=headers,
        )

    corpo = client.get("/ofertas?tipo_ajuda=posso_entregar").json()

    assert [item["titulo"] for item in corpo] == ["Posso levar"]


# --------------------------------------------------------------------------- #
# Mensagens
# --------------------------------------------------------------------------- #
def test_enviar_e_ler_mensagens(
    client: TestClient, usuario_ana: Usuario, usuario_carlos: Usuario
) -> None:
    """Mensagem enviada aparece no histórico dos dois participantes."""
    headers_carlos = cabecalho_autenticado(client, usuario_carlos.email)

    resposta = client.post(
        "/mensagens",
        json={"destinatario_id": usuario_ana.id, "texto": "Olá, Ana!"},
        headers=headers_carlos,
    )
    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["remetente_nome"] == "Carlos Mendes"

    headers_ana = cabecalho_autenticado(client, usuario_ana.email)
    chat = client.get(f"/mensagens?com={usuario_carlos.id}", headers=headers_ana).json()

    assert [m["texto"] for m in chat] == ["Olá, Ana!"]
    # Abrir o chat marca a mensagem recebida como lida.
    assert chat[0]["lida"] is True


def test_nao_e_possivel_mandar_mensagem_para_si_mesmo(
    client: TestClient, usuario_ana: Usuario
) -> None:
    """Conversa consigo mesmo não faz sentido no domínio e é bloqueada."""
    headers = cabecalho_autenticado(client, usuario_ana.email)

    resposta = client.post(
        "/mensagens", json={"destinatario_id": usuario_ana.id, "texto": "oi"}, headers=headers
    )

    assert resposta.status_code == 422


def test_lista_de_conversas_traz_ultima_mensagem_e_nao_lidas(
    client: TestClient, usuario_ana: Usuario, usuario_carlos: Usuario
) -> None:
    """A aba Mensagens mostra a última fala e o contador de não lidas."""
    headers_carlos = cabecalho_autenticado(client, usuario_carlos.email)
    for texto in ["Primeira", "Segunda"]:
        client.post(
            "/mensagens",
            json={"destinatario_id": usuario_ana.id, "texto": texto},
            headers=headers_carlos,
        )

    headers_ana = cabecalho_autenticado(client, usuario_ana.email)
    conversas = client.get("/mensagens/conversas", headers=headers_ana).json()

    assert len(conversas) == 1
    assert conversas[0]["interlocutor_nome"] == "Carlos Mendes"
    assert conversas[0]["ultima_mensagem"] == "Segunda"
    assert conversas[0]["nao_lidas"] == 2


# --------------------------------------------------------------------------- #
# Entregas
# --------------------------------------------------------------------------- #
def test_agendar_e_concluir_entrega_atualiza_impacto(
    client: TestClient,
    session: Session,
    usuario_ana: Usuario,
    usuario_carlos: Usuario,
    categorias: dict[str, Categoria],
) -> None:
    """Concluir a entrega fecha o pedido e alimenta os contadores de impacto."""
    solicitacao = _pedido_da_ana(session, usuario_ana, categorias["agua"])
    headers_carlos = cabecalho_autenticado(client, usuario_carlos.email)

    resposta = client.post(
        "/entregas",
        json={
            "solicitacao_id": solicitacao.id,
            "data": "15/03/2026",
            "hora": "14:00",
            "local": "Praça Benedito Calixto",
        },
        headers=headers_carlos,
    )
    assert resposta.status_code == 201, resposta.text
    entrega_id = resposta.json()["id"]
    assert resposta.json()["status"] == "agendada"

    resposta = client.patch(
        f"/entregas/{entrega_id}", json={"status": "realizada"}, headers=headers_carlos
    )
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "realizada"

    assert client.get(f"/solicitacoes/{solicitacao.id}").json()["status"] == "concluida"

    impacto_carlos = client.get("/perfil/impacto", headers=headers_carlos).json()
    assert impacto_carlos["solicitacoes_atendidas"] == 1

    headers_ana = cabecalho_autenticado(client, usuario_ana.email)
    assert client.get("/perfil/impacto", headers=headers_ana).json()["doacoes_recebidas"] == 1


# --------------------------------------------------------------------------- #
# ONGs
# --------------------------------------------------------------------------- #
def test_listar_ongs_com_distancia(
    client: TestClient, usuario_ana: Usuario, ong_verificada: ONG
) -> None:
    """A lista de ONGs traz selo de verificação e distância formatada."""
    corpo = client.get(f"/ongs?lat={usuario_ana.latitude}&long={usuario_ana.longitude}").json()

    assert len(corpo) == 1
    assert corpo[0]["verificada"] is True
    assert corpo[0]["distancia_km"] is not None
    assert corpo[0]["distancia_formatada"] != "--"


def test_avaliar_ong_recalcula_media(
    client: TestClient, usuario_ana: Usuario, ong_verificada: ONG
) -> None:
    """Nota 5 sobre média 4.0 com 10 votos resulta em 4.09 com 11 votos."""
    headers = cabecalho_autenticado(client, usuario_ana.email)

    resposta = client.post(f"/ongs/{ong_verificada.id}/avaliar", json={"nota": 5}, headers=headers)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total_avaliacoes"] == 11
    assert corpo["avaliacao"] == round((4.0 * 10 + 5) / 11, 2)


# --------------------------------------------------------------------------- #
# Mapa
# --------------------------------------------------------------------------- #
def test_mapa_agrupa_pontos_por_tipo(
    client: TestClient,
    session: Session,
    usuario_ana: Usuario,
    usuario_carlos: Usuario,
    categorias: dict[str, Categoria],
    ong_verificada: ONG,
) -> None:
    """O mapa junta solicitações, ofertas, pontos de retirada e ONGs."""
    _pedido_da_ana(session, usuario_ana, categorias["agua"])
    headers = cabecalho_autenticado(client, usuario_carlos.email)
    client.post(
        "/ofertas",
        json={
            "titulo": "Retirada em Pinheiros",
            "categoria_id": categorias["agua"].id,
            "tipo_ajuda": "ponto_retirada",
        },
        headers=headers,
    )

    corpo = client.get("/mapa").json()

    assert corpo["total_por_tipo"]["ajuda"] == 1
    assert corpo["total_por_tipo"]["ponto_retirada"] == 1
    assert corpo["total_por_tipo"]["ong"] == 1
    assert all("latitude" in ponto for ponto in corpo["pontos"])


def test_mapa_filtra_por_tipo(
    client: TestClient, session: Session, usuario_ana: Usuario, categorias: dict[str, Categoria],
    ong_verificada: ONG,
) -> None:
    """Os toggles do painel de filtros usam o parâmetro `tipos`."""
    _pedido_da_ana(session, usuario_ana, categorias["agua"])

    corpo = client.get("/mapa?tipos=ong").json()

    assert corpo["total_por_tipo"]["ajuda"] == 0
    assert corpo["total_por_tipo"]["ong"] == 1


def test_mapa_retorna_os_16_pontos_do_seed(client: TestClient, session: Session) -> None:
    """O cenário de demonstração precisa alimentar todos os pins do mapa."""
    categorias = _criar_categorias(session)
    usuarios = _criar_usuarios(session)
    _criar_ongs(session)
    solicitacoes = _criar_solicitacoes(session, usuarios, categorias)
    _criar_ofertas(session, usuarios, categorias, solicitacoes)

    corpo = client.get("/mapa").json()

    assert len(corpo["pontos"]) == 16
    assert corpo["total_por_tipo"] == {
        "ajuda": 7,
        "oferecendo": 2,
        "ong": 5,
        "ponto_retirada": 2,
    }
    assert {
        "id",
        "tipo",
        "latitude",
        "longitude",
        "titulo",
    }.issubset(corpo["pontos"][0])
