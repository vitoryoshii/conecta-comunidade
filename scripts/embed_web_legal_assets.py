"""Inclui os Markdown legais no filesystem Python do artefato Web Flet.

O Flet copia assets para a raiz HTTP da PWA, mas o Pyodide executa o app a
partir de ``assets/app/app.zip``. Documentos que o Python lê com ``pathlib``
precisam estar neste ZIP, além da cópia estática opcional do Flet.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile


NOMES = ("termos-de-uso.md", "politica-de-privacidade.md")
PREFIXO = "assets/legal/"


def incorporar(app_zip: Path, diretorio_legal: Path) -> None:
    """Regrava ``app.zip`` sem duplicatas e com os dois documentos oficiais."""
    if not app_zip.is_file():
        raise FileNotFoundError(f"app.zip ausente: {app_zip}")
    documentos = {nome: diretorio_legal / nome for nome in NOMES}
    ausentes = [str(caminho) for caminho in documentos.values() if not caminho.is_file()]
    if ausentes:
        raise FileNotFoundError("Documento legal ausente: " + ", ".join(ausentes))

    with NamedTemporaryFile(delete=False, suffix=".zip", dir=app_zip.parent) as temporario:
        destino = Path(temporario.name)
    try:
        with ZipFile(app_zip) as origem, ZipFile(destino, "w", ZIP_DEFLATED) as saida:
            for entrada in origem.infolist():
                if entrada.filename not in {PREFIXO + nome for nome in NOMES}:
                    saida.writestr(entrada, origem.read(entrada.filename))
            for nome, caminho in documentos.items():
                saida.writestr(PREFIXO + nome, caminho.read_bytes())
        shutil.move(destino, app_zip)
    finally:
        destino.unlink(missing_ok=True)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Uso: embed_web_legal_assets.py <app.zip> <assets/legal>")
    incorporar(Path(sys.argv[1]), Path(sys.argv[2]))
