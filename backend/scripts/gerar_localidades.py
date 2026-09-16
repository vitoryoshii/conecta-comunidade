"""
Gera `backend/data/localidades.json` a partir da API de localidades do IBGE.

Roda **uma vez**, manualmente, e o JSON resultante é versionado junto do código:

    python -m backend.scripts.gerar_localidades

A razão de congelar os dados em arquivo é que a API não deve depender do IBGE em
tempo de execução — a divisão político-administrativa muda raramente, e uma
indisponibilidade do serviço externo não pode derrubar o cadastro do app.

Para atualizar a base (criação ou renomeação de municípios), rode o script de
novo e versione o JSON alterado.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import httpx

URL_ESTADOS = "https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=nome"
URL_MUNICIPIOS = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf_id}/municipios"

DESTINO = Path(__file__).resolve().parent.parent / "data" / "localidades.json"

# O IBGE pode demorar para responder a lista de municípios dos estados grandes.
TIMEOUT_SEGUNDOS = 60.0


def _ordenar_por_nome(itens: list[str]) -> list[str]:
    """Ordem alfabética tolerante a acentos ("Águas" junto de "Aguas")."""
    import unicodedata

    def chave(texto: str) -> str:
        sem_acento = unicodedata.normalize("NFKD", texto)
        return "".join(c for c in sem_acento if not unicodedata.combining(c)).casefold()

    return sorted(itens, key=chave)


def baixar() -> dict[str, Any]:
    """Baixa estados e municípios e monta a estrutura final do arquivo."""
    with httpx.Client(timeout=TIMEOUT_SEGUNDOS) as http:
        resposta = http.get(URL_ESTADOS)
        resposta.raise_for_status()
        estados_ibge = resposta.json()

        estados: list[dict[str, Any]] = []
        for estado in estados_ibge:
            municipios = http.get(URL_MUNICIPIOS.format(uf_id=estado["id"]))
            municipios.raise_for_status()
            cidades = _ordenar_por_nome([m["nome"] for m in municipios.json()])

            print(f"  {estado['sigla']} {estado['nome']}: {len(cidades)} municípios")
            estados.append(
                {"sigla": estado["sigla"], "nome": estado["nome"], "cidades": cidades}
            )

    # A API já devolve os estados por nome, mas reordenamos para o arquivo não
    # depender do parâmetro `orderBy` continuar existindo.
    estados.sort(key=lambda e: e["nome"])
    return {"estados": estados}


def main() -> int:
    """Baixa os dados e grava o JSON, relatando o total no final."""
    print("Baixando localidades do IBGE...")
    dados = baixar()

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    total_cidades = sum(len(e["cidades"]) for e in dados["estados"])
    print(f"\n{len(dados['estados'])} estados e {total_cidades} municípios")
    print(f"Gravado em {DESTINO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
