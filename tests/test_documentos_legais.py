"""Regressões dos documentos legais nos layouts de desenvolvimento e staging."""

from pathlib import Path
import zipfile

from mobile import legal_textos
from scripts.prepare_mobile_distribution import preparar_staging


RAIZ = Path(__file__).resolve().parent.parent


def _ler(chave: str) -> str:
    legal_textos.texto.cache_clear()
    return legal_textos.texto(chave)


def test_documentos_legais_sao_lidos_no_layout_de_desenvolvimento() -> None:
    assert "Termos de Uso" in _ler("termos")
    assert "Política de Privacidade" in _ler("privacidade")
    assert legal_textos.AVISO_DE_FALTA not in _ler("termos")


def test_staging_android_publica_os_dois_markdowns_na_raiz_de_assets(tmp_path: Path) -> None:
    staging = preparar_staging(tmp_path / "distribution-app")
    for chave, nome in legal_textos.DOCUMENTOS.values():
        publicado = staging / "assets" / "legal" / nome
        original = RAIZ / "mobile" / "assets" / "legal" / nome
        assert publicado.read_text(encoding="utf-8") == original.read_text(encoding="utf-8")


def test_resolvedor_aceita_o_layout_empacotado_do_staging(
    tmp_path: Path, monkeypatch
) -> None:
    staging = preparar_staging(tmp_path / "distribution-app")
    monkeypatch.setattr(legal_textos, "pastas_de_documentos", lambda: (staging / "assets" / "legal",))
    assert "Termos de Uso" in _ler("termos")
    assert legal_textos.AVISO_DE_FALTA not in _ler("privacidade")


def test_inclusao_no_app_zip_web_mantem_os_markdowns_oficiais(tmp_path: Path) -> None:
    from scripts.embed_web_legal_assets import incorporar

    pacote = tmp_path / "app.zip"
    with zipfile.ZipFile(pacote, "w") as arquivo:
        arquivo.writestr("mobile/legal_textos.pyc", b"python-bytecode")

    incorporar(pacote, RAIZ / "mobile" / "assets" / "legal")

    with zipfile.ZipFile(pacote) as arquivo:
        for _, nome in legal_textos.DOCUMENTOS.values():
            assert arquivo.read(f"assets/legal/{nome}") == (
                RAIZ / "mobile" / "assets" / "legal" / nome
            ).read_bytes()
