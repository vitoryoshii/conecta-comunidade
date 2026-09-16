"""
Textos dos documentos legais exibidos no app.

Os arquivos em `mobile/assets/legal/` são a **única** fonte do conteúdo: quem
revisa os Termos ou a Política mexe no `.md` e o app acompanha, sem ninguém
precisar lembrar de atualizar uma cópia em Python. A leitura é feita direto do
disco com `pathlib`, e não pelo servidor de assets do Flet, porque o app roda o
Python na própria máquina — assim o texto está disponível no momento em que a
tela é montada, sem requisição nenhuma.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

PASTA = Path(__file__).resolve().parent / "assets" / "legal"

# chave da rota -> (título exibido, arquivo em assets/legal)
DOCUMENTOS: dict[str, tuple[str, str]] = {
    "termos": ("Termos de Uso", "termos-de-uso.md"),
    "privacidade": ("Política de Privacidade", "politica-de-privacidade.md"),
}

# Documento aberto quando a rota chega sem dizer qual.
PADRAO = "termos"

# Exibido se o arquivo não for encontrado (empacotamento incompleto, por
# exemplo). Mostrar o caminho e o contato é mais útil do que uma tela vazia —
# e deixa claro que o documento existe, mesmo que esta cópia não o encontre.
AVISO_DE_FALTA = (
    "## Documento indisponível\n\n"
    "Não foi possível carregar este documento nesta instalação do aplicativo.\n\n"
    "Você pode solicitá-lo por e-mail: **caio.cacalho@al.ibta.edu.br**."
)


def titulo(chave: str) -> str:
    """Título do documento, usado no cabeçalho da tela."""
    nome, _ = DOCUMENTOS.get(chave, DOCUMENTOS[PADRAO])
    return nome


@lru_cache(maxsize=None)
def texto(chave: str) -> str:
    """Conteúdo Markdown do documento, lido uma única vez por execução."""
    _, arquivo = DOCUMENTOS.get(chave, DOCUMENTOS[PADRAO])
    caminho = PASTA / arquivo
    try:
        return caminho.read_text(encoding="utf-8")
    except OSError:
        return AVISO_DE_FALTA
