"""Prepara ícones Web/PWA a partir da identidade visual versionada.

O Flet gera os arquivos PWA básicos, porém também gera um favicon padrão.
Este módulo substitui apenas esses recursos pelo símbolo oficial já aprovado,
sem rasterizar SVGs em tempo de build e sem dependências de terceiros.
"""

from __future__ import annotations

import shutil
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOGO_DIR = ROOT / "mobile" / "assets" / "brand" / "logo"

# Os PNGs foram entregues junto à marca em seus tamanhos finais. Em especial,
# ``app-icon-512`` tem margem transparente para launcher/favicons, enquanto
# ``icon-*`` preenche a área segura exigida por ícones maskable.
WEB_ICON_FILES = (
    ("icon-16.png", "favicon-16x16.png"),
    ("icon-32.png", "favicon-32x32.png"),
    ("icon-32.png", "favicon.png"),  # substitui o favicon padrão do Flet
    ("icon-180.png", "apple-touch-icon.png"),
    ("favicon.svg", "favicon.svg"),
    ("app-icon-512.png", "icons/Icon-512.png"),
    ("icon-192.png", "icons/Icon-192.png"),
    ("icon-512.png", "icons/Icon-maskable-512.png"),
    ("icon-192.png", "icons/Icon-maskable-192.png"),
)


def _copy(source_name: str, target: Path) -> None:
    source = LOGO_DIR / source_name
    if not source.is_file():
        raise FileNotFoundError(f"Asset oficial ausente: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def _write_ico(destination: Path, source_names: tuple[str, ...] = ("icon-16.png", "icon-32.png", "icon-48.png")) -> None:
    """Cria um ICO com payloads PNG oficiais (formato aceito por navegadores)."""
    payloads: list[tuple[int, bytes]] = []
    for source_name in source_names:
        payload = (LOGO_DIR / source_name).read_bytes()
        if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError(f"Ícone oficial não é PNG válido: {source_name}")
        # Largura/altura ficam nos bytes 16..23 do cabeçalho IHDR.
        width, height = struct.unpack(">II", payload[16:24])
        if width != height or width not in (16, 32, 48, 64, 128, 256):
            raise ValueError(f"Dimensão ICO inválida em {source_name}: {width}x{height}")
        payloads.append((width, payload))

    header = struct.pack("<HHH", 0, 1, len(payloads))
    offset = 6 + 16 * len(payloads)
    entries: list[bytes] = []
    for size, payload in payloads:
        entries.append(
            struct.pack(
                "<BBBBHHII",
                0 if size == 256 else size,
                0 if size == 256 else size,
                0,
                0,
                1,
                32,
                len(payload),
                offset,
            )
        )
        offset += len(payload)

    destination.write_bytes(header + b"".join(entries) + b"".join(payload for _, payload in payloads))


def prepare_web_icon_assets(output_dir: Path) -> None:
    """Substitui somente os ícones do build estático já concluído."""
    output_dir = output_dir.resolve()
    if not (output_dir / "index.html").is_file():
        raise FileNotFoundError(f"Build Web ausente ou incompleto: {output_dir / 'index.html'}")

    for source_name, relative_target in WEB_ICON_FILES:
        _copy(source_name, output_dir / relative_target)
    _write_ico(output_dir / "favicon.ico")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    prepare_web_icon_assets(parser.parse_args().output_dir)
