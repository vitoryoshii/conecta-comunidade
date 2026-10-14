"""Regressões de configuração segura do runtime."""

import pytest
from pydantic import ValidationError

from backend.config import Settings


def test_producao_recusa_secret_key_padrao(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERCEL_ENV", "production")

    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(_env_file=None)


def test_producao_aceita_secret_key_forte(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERCEL_ENV", "production")

    configuracao = Settings(
        _env_file=None,
        secret_key="s" * 32,
        database_url="postgresql+psycopg2://usuario:senha@localhost:5432/conecta",
    )

    assert configuracao.secret_key == "s" * 32
