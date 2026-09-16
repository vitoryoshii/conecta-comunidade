"""
Base de estados e municípios do IBGE, carregada de arquivo.

Os dados vêm de `backend/data/localidades.json`, gerado uma única vez por
`backend.scripts.gerar_localidades`, e trazem a latitude/longitude da sede de
cada município. Ficam em memória a partir da primeira consulta: são poucas
centenas de KB, e mantê-los carregados evita ler o disco a cada requisição.

A API **não** consulta serviço externo em tempo de execução — ver o docstring
do script.
"""

from __future__ import annotations

import json
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, NamedTuple

ARQUIVO = Path(__file__).resolve().parent.parent / "data" / "localidades.json"


class Localizacao(NamedTuple):
    """Região validada de um usuário, pronta para gravar."""

    estado: str
    cidade: str
    latitude: float
    longitude: float


# Usuário sem região informada: o cadastro não exige localização.
SEM_LOCALIZACAO = Localizacao("", "", 0.0, 0.0)


def _normalizar(texto: str) -> str:
    """Forma comparável de um nome: sem acento, sem caixa, sem sobras de espaço.

    Serve para aceitar "sao paulo" ou "SÃO PAULO" na validação sem que o dado
    gravado deixe de ser o nome oficial do IBGE.
    """
    sem_acento = unicodedata.normalize("NFKD", texto.strip())
    return "".join(c for c in sem_acento if not unicodedata.combining(c)).casefold()


@lru_cache(maxsize=1)
def _base() -> dict[str, Any]:
    """Conteúdo do arquivo, lido uma única vez por processo.

    O índice por sigla e o índice de nomes normalizados são montados aqui para
    que a validação de cadastro não percorra milhares de municípios a cada
    chamada.
    """
    dados = json.loads(ARQUIVO.read_text(encoding="utf-8"))

    por_sigla: dict[str, dict[str, Any]] = {}
    for estado in dados["estados"]:
        por_sigla[estado["sigla"]] = {
            "sigla": estado["sigla"],
            "nome": estado["nome"],
            "cidades": estado["cidades"],
            # nome normalizado -> registro da cidade (nome oficial + coordenadas)
            "indice": {_normalizar(c["nome"]): c for c in estado["cidades"]},
        }

    return {"estados": dados["estados"], "por_sigla": por_sigla}


def listar_estados() -> list[dict[str, str]]:
    """Os 27 estados (26 + DF), já ordenados por nome."""
    return [{"sigla": e["sigla"], "nome": e["nome"]} for e in _base()["estados"]]


def estado_existe(sigla: str) -> bool:
    """Indica se a sigla corresponde a uma UF conhecida."""
    return sigla.strip().upper() in _base()["por_sigla"]


def listar_cidades(sigla: str) -> list[dict[str, Any]] | None:
    """Municípios da UF (nome e coordenadas), ou `None` se a sigla não existir."""
    estado = _base()["por_sigla"].get(sigla.strip().upper())
    return list(estado["cidades"]) if estado else None


def buscar_cidade(sigla: str, cidade: str) -> dict[str, Any] | None:
    """Registro do município dentro da UF, ou `None` se não pertencer a ela."""
    estado = _base()["por_sigla"].get(sigla.strip().upper())
    if estado is None:
        return None
    return estado["indice"].get(_normalizar(cidade))


def validar_estado_e_cidade(estado: str, cidade: str) -> Localizacao:
    """Valida o par informado no cadastro e devolve a localização a gravar.

    Aceita os dois campos vazios — quem se cadastra sem informar a região fica
    sem localização, como antes. Informar só um dos dois é erro: sem a UF não dá
    para saber de qual "Bom Jesus" (são 11 no país) se trata.

    As coordenadas saem da própria base, e não do que o cliente enviou: é o que
    garante que ninguém mais seja gravado em (0, 0).

    Levanta `ValueError` com mensagem pronta para virar 422 no router.
    """
    estado_limpo = estado.strip()
    cidade_limpa = cidade.strip()

    if not estado_limpo and not cidade_limpa:
        return SEM_LOCALIZACAO
    if not estado_limpo:
        raise ValueError("Informe o estado da cidade escolhida.")
    if not cidade_limpa:
        raise ValueError("Informe a cidade do estado escolhido.")

    sigla = estado_limpo.upper()
    if not estado_existe(sigla):
        raise ValueError(f"Estado '{estado_limpo}' não existe.")

    encontrada = buscar_cidade(sigla, cidade_limpa)
    if encontrada is None:
        raise ValueError(f"'{cidade_limpa}' não é um município de {sigla}.")

    return Localizacao(sigla, encontrada["nome"], encontrada["lat"], encontrada["lng"])
