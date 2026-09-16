"""
Base de estados e municípios do IBGE, carregada de arquivo.

Os dados vêm de `backend/data/localidades.json`, gerado uma única vez por
`backend.scripts.gerar_localidades`. Ficam em memória a partir da primeira
consulta: são ~140 KB, e mantê-los carregados evita ler o disco a cada
requisição do cadastro.

A API **não** consulta o IBGE em tempo de execução — ver o docstring do script.
"""

from __future__ import annotations

import json
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

ARQUIVO = Path(__file__).resolve().parent.parent / "data" / "localidades.json"


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
    que a validação de cadastro não percorra 5.571 municípios a cada chamada.
    """
    dados = json.loads(ARQUIVO.read_text(encoding="utf-8"))

    por_sigla: dict[str, dict[str, Any]] = {}
    for estado in dados["estados"]:
        por_sigla[estado["sigla"]] = {
            "sigla": estado["sigla"],
            "nome": estado["nome"],
            "cidades": estado["cidades"],
            # nome normalizado -> nome oficial, para validar e normalizar juntos.
            "indice": {_normalizar(cidade): cidade for cidade in estado["cidades"]},
        }

    return {"estados": dados["estados"], "por_sigla": por_sigla}


def listar_estados() -> list[dict[str, str]]:
    """Os 27 estados (26 + DF), já ordenados por nome."""
    return [{"sigla": e["sigla"], "nome": e["nome"]} for e in _base()["estados"]]


def estado_existe(sigla: str) -> bool:
    """Indica se a sigla corresponde a uma UF conhecida."""
    return sigla.strip().upper() in _base()["por_sigla"]


def listar_cidades(sigla: str) -> list[str] | None:
    """Municípios da UF em ordem alfabética, ou `None` se a sigla não existir."""
    estado = _base()["por_sigla"].get(sigla.strip().upper())
    return list(estado["cidades"]) if estado else None


def nome_oficial_da_cidade(sigla: str, cidade: str) -> str | None:
    """Nome oficial do município dentro da UF, ou `None` se não pertencer a ela.

    Devolver o nome oficial (em vez de só um booleano) permite ao cadastro
    gravar "São Paulo" mesmo quando o cliente enviou "sao paulo".
    """
    estado = _base()["por_sigla"].get(sigla.strip().upper())
    if estado is None:
        return None
    return estado["indice"].get(_normalizar(cidade))


def validar_estado_e_cidade(estado: str, cidade: str) -> tuple[str, str]:
    """Valida o par informado no cadastro e devolve (sigla, nome oficial).

    Aceita os dois campos vazios — quem se cadastra sem informar a região fica
    sem localização, como antes. Informar só um dos dois é erro: sem a UF não dá
    para saber de qual "Bom Jesus" (são 11 no país) se trata.

    Levanta `ValueError` com mensagem pronta para virar 422 no router.
    """
    estado_limpo = estado.strip()
    cidade_limpa = cidade.strip()

    if not estado_limpo and not cidade_limpa:
        return "", ""
    if not estado_limpo:
        raise ValueError("Informe o estado da cidade escolhida.")
    if not cidade_limpa:
        raise ValueError("Informe a cidade do estado escolhido.")

    sigla = estado_limpo.upper()
    if not estado_existe(sigla):
        raise ValueError(f"Estado '{estado_limpo}' não existe.")

    oficial = nome_oficial_da_cidade(sigla, cidade_limpa)
    if oficial is None:
        raise ValueError(f"'{cidade_limpa}' não é um município de {sigla}.")

    return sigla, oficial
