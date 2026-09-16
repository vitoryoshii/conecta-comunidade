"""
Gera `backend/data/localidades.json` com estados, municípios e coordenadas.

Roda **uma vez**, manualmente, e o JSON resultante é versionado junto do código:

    python -m backend.scripts.gerar_localidades

A razão de congelar os dados em arquivo é que a API não deve depender de serviço
externo em tempo de execução — a divisão político-administrativa muda raramente,
e uma indisponibilidade de terceiro não pode derrubar o cadastro do app.

------------------------------------------------------------------------------
Fontes
------------------------------------------------------------------------------
* **Estados e municípios** (nomes oficiais e códigos): API de localidades do
  IBGE. É a fonte de verdade da lista — nenhum município entra no arquivo sem
  estar aqui.
* **Coordenadas**: dataset público `kelvins/municipios-brasileiros`, que publica
  a latitude/longitude da **sede** de cada município indexada pelo código do
  IBGE. O cruzamento é feito pelo código, não pelo nome, então grafia e acentos
  não influem.

Por que não a malha do IBGE: a API de malhas devolve o polígono do município, e
o centroide dele cai longe da sede em municípios grandes (medimos 62 km em
Barreiras/BA, 11 km em Salvador). A sede é o ponto certo para "pedidos próximos".

Municípios sem coordenada na fonte caem para a coordenada da capital do estado,
e o script informa quantos foram.
"""

from __future__ import annotations

import csv
import io
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any

import httpx

URL_ESTADOS = "https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=nome"
URL_MUNICIPIOS = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf_id}/municipios"
# O mesmo arquivo em dois espelhos: a rede daqui oscila com o raw do GitHub, e
# o script tenta o próximo da lista quando um falha.
URLS_COORDENADAS = (
    "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv",
    "https://cdn.jsdelivr.net/gh/kelvins/municipios-brasileiros@main/csv/municipios.csv",
)

# Quantas vezes insistir em cada espelho antes de passar para o seguinte.
TENTATIVAS_POR_ESPELHO = 3

DESTINO = Path(__file__).resolve().parent.parent / "data" / "localidades.json"

# O IBGE pode demorar para responder a lista de municípios dos estados grandes.
TIMEOUT_SEGUNDOS = 60.0


def _chave_de_ordem(texto: str) -> str:
    """Ordem alfabética tolerante a acentos ("Águas" junto de "Aguas")."""
    sem_acento = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sem_acento if not unicodedata.combining(c)).casefold()


def _baixar_com_espelhos(http: httpx.Client, urls: tuple[str, ...]) -> httpx.Response:
    """Tenta cada espelho algumas vezes e devolve a primeira resposta boa."""
    ultimo_erro: Exception | None = None

    for url in urls:
        for tentativa in range(1, TENTATIVAS_POR_ESPELHO + 1):
            try:
                resposta = http.get(url, follow_redirects=True)
                resposta.raise_for_status()
                return resposta
            except (httpx.HTTPError, httpx.StreamError) as erro:
                ultimo_erro = erro
                print(f"  falha em {url} (tentativa {tentativa}): {type(erro).__name__}")

    raise RuntimeError(
        "Nenhum espelho de coordenadas respondeu. Rode o script de novo quando "
        f"a rede estabilizar. Último erro: {ultimo_erro}"
    )


def baixar_coordenadas(http: httpx.Client) -> tuple[dict[str, tuple[float, float]], dict[int, tuple[float, float]]]:
    """Coordenadas da sede por código do IBGE, e a da capital por código de UF."""
    resposta = _baixar_com_espelhos(http, URLS_COORDENADAS)

    por_municipio: dict[str, tuple[float, float]] = {}
    capital_por_uf: dict[int, tuple[float, float]] = {}

    for linha in csv.DictReader(io.StringIO(resposta.text)):
        ponto = (float(linha["latitude"]), float(linha["longitude"]))
        por_municipio[linha["codigo_ibge"]] = ponto
        if linha["capital"] == "1":
            capital_por_uf[int(linha["codigo_uf"])] = ponto

    return por_municipio, capital_por_uf


def baixar() -> tuple[dict[str, Any], int]:
    """Monta a estrutura final do arquivo e conta os municípios sem coordenada."""
    with httpx.Client(timeout=TIMEOUT_SEGUNDOS) as http:
        print("Baixando coordenadas das sedes...")
        coordenadas, capitais = baixar_coordenadas(http)
        print(f"  {len(coordenadas)} municípios com coordenada, {len(capitais)} capitais")

        print("Baixando estados e municípios do IBGE...")
        resposta = http.get(URL_ESTADOS)
        resposta.raise_for_status()
        estados_ibge = resposta.json()

        estados: list[dict[str, Any]] = []
        sem_coordenada = 0

        for estado in estados_ibge:
            municipios = http.get(URL_MUNICIPIOS.format(uf_id=estado["id"]))
            municipios.raise_for_status()

            fallback = capitais.get(estado["id"], (0.0, 0.0))
            cidades: list[dict[str, Any]] = []
            faltando_no_estado = 0

            for municipio in municipios.json():
                ponto = coordenadas.get(str(municipio["id"]))
                if ponto is None:
                    # Município novo, ainda ausente do dataset de coordenadas:
                    # a capital da UF erra menos do que (0, 0).
                    ponto = fallback
                    faltando_no_estado += 1
                cidades.append(
                    {"nome": municipio["nome"], "lat": ponto[0], "lng": ponto[1]}
                )

            cidades.sort(key=lambda c: _chave_de_ordem(c["nome"]))
            sem_coordenada += faltando_no_estado

            aviso = f"  ({faltando_no_estado} sem coordenada)" if faltando_no_estado else ""
            print(f"  {estado['sigla']} {estado['nome']}: {len(cidades)} municípios{aviso}")

            estados.append(
                {"sigla": estado["sigla"], "nome": estado["nome"], "cidades": cidades}
            )

    # A API já devolve os estados por nome, mas reordenamos para o arquivo não
    # depender do parâmetro `orderBy` continuar existindo.
    estados.sort(key=lambda e: _chave_de_ordem(e["nome"]))
    return {"estados": estados}, sem_coordenada


def main() -> int:
    """Baixa os dados e grava o JSON, relatando os totais no final."""
    dados, sem_coordenada = baixar()

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    total = sum(len(e["cidades"]) for e in dados["estados"])
    print(f"\n{len(dados['estados'])} estados e {total} municípios")
    if sem_coordenada:
        print(f"{sem_coordenada} sem coordenada própria (usaram a capital da UF)")
    else:
        print("todos com coordenada própria")
    print(f"Gravado em {DESTINO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
