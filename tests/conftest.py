"""
Fixtures compartilhadas pelos testes.

Cada teste roda contra um banco SQLite **em memória**, criado do zero e
descartado ao final — nenhum teste enxerga dados de outro, e o `conecta.db` de
desenvolvimento nunca é tocado.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from backend.database import get_session
from backend.main import app
from backend.models import ONG, Categoria, Usuario
from backend.services import auth_service
from backend.services.auth_service import gerar_hash_senha

# Coordenadas fixas usadas nos testes de distância (bairros de São Paulo).
COORD_VILA_MADALENA = (-23.5545, -46.6896)
COORD_PINHEIROS = (-23.5670, -46.7020)
COORD_CAPAO_REDONDO = (-23.6600, -46.7700)


@pytest.fixture(scope="session", autouse=True)
def _bcrypt_rapido() -> None:
    """Reduz o custo do bcrypt durante os testes.

    Em produção o algoritmo precisa ser lento (é essa a defesa contra força
    bruta), mas 12 rounds custam ~0,4 s por hash — o que tornaria a suíte
    desnecessariamente demorada. Aqui usamos o mínimo aceito pela biblioteca:
    o comportamento testado é o mesmo, apenas mais barato.
    """
    auth_service.contexto_senha.update(bcrypt__rounds=4)


@pytest.fixture(name="session")
def fixture_session() -> Generator[Session, None, None]:
    """Sessão ligada a um banco SQLite em memória, isolado por teste."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        # StaticPool mantém a MESMA conexão: sem isso, cada checkout criaria um
        # banco em memória novo e vazio.
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def fixture_client(session: Session) -> Generator[TestClient, None, None]:
    """Cliente HTTP do FastAPI apontando para a sessão de teste."""

    def obter_sessao_de_teste() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_session] = obter_sessao_de_teste
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="categorias")
def fixture_categorias(session: Session) -> dict[str, Categoria]:
    """Duas categorias mínimas para os testes de solicitação e oferta."""
    agua = Categoria(nome="Água", icone="water_drop")
    alimentos = Categoria(nome="Alimentos", icone="restaurant")
    session.add(agua)
    session.add(alimentos)
    session.commit()
    session.refresh(agua)
    session.refresh(alimentos)
    return {"agua": agua, "alimentos": alimentos}


@pytest.fixture(name="usuario_ana")
def fixture_usuario_ana(session: Session) -> Usuario:
    """Solicitante localizada na Vila Madalena."""
    usuario = Usuario(
        nome="Ana Ribeiro",
        email="ana@teste.com",
        senha_hash=gerar_hash_senha("senha123"),
        estado="SP",
        cidade="São Paulo",
        latitude=COORD_VILA_MADALENA[0],
        longitude=COORD_VILA_MADALENA[1],
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@pytest.fixture(name="usuario_carlos")
def fixture_usuario_carlos(session: Session) -> Usuario:
    """Doador localizado em Pinheiros."""
    usuario = Usuario(
        nome="Carlos Mendes",
        email="carlos@teste.com",
        senha_hash=gerar_hash_senha("senha123"),
        estado="SP",
        cidade="São Paulo",
        latitude=COORD_PINHEIROS[0],
        longitude=COORD_PINHEIROS[1],
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@pytest.fixture(name="ong_verificada")
def fixture_ong_verificada(session: Session) -> ONG:
    """Instituição verificada usada nos testes de listagem e avaliação."""
    ong = ONG(
        nome="Instituto Semear",
        descricao="Distribuição de cestas básicas.",
        avaliacao=4.0,
        total_avaliacoes=10,
        verificada=True,
        recursos_disponiveis=[{"nome": "Cestas básicas", "quantidade": 100}],
        endereco="Centro - São Paulo/SP",
        latitude=-23.5460,
        longitude=-46.6360,
    )
    session.add(ong)
    session.commit()
    session.refresh(ong)
    return ong


def cabecalho_autenticado(client: TestClient, email: str, senha: str = "senha123") -> dict[str, str]:
    """Faz login e devolve o header `Authorization` pronto para uso."""
    resposta = client.post("/auth/login", json={"email": email, "senha": senha})
    assert resposta.status_code == 200, resposta.text
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}
