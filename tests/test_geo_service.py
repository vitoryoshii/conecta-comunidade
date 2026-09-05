"""Testes do serviço de geolocalização (haversine e formatação)."""

import math

from backend.services.geo_service import (
    calcular_distancia_km,
    chave_ordenacao_distancia,
    coordenada_valida,
    formatar_distancia,
)

# Referências reais para conferir a ordem de grandeza do cálculo.
SAO_PAULO = (-23.5505, -46.6333)
RIO_DE_JANEIRO = (-22.9068, -43.1729)
VILA_MADALENA = (-23.5545, -46.6896)


def test_distancia_entre_ponto_e_ele_mesmo_e_zero() -> None:
    """A distância de um ponto para ele mesmo precisa ser exatamente zero."""
    assert calcular_distancia_km(*SAO_PAULO, *SAO_PAULO) == 0.0


def test_distancia_sao_paulo_rio() -> None:
    """São Paulo -> Rio de Janeiro fica em torno de 360 km em linha reta."""
    distancia = calcular_distancia_km(*SAO_PAULO, *RIO_DE_JANEIRO)

    assert distancia is not None
    assert 350 < distancia < 375


def test_distancia_curta_dentro_da_cidade() -> None:
    """Centro -> Vila Madalena deve ficar na casa de poucos quilômetros."""
    distancia = calcular_distancia_km(*SAO_PAULO, *VILA_MADALENA)

    assert distancia is not None
    assert 5 < distancia < 8


def test_distancia_e_simetrica() -> None:
    """A ordem dos pontos não pode alterar o resultado."""
    ida = calcular_distancia_km(*SAO_PAULO, *RIO_DE_JANEIRO)
    volta = calcular_distancia_km(*RIO_DE_JANEIRO, *SAO_PAULO)

    assert ida == volta


def test_coordenada_ausente_devolve_none() -> None:
    """Sem coordenada válida em uma das pontas, não existe distância."""
    assert calcular_distancia_km(None, None, *SAO_PAULO) is None
    assert calcular_distancia_km(*SAO_PAULO, 0.0, 0.0) is None


def test_validacao_de_coordenadas() -> None:
    """Latitudes/longitudes fora do intervalo válido são rejeitadas."""
    assert coordenada_valida(-23.55, -46.63) is True
    assert coordenada_valida(0.0, 0.0) is False
    assert coordenada_valida(91.0, 0.5) is False
    assert coordenada_valida(-23.55, 181.0) is False


def test_formatacao_da_distancia() -> None:
    """Abaixo de 1 km exibimos metros; acima, quilômetros com uma casa."""
    assert formatar_distancia(0.35) == "350 m"
    assert formatar_distancia(4.24) == "4,2 km"
    assert formatar_distancia(None) == "--"


def test_chave_de_ordenacao_joga_sem_coordenada_para_o_fim() -> None:
    """Registros sem distância devem ficar no fim de qualquer ordenação."""
    assert chave_ordenacao_distancia(2.5) == 2.5
    assert math.isinf(chave_ordenacao_distancia(None))
