"""
Mapa interativo em Leaflet + OpenStreetMap.

O app desenha o mapa com tiles do OSM na própria tela (`mapa_tiles.py`), o que
já mostra as ruas — mas é uma imagem: não dá zoom nem arrasta. Este módulo gera
a versão **interativa**, uma página Leaflet com os mesmos pontos, aberta no
navegador pelo botão "Abrir mapa interativo".

Por que no navegador, e não dentro do app: o `ft.WebView` não existe no pacote
`flet` 0.86 (virou o pacote separado `flet-webview`), e o plugin de WebView do
Flutter não tem suporte a Windows desktop — que é onde o app é usado e
demonstrado. Abrir no navegador entrega o mapa interativo hoje, sem dependência
nova e sem uma tela que renderiza em branco.

O HTML é escrito em um arquivo temporário e aberto por URL `file://`. Os pontos
entram como JSON, nunca por interpolação de texto: título com aspas ou acento
não quebra a página nem injeta script.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Sequence

# Cores por tipo de ponto, espelhando `theme.CORES_MAPA` — o HTML é servido fora
# do app, então não importa o módulo de tema.
CORES = {
    "ajuda": "#E23B3B",
    "oferecendo": "#1FA96C",
    "ong": "#0E2A47",
    "ponto_retirada": "#F5A623",
}

ROTULOS = {
    "ajuda": "Precisa de ajuda",
    "oferecendo": "Oferecendo",
    "ong": "ONG",
    "ponto_retirada": "Ponto de retirada",
}

COR_PADRAO = "#1FA96C"

ZOOM_PADRAO = 13

# Leaflet servido por CDN. Sem chave de API, sem cadastro.
LEAFLET_CSS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
LEAFLET_JS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"

MODELO = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Conecta Comunidade — Mapa</title>
<link rel="stylesheet" href="{css}" />
<style>
  html, body {{ margin: 0; height: 100%; font-family: "Segoe UI", system-ui, sans-serif; }}
  #mapa {{ height: 100%; }}
  .pino {{
    width: 26px; height: 26px; border-radius: 50%;
    border: 2px solid #fff; box-shadow: 0 3px 8px rgba(0,0,0,.3);
    display: flex; align-items: center; justify-content: center;
    color: #fff; font-size: 12px; font-weight: 700;
  }}
  .legenda {{
    position: absolute; z-index: 1000; left: 12px; bottom: 22px;
    background: #fff; border-radius: 14px; padding: 10px 12px;
    box-shadow: 0 6px 18px rgba(0,0,0,.12); font-size: 12px; color: #122C1E;
  }}
  .legenda div {{ display: flex; align-items: center; gap: 8px; margin: 3px 0; }}
  .legenda i {{ width: 11px; height: 11px; border-radius: 50%; display: inline-block; }}
  .titulo-popup {{ font-weight: 700; color: #122C1E; }}
  .meta-popup {{ color: #6B7B72; }}
</style>
</head>
<body>
<div id="mapa"></div>
<div class="legenda">{legenda}</div>
<script src="{js}"></script>
<script>
  var pontos = {pontos};
  var cores = {cores};

  // `fadeAnimation: false` não é enfeite: o fade do Leaflet depende de
  // `requestAnimationFrame`, que não roda enquanto a aba está em segundo plano
  // — os tiles chegam a carregar, mas ficam presos em `opacity: 0` e a página
  // parece um mapa vazio. Sem o fade, eles aparecem assim que baixam.
  var mapa = L.map('mapa', {{ fadeAnimation: false }}).setView([{lat}, {lng}], {zoom});
  L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  }}).addTo(mapa);

  var marcadores = [];
  pontos.forEach(function (ponto) {{
    var cor = ponto.emergencia ? '#E23B3B' : (cores[ponto.tipo] || '{cor_padrao}');
    var icone = L.divIcon({{
      className: '',
      html: '<div class="pino" style="background:' + cor + '">' +
            (ponto.emergencia ? '!' : '') + '</div>',
      iconSize: [26, 26],
      iconAnchor: [13, 13],
      popupAnchor: [0, -14]
    }});

    var marcador = L.marker([ponto.latitude, ponto.longitude], {{ icon: icone }}).addTo(mapa);
    // `textContent` em vez de HTML montado à mão: o título vem do banco e não
    // pode virar marcação dentro do popup.
    var caixa = document.createElement('div');
    var titulo = document.createElement('div');
    titulo.className = 'titulo-popup';
    titulo.textContent = ponto.titulo || '';
    var meta = document.createElement('div');
    meta.className = 'meta-popup';
    meta.textContent = [ponto.rotulo, ponto.distancia].filter(Boolean).join(' · ');
    caixa.appendChild(titulo);
    caixa.appendChild(meta);
    marcador.bindPopup(caixa);

    // O app lê este hash quando (e se) a página rodar dentro de um WebView: é
    // o canal mais simples de "toquei no pino de id X".
    marcador.on('click', function () {{
      window.location.hash = 'ponto-' + ponto.tipo + '-' + ponto.id;
    }});
    marcadores.push(marcador);
  }});

  if (marcadores.length > 1) {{
    mapa.fitBounds(L.featureGroup(marcadores).getBounds().pad(0.2));
  }}
</script>
</body>
</html>
"""


def _json_para_script(valor: Any) -> str:
    """Serializa em JSON seguro para colocar **dentro** de uma tag `<script>`.

    `json.dumps` escapa aspas, mas não `<`: um título contendo `</script>`
    fecharia a tag no meio do JSON, e o resto do texto passaria a ser lido como
    HTML pelo navegador. Escapando os três caracteres perigosos em notação
    unicode, o JavaScript recebe exatamente o mesmo texto e a tag não tem como
    ser fechada de dentro do dado.
    """
    bruto = json.dumps(valor, ensure_ascii=False)
    # As sequências vão para o arquivo como texto (barra invertida + u003c):
    # é o JavaScript que as lê de volta como '<' ao interpretar a string.
    return (
        bruto.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def _legenda(tipos: Sequence[str]) -> str:
    """Quadro de legenda com as cores dos tipos presentes no mapa."""
    linhas = [
        f'<div><i style="background:{CORES.get(tipo, COR_PADRAO)}"></i>{ROTULOS.get(tipo, tipo)}</div>'
        for tipo in tipos
    ]
    return "".join(linhas) or "<div>Nenhum ponto com os filtros atuais</div>"


def montar_html(
    pontos: Sequence[dict[str, Any]],
    centro: tuple[float, float],
    zoom: int = ZOOM_PADRAO,
) -> str:
    """Página Leaflet completa, com os pontos já embutidos."""
    dados = [
        {
            "id": ponto.get("id"),
            "tipo": ponto.get("tipo", "ajuda"),
            "titulo": ponto.get("titulo", ""),
            "rotulo": ROTULOS.get(ponto.get("tipo", ""), ""),
            "distancia": ponto.get("distancia_formatada", ""),
            "emergencia": bool(ponto.get("emergencia")),
            "latitude": ponto.get("latitude"),
            "longitude": ponto.get("longitude"),
        }
        for ponto in pontos
        if ponto.get("latitude") is not None and ponto.get("longitude") is not None
    ]

    tipos_presentes = list(dict.fromkeys(p["tipo"] for p in dados))

    return MODELO.format(
        css=LEAFLET_CSS,
        js=LEAFLET_JS,
        pontos=_json_para_script(dados),
        cores=_json_para_script(CORES),
        legenda=_legenda(tipos_presentes),
        lat=centro[0],
        lng=centro[1],
        zoom=zoom,
        cor_padrao=COR_PADRAO,
    )


def salvar_html(conteudo: str) -> Path:
    """Grava a página em um arquivo temporário e devolve o caminho."""
    # `delete=False` porque o navegador abre o arquivo depois que esta função
    # retorna; o sistema limpa a pasta temporária por conta própria.
    with tempfile.NamedTemporaryFile(
        "w", suffix=".html", prefix="conecta-mapa-", delete=False, encoding="utf-8"
    ) as arquivo:
        arquivo.write(conteudo)
        return Path(arquivo.name)


def url_do_mapa(
    pontos: Sequence[dict[str, Any]],
    centro: tuple[float, float],
    zoom: int = ZOOM_PADRAO,
) -> str:
    """Gera a página e devolve a URL `file://` para abrir no navegador."""
    return salvar_html(montar_html(pontos, centro, zoom)).as_uri()
