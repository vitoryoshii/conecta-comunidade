"""
Guarda das fotos de perfil.

O arquivo escolhido pelo usuário é **copiado** para `mobile/assets/avatars/`, e o
que vai para a API (`usuario.avatar_url`) é o caminho relativo dentro da pasta de
assets — `avatars/usuario_3_1758067200.jpg`.

Copiar, e não apenas guardar o caminho de origem, é o que faz a foto continuar
existindo depois que a pessoa mover ou apagar o original. E o caminho relativo é
o que faz o `ft.Image` achar o arquivo tanto na janela nativa quanto no modo web,
já que os dois servem esta mesma pasta.

TODO: numa versão com servidor, o arquivo deve subir para um storage e a API
guardar a URL pública. A pasta local resolve a demonstração, mas não sobrevive a
trocar de máquina.
"""

from __future__ import annotations

import shutil
import time
from os import getenv
from pathlib import Path


def _pasta_de_avatares() -> Path:
    """Devolve armazenamento gravável, fora do bundle somente-leitura."""
    diretorio_dados = getenv("FLET_APP_STORAGE_DATA")
    if diretorio_dados:
        return Path(diretorio_dados) / "avatars"
    # Mantém o comportamento local em desenvolvimento fora do runtime Flet.
    return Path(__file__).resolve().parent / "assets" / "avatars"


PASTA = _pasta_de_avatares()

# Extensões aceitas. Qualquer outra coisa (um .pdf renomeado, por exemplo) é
# recusada antes de virar um arquivo dentro dos assets.
EXTENSOES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}

# Teto de tamanho: a foto é só um avatar, e um arquivo de dezenas de MB deixaria
# a abertura da tela lenta sem nenhum ganho visível.
TAMANHO_MAXIMO = 8 * 1024 * 1024


def salvar(usuario_id: int, origem: str | Path) -> str:
    """Copia a imagem para os assets e devolve o caminho relativo a gravar.

    Levanta `ValueError` com uma mensagem pronta para a tela quando o arquivo
    não serve.
    """
    caminho = Path(origem)
    extensao = caminho.suffix.lower()

    if extensao not in EXTENSOES:
        raise ValueError("Escolha uma imagem (JPG, PNG, WEBP ou GIF).")
    if not caminho.is_file():
        raise ValueError("Não foi possível ler o arquivo escolhido.")
    if caminho.stat().st_size > TAMANHO_MAXIMO:
        raise ValueError("A imagem precisa ter no máximo 8 MB.")

    PASTA.mkdir(parents=True, exist_ok=True)
    # O carimbo de tempo no nome evita que a tela continue mostrando a foto
    # antiga por causa do cache de imagem quando a pessoa troca de avatar.
    destino = PASTA / f"usuario_{usuario_id}_{int(time.time())}{extensao}"
    shutil.copyfile(caminho, destino)

    return f"avatars/{destino.name}"
