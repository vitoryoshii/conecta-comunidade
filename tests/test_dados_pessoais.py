"""Testes de CPF, telefone e data de nascimento no cadastro."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from backend.models import Usuario
from backend.services import dados_pessoais_service as dados

# CPF válido usado como base nos cadastros de teste.
CPF_VALIDO = "529.982.247-25"


def _payload(**sobrescrever) -> dict:
    """Cadastro completo e válido, com os campos que o teste quiser trocar."""
    base = {
        "nome": "Pessoa de Teste",
        "email": "pessoa@teste.com",
        "senha": "senha123",
        "cpf": CPF_VALIDO,
        "telefone": "(11) 98765-4321",
        "data_nascimento": "1995-04-12",
        "estado": "SP",
        "cidade": "São Paulo",
    }
    base.update(sobrescrever)
    return base


# --------------------------------------------------------------------------- #
# Regras de validação, isoladas do HTTP
# --------------------------------------------------------------------------- #
def test_cpf_confere_o_digito_verificador() -> None:
    """Um dígito trocado invalida o CPF — não basta ter 11 números."""
    assert dados.cpf_valido("529.982.247-25") is True
    assert dados.cpf_valido("529.982.247-24") is False
    assert dados.cpf_valido("5299822472") is False


def test_cpf_rejeita_sequencia_de_digito_repetido() -> None:
    """111.111.111-11 passa no módulo 11, mas não é um CPF real."""
    for repetido in ("11111111111", "00000000000", "99999999999"):
        assert dados.cpf_valido(repetido) is False


def test_telefone_exige_ddd_existente_e_tamanho_certo() -> None:
    """DDD inexistente e tamanho errado são recusados."""
    assert dados.validar_telefone("(11) 98765-4321") == "11987654321"
    assert dados.validar_telefone("11 3333-4444") == "1133334444"

    for invalido in ("(10) 98765-4321", "11987654", "119876543210"):
        with pytest.raises(ValueError):
            dados.validar_telefone(invalido)


def test_idade_minima_e_data_futura() -> None:
    """Menor de 18 e data no futuro são recusados."""
    hoje = date(2026, 9, 16)

    assert dados.validar_data_de_nascimento(date(2008, 9, 16), hoje) == date(2008, 9, 16)

    with pytest.raises(ValueError):
        # Um dia antes de completar 18 anos.
        dados.validar_data_de_nascimento(date(2008, 9, 17), hoje)
    with pytest.raises(ValueError):
        dados.validar_data_de_nascimento(date(2030, 1, 1), hoje)


def test_mascara_esconde_os_digitos_identificadores() -> None:
    """A máscara mostra o miolo e esconde começo e fim."""
    assert dados.mascarar_cpf("52998224725") == "***.982.247-**"
    assert dados.mascarar_cpf("123") is None


# --------------------------------------------------------------------------- #
# Cadastro pela API
# --------------------------------------------------------------------------- #
def test_cadastro_completo_persiste_os_dados_normalizados(client: TestClient) -> None:
    """CPF e telefone são gravados só com dígitos, sem a máscara digitada."""
    resposta = client.post("/auth/register", json=_payload())

    assert resposta.status_code == 201, resposta.text
    token = resposta.json()["access_token"]

    eu = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    # A máscara comprova que o número guardado tem os dígitos certos.
    assert eu["cpf"] == "***.982.247-**"
    assert eu["telefone"] == "11987654321"
    assert eu["data_nascimento"] == "1995-04-12"


def test_cadastro_rejeita_cpf_com_digito_errado(client: TestClient) -> None:
    """CPF com verificador inválido responde 422."""
    resposta = client.post("/auth/register", json=_payload(cpf="529.982.247-24"))

    assert resposta.status_code == 422, resposta.text
    assert "CPF" in resposta.json()["detail"]


def test_cadastro_rejeita_cpf_ja_usado(client: TestClient) -> None:
    """O segundo cadastro com o mesmo CPF responde 409 com mensagem clara."""
    assert client.post("/auth/register", json=_payload()).status_code == 201

    repetido = client.post(
        "/auth/register", json=_payload(email="outra@teste.com")
    )

    assert repetido.status_code == 409, repetido.text
    assert "CPF" in repetido.json()["detail"]


def test_cadastro_rejeita_menor_de_idade(client: TestClient) -> None:
    """Quem não tem 18 anos não entra."""
    nascimento = date.today().replace(year=date.today().year - 15).isoformat()
    resposta = client.post("/auth/register", json=_payload(data_nascimento=nascimento))

    assert resposta.status_code == 422, resposta.text
    assert "18" in resposta.json()["detail"]


def test_cadastro_rejeita_telefone_malformado(client: TestClient) -> None:
    """Telefone sem DDD válido responde 422."""
    resposta = client.post("/auth/register", json=_payload(telefone="(10) 98765-4321"))

    assert resposta.status_code == 422, resposta.text


# --------------------------------------------------------------------------- #
# Vazamento de dado pessoal
# --------------------------------------------------------------------------- #
def test_perfil_publico_nao_expoe_dados_pessoais(
    client: TestClient, usuario_ana: Usuario
) -> None:
    """`GET /usuarios/{id}` é público: não pode trazer CPF, telefone nem idade."""
    resposta = client.get(f"/usuarios/{usuario_ana.id}")

    assert resposta.status_code == 200
    corpo = resposta.json()
    for campo in ("cpf", "telefone", "data_nascimento", "senha_hash"):
        assert campo not in corpo, f"{campo} vazou no perfil público"


def test_cpf_nunca_sai_completo_da_api(client: TestClient) -> None:
    """Nem o dono recebe o CPF inteiro — só a versão mascarada."""
    token = client.post("/auth/register", json=_payload()).json()["access_token"]

    eu = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert "52998224725" not in eu.text
    assert eu.json()["cpf"] == "***.982.247-**"
