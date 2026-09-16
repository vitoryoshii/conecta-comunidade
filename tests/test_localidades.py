"""Testes das rotas de estados e municípios (base IBGE em arquivo)."""

import pytest
from fastapi.testclient import TestClient

from backend.services import localidades_service


def test_lista_os_27_estados(client: TestClient) -> None:
    """A base precisa trazer as 26 UFs mais o Distrito Federal."""
    resposta = client.get("/localidades/estados")

    assert resposta.status_code == 200
    estados = resposta.json()
    assert len(estados) == 27
    assert {"sigla": "SP", "nome": "São Paulo"} in estados
    # Ordenados por nome: o Acre abre a lista.
    assert estados[0]["sigla"] == "AC"


def test_cidades_de_sao_paulo(client: TestClient) -> None:
    """SP tem 645 municípios, e a capital está entre eles."""
    resposta = client.get("/localidades/estados/SP/cidades")

    assert resposta.status_code == 200
    cidades = resposta.json()
    assert len(cidades) == 645

    nomes = [c["nome"] for c in cidades]
    assert "São Paulo" in nomes
    assert "Salvador" not in nomes


def test_toda_cidade_tem_coordenada(client: TestClient) -> None:
    """Nenhum município pode sair da API em (0, 0) — era a regressão a corrigir."""
    cidades = client.get("/localidades/estados/BA/cidades").json()

    assert all(c["lat"] != 0.0 and c["lng"] != 0.0 for c in cidades)

    salvador = next(c for c in cidades if c["nome"] == "Salvador")
    assert salvador["lat"] == pytest.approx(-12.97, abs=0.05)
    assert salvador["lng"] == pytest.approx(-38.50, abs=0.05)


def test_estado_inexistente_responde_404(client: TestClient) -> None:
    """Uma sigla que não existe não deve devolver lista vazia, e sim 404."""
    assert client.get("/localidades/estados/XX/cidades").status_code == 404


def test_cidade_precisa_pertencer_ao_estado() -> None:
    """O serviço rejeita o par trocado e normaliza o par correto."""
    with pytest.raises(ValueError):
        localidades_service.validar_estado_e_cidade("SP", "Salvador")

    local = localidades_service.validar_estado_e_cidade("ba", "salvador")
    assert (local.estado, local.cidade) == ("BA", "Salvador")
    assert local.latitude == pytest.approx(-12.97, abs=0.05)
    assert local.longitude == pytest.approx(-38.50, abs=0.05)

    # Sem região informada continua valendo: o cadastro não exige localização.
    assert localidades_service.validar_estado_e_cidade("", "") == ("", "", 0.0, 0.0)
