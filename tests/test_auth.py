"""Testes do fluxo de autenticação (cadastro, login e JWT)."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.models import Usuario
from backend.services.auth_service import (
    criar_access_token,
    decodificar_access_token,
    gerar_hash_senha,
    verificar_senha,
)


# O cadastro passou a exigir dados pessoais e o aceite dos termos; estes campos
# completam qualquer payload de teste que não esteja exercitando justamente essa
# validação.
DADOS_PESSOAIS = {
    "cpf": "529.982.247-25",
    "telefone": "(11) 98765-4321",
    "data_nascimento": "1995-04-12",
    "aceite_termos": True,
}


def test_registro_cria_usuario_e_devolve_token(client: TestClient) -> None:
    """O cadastro deve responder 201 com token e dados do usuário."""
    resposta = client.post(
        "/auth/register",
        json={
            "nome": "Nova Pessoa",
            "email": "nova@teste.com",
            "senha": "senha123",
            "tipo": "doador",
            "estado": "SP",
            "cidade": "São Paulo",
            "latitude": -23.55,
            "longitude": -46.63,
            **DADOS_PESSOAIS,
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
        json={
            "nome": "Outra Ana",
            "email": usuario_ana.email,
            "senha": "senha123",
            **DADOS_PESSOAIS,
        },
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


def test_registro_grava_as_coordenadas_da_cidade(client: TestClient) -> None:
    """Quem se cadastra em Salvador nasce lá, não em (0, 0)."""
    resposta = client.post(
        "/auth/register",
        json={
            "nome": "Pessoa de Salvador",
            "email": "salvador@teste.com",
            "senha": "senha123",
            "estado": "BA",
            "cidade": "Salvador",
            **DADOS_PESSOAIS,
        },
    )

    assert resposta.status_code == 201, resposta.text
    usuario = resposta.json()["usuario"]
    assert usuario["latitude"] != 0.0
    assert usuario["longitude"] != 0.0
    assert usuario["latitude"] == pytest.approx(-12.97, abs=0.05)
    assert usuario["longitude"] == pytest.approx(-38.50, abs=0.05)


def test_registro_rejeita_cidade_que_nao_e_do_estado(client: TestClient) -> None:
    """Salvador é da Bahia: enviá-la como cidade de SP precisa dar 422."""
    resposta = client.post(
        "/auth/register",
        json={
            "nome": "Fora de Lugar",
            "email": "fora@teste.com",
            "senha": "senha123",
            "estado": "SP",
            "cidade": "Salvador",
            **DADOS_PESSOAIS,
        },
    )

    assert resposta.status_code == 422, resposta.text
    assert "SP" in resposta.json()["detail"]


def test_registro_normaliza_estado_e_cidade(client: TestClient) -> None:
    """Sigla em minúscula e cidade sem acento viram o dado oficial do IBGE."""
    resposta = client.post(
        "/auth/register",
        json={
            "nome": "Pessoa Baiana",
            "email": "baiana@teste.com",
            "senha": "senha123",
            **DADOS_PESSOAIS,
            "estado": "ba",
            "cidade": "salvador",
        },
    )

    assert resposta.status_code == 201, resposta.text
    usuario = resposta.json()["usuario"]
    assert usuario["estado"] == "BA"
    assert usuario["cidade"] == "Salvador"


def test_recuperar_senha_responde_igual_para_email_conhecido_e_desconhecido(
    client: TestClient, usuario_ana: Usuario
) -> None:
    """A rota nunca revela se o e-mail está cadastrado: mesmo status, mesmo texto."""
    cadastrado = client.post("/auth/recuperar-senha", json={"email": usuario_ana.email})
    desconhecido = client.post("/auth/recuperar-senha", json={"email": "ninguem@teste.com"})

    assert cadastrado.status_code == 200, cadastrado.text
    assert desconhecido.status_code == 200, desconhecido.text
    assert cadastrado.json() == desconhecido.json()
    assert cadastrado.json()["mensagem"]


def test_recuperar_senha_rejeita_email_invalido(client: TestClient) -> None:
    """Um e-mail malformado continua sendo barrado pela validação do Pydantic."""
    resposta = client.post("/auth/recuperar-senha", json={"email": "nao-e-email"})

    assert resposta.status_code == 422


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
