"""Testes de criação, listagem, filtros e ordenação de solicitações."""

from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.models import Categoria, Solicitacao, StatusSolicitacao, Urgencia, Usuario
from tests.conftest import COORD_CAPAO_REDONDO, COORD_PINHEIROS, cabecalho_autenticado


def _criar_solicitacao(
    session: Session,
    usuario: Usuario,
    categoria: Categoria,
    *,
    titulo: str,
    urgencia: Urgencia = Urgencia.MEDIA,
    status: StatusSolicitacao = StatusSolicitacao.ATIVA,
    coordenadas: tuple[float, float] = COORD_PINHEIROS,
    emergencia: bool = False,
) -> Solicitacao:
    """Insere uma solicitação diretamente no banco (atalho para os cenários)."""
    solicitacao = Solicitacao(
        usuario_id=usuario.id,  # type: ignore[arg-type]
        titulo=titulo,
        descricao="Descrição de teste.",
        categoria_id=categoria.id,  # type: ignore[arg-type]
        urgencia=urgencia,
        status=status,
        latitude=coordenadas[0],
        longitude=coordenadas[1],
        emergencia=emergencia,
    )
    session.add(solicitacao)
    session.commit()
    session.refresh(solicitacao)
    return solicitacao


def test_criar_solicitacao_exige_autenticacao(
    client: TestClient, categorias: dict[str, Categoria]
) -> None:
    """Sem JWT, a publicação de um pedido deve ser recusada."""
    resposta = client.post(
        "/solicitacoes",
        json={"titulo": "Pedido sem token", "categoria_id": categorias["agua"].id},
    )

    assert resposta.status_code == 401


def test_criar_solicitacao_autenticado(
    client: TestClient, usuario_ana: Usuario, categorias: dict[str, Categoria]
) -> None:
    """Com JWT, o pedido é criado e já volta enriquecido para o app."""
    headers = cabecalho_autenticado(client, usuario_ana.email)

    resposta = client.post(
        "/solicitacoes",
        json={
            "titulo": "Água potável para 4 famílias",
            "descricao": "Sem abastecimento há três dias.",
            "categoria_id": categorias["agua"].id,
            "quantidade": "50 litros",
            "urgencia": "alta",
            "pessoas_beneficiadas": 16,
            "emergencia": True,
        },
        headers=headers,
    )

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["titulo"] == "Água potável para 4 famílias"
    assert corpo["urgencia"] == "alta"
    assert corpo["emergencia"] is True
    assert corpo["categoria_nome"] == "Água"
    assert corpo["autor_nome"] == "Ana Ribeiro"
    # Sem coordenadas no payload, o pedido herda a localização do autor.
    assert corpo["latitude"] == usuario_ana.latitude


def test_criar_solicitacao_com_categoria_inexistente(
    client: TestClient, usuario_ana: Usuario
) -> None:
    """Categoria inválida deve ser barrada com 422."""
    headers = cabecalho_autenticado(client, usuario_ana.email)

    resposta = client.post(
        "/solicitacoes", json={"titulo": "Pedido inválido", "categoria_id": 999}, headers=headers
    )

    assert resposta.status_code == 422


def test_listagem_e_publica(
    client: TestClient, session: Session, usuario_ana: Usuario, categorias: dict[str, Categoria]
) -> None:
    """Visitantes (sem token) conseguem ver a lista de pedidos."""
    _criar_solicitacao(session, usuario_ana, categorias["agua"], titulo="Pedido público")

    resposta = client.get("/solicitacoes")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


def test_filtro_por_categoria(
    client: TestClient, session: Session, usuario_ana: Usuario, categorias: dict[str, Categoria]
) -> None:
    """O filtro `categoria_id` deve isolar apenas os pedidos daquela categoria."""
    _criar_solicitacao(session, usuario_ana, categorias["agua"], titulo="Preciso de água")
    _criar_solicitacao(session, usuario_ana, categorias["alimentos"], titulo="Preciso de comida")

    resposta = client.get(f"/solicitacoes?categoria_id={categorias['agua'].id}")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["titulo"] == "Preciso de água"


def test_filtro_por_urgencia(
    client: TestClient, session: Session, usuario_ana: Usuario, categorias: dict[str, Categoria]
) -> None:
    """O filtro de urgência deve devolver somente o nível pedido."""
    _criar_solicitacao(
        session, usuario_ana, categorias["agua"], titulo="Urgente", urgencia=Urgencia.ALTA
    )
    _criar_solicitacao(
        session, usuario_ana, categorias["agua"], titulo="Tranquilo", urgencia=Urgencia.BAIXA
    )

    corpo = client.get("/solicitacoes?urgencia=alta").json()

    assert [item["titulo"] for item in corpo] == ["Urgente"]


def test_filtro_por_status(
    client: TestClient, session: Session, usuario_ana: Usuario, categorias: dict[str, Categoria]
) -> None:
    """As abas de *Minhas solicitações* dependem do filtro por status."""
    _criar_solicitacao(session, usuario_ana, categorias["agua"], titulo="Ativa")
    _criar_solicitacao(
        session,
        usuario_ana,
        categorias["agua"],
        titulo="Concluída",
        status=StatusSolicitacao.CONCLUIDA,
    )

    corpo = client.get("/solicitacoes?status=concluida").json()

    assert [item["titulo"] for item in corpo] == ["Concluída"]


def test_busca_por_texto(
    client: TestClient, session: Session, usuario_ana: Usuario, categorias: dict[str, Categoria]
) -> None:
    """A barra de busca da tela Explorar procura no título e na descrição."""
    _criar_solicitacao(session, usuario_ana, categorias["agua"], titulo="Cobertores para o abrigo")
    _criar_solicitacao(session, usuario_ana, categorias["alimentos"], titulo="Cestas básicas")

    corpo = client.get("/solicitacoes?busca=cobertor").json()

    assert [item["titulo"] for item in corpo] == ["Cobertores para o abrigo"]


def test_ordenacao_por_distancia(
    client: TestClient,
    session: Session,
    usuario_ana: Usuario,
    usuario_carlos: Usuario,
    categorias: dict[str, Categoria],
) -> None:
    """Com `lat`/`long`, o pedido mais próximo vem primeiro e traz a distância."""
    _criar_solicitacao(
        session,
        usuario_carlos,
        categorias["agua"],
        titulo="Longe (Capão Redondo)",
        coordenadas=COORD_CAPAO_REDONDO,
    )
    _criar_solicitacao(
        session,
        usuario_carlos,
        categorias["agua"],
        titulo="Perto (Pinheiros)",
        coordenadas=COORD_PINHEIROS,
    )

    corpo = client.get(
        f"/solicitacoes?lat={usuario_ana.latitude}&long={usuario_ana.longitude}"
        "&ordenar_por=distancia"
    ).json()

    assert [item["titulo"] for item in corpo] == ["Perto (Pinheiros)", "Longe (Capão Redondo)"]
    assert corpo[0]["distancia_km"] < corpo[1]["distancia_km"]
    assert corpo[0]["distancia_formatada"] != "--"


def test_emergencia_fica_no_topo(
    client: TestClient,
    session: Session,
    usuario_ana: Usuario,
    usuario_carlos: Usuario,
    categorias: dict[str, Categoria],
) -> None:
    """O modo emergência fura a fila da ordenação por distância."""
    _criar_solicitacao(
        session,
        usuario_carlos,
        categorias["agua"],
        titulo="Perto e comum",
        coordenadas=COORD_PINHEIROS,
    )
    _criar_solicitacao(
        session,
        usuario_carlos,
        categorias["agua"],
        titulo="Longe mas emergência",
        coordenadas=COORD_CAPAO_REDONDO,
        emergencia=True,
    )

    corpo = client.get(
        f"/solicitacoes?lat={usuario_ana.latitude}&long={usuario_ana.longitude}"
    ).json()

    assert corpo[0]["titulo"] == "Longe mas emergência"


def test_detalhe_e_404_para_id_inexistente(client: TestClient) -> None:
    """Detalhe de um pedido que não existe deve responder 404."""
    assert client.get("/solicitacoes/999").status_code == 404


def test_somente_o_autor_pode_atualizar(
    client: TestClient,
    session: Session,
    usuario_ana: Usuario,
    usuario_carlos: Usuario,
    categorias: dict[str, Categoria],
) -> None:
    """Outro usuário não pode mudar o status do pedido alheio."""
    solicitacao = _criar_solicitacao(
        session, usuario_ana, categorias["agua"], titulo="Pedido da Ana"
    )
    headers_carlos = cabecalho_autenticado(client, usuario_carlos.email)

    resposta = client.patch(
        f"/solicitacoes/{solicitacao.id}", json={"status": "concluida"}, headers=headers_carlos
    )

    assert resposta.status_code == 403


def test_autor_atualiza_status(
    client: TestClient, session: Session, usuario_ana: Usuario, categorias: dict[str, Categoria]
) -> None:
    """O autor consegue mover o pedido entre as abas de status."""
    solicitacao = _criar_solicitacao(
        session, usuario_ana, categorias["agua"], titulo="Pedido da Ana"
    )
    headers = cabecalho_autenticado(client, usuario_ana.email)

    resposta = client.patch(
        f"/solicitacoes/{solicitacao.id}", json={"status": "em_andamento"}, headers=headers
    )

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "em_andamento"
