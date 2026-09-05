"""Testes do fluxo de autenticação (cadastro, login e JWT)."""

from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.models import Usuario
from backend.services.auth_service import (
    criar_access_token,
    decodificar_access_token,
    gerar_hash_senha,
    verificar_senha,
)


def test_registro_cria_usuario_e_devolve_token(client: TestClient) -> None:
    """O cadastro deve responder 201 com token e dados do usuário."""
    resposta = client.post(
        "/auth/register",
        json={
            "nome": "Nova Pessoa",
            "email": "nova@teste.com",
            "senha": "senha123",
            "tipo": "doador",
            "cidade": "São Paulo",
            "latitude": -23.55,
            "longitude": -46.63,
        },
    )

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["token_type"] == "bearer"
    assert corpo["access_token"]
    assert corpo["usuario"]["email"] == "nova@teste.com"
    # A senha nunca deve aparecer na resposta, em nenhum formato.
    assert "senha" not in corpo["usuario"]
    assert "senha_hash" not in corpo["usuario"]


def test_registro_rejeita_email_duplicado(client: TestClient, usuario_ana: Usuario) -> None:
    """Dois cadastros com o mesmo e-mail devem resultar em 409."""
    resposta = client.post(
        "/auth/register",
        json={"nome": "Outra Ana", "email": usuario_ana.email, "senha": "senha123"},
    )

    assert resposta.status_code == 409


def test_login_com_credenciais_validas(client: TestClient, usuario_ana: Usuario) -> None:
    """Login correto devolve 200 e um token utilizável."""
    resposta = client.post("/auth/login", json={"email": usuario_ana.email, "senha": "senha123"})

    assert resposta.status_code == 200
    assert resposta.json()["usuario"]["nome"] == "Ana Ribeiro"


def test_login_com_senha_errada(client: TestClient, usuario_ana: Usuario) -> None:
    """Senha incorreta deve resultar em 401."""
    resposta = client.post("/auth/login", json={"email": usuario_ana.email, "senha": "errada"})

    assert resposta.status_code == 401


def test_rota_me_exige_token(client: TestClient, usuario_ana: Usuario) -> None:
    """`/auth/me` responde 401 sem token e 200 com token válido."""
    assert client.get("/auth/me").status_code == 401

    token = client.post(
        "/auth/login", json={"email": usuario_ana.email, "senha": "senha123"}
    ).json()["access_token"]

    resposta = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resposta.status_code == 200
    assert resposta.json()["email"] == usuario_ana.email


def test_token_invalido_e_recusado(client: TestClient) -> None:
    """Um token forjado não deve autenticar ninguém."""
    resposta = client.get("/auth/me", headers={"Authorization": "Bearer token-invalido"})
    assert resposta.status_code == 401


def test_hash_de_senha_nao_guarda_texto_puro(session: Session) -> None:
    """O hash bcrypt precisa diferir da senha e validar corretamente."""
    hash_gerado = gerar_hash_senha("senha123")

    assert hash_gerado != "senha123"
    assert verificar_senha("senha123", hash_gerado) is True
    assert verificar_senha("outra", hash_gerado) is False


def test_ciclo_do_token_jwt() -> None:
    """O id codificado no token deve voltar íntegro na decodificação."""
    token = criar_access_token(42)

    assert decodificar_access_token(token) == 42
    assert decodificar_access_token("nao-e-um-jwt") is None
