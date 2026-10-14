"""Regressões para separar dependências do backend e do APK Flet."""

from pathlib import Path
import tomllib

from scripts.prepare_mobile_distribution import PYPROJECT_MOBILE


ROOT = Path(__file__).resolve().parents[1]


def _nomes(distribuicoes: list[str]) -> set[str]:
    return {item.split("[", 1)[0].split("=", 1)[0].lower() for item in distribuicoes}


def test_manifesto_raiz_declara_dependencias_do_backend() -> None:
    projeto = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencias = _nomes(projeto["project"]["dependencies"])

    assert {
        "fastapi",
        "sqlmodel",
        "pydantic-settings",
        "email-validator",
        "python-dotenv",
        "python-jose",
        "passlib",
        "bcrypt",
        "geopy",
        "psycopg2-binary",
    } <= dependencias


def test_manifesto_gerado_para_apk_nao_inclui_backend() -> None:
    projeto_mobile = tomllib.loads(PYPROJECT_MOBILE)
    dependencias = _nomes(projeto_mobile["project"]["dependencies"])

    assert dependencias == {"flet", "httpx"}
    assert projeto_mobile["tool"]["flet"]["app"]["module"] == "main"
