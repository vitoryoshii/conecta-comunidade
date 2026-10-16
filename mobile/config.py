"""Configuração não sensível do aplicativo mobile."""

from dataclasses import dataclass
from os import getenv

AMBIENTE_DESENVOLVIMENTO = "development"
AMBIENTE_PRODUCAO = "production"


@dataclass(frozen=True)
class ConfiguracaoMobile:
    ambiente: str
    api_base_url: str


_URLS_DA_API = {
    AMBIENTE_DESENVOLVIMENTO: "http://127.0.0.1:8000",
    AMBIENTE_PRODUCAO: "https://conecta-comunidade-wheat.vercel.app",
}


def _url_publica_da_api(ambiente: str) -> str:
    """Resolve a URL pública incorporada no build mobile/web.

    O valor identifica a API e nunca contém credenciais. Isso permite que a
    PWA declare a origem no momento do build sem mudar seu contrato.
    """
    url = getenv("CONECTA_API_BASE_URL", _URLS_DA_API[ambiente]).rstrip("/")
    if ambiente == AMBIENTE_PRODUCAO and not url.startswith("https://"):
        raise ValueError("A API de produção deve usar HTTPS.")
    return url


def obter_configuracao(ambiente: str | None = None) -> ConfiguracaoMobile:
    """Devolve uma configuração pública; o APK usa produção por padrão."""
    resolvido = (ambiente or getenv("CONECTA_MOBILE_ENV", AMBIENTE_PRODUCAO)).lower()
    if resolvido not in _URLS_DA_API:
        raise ValueError(f"Ambiente mobile inválido: {resolvido!r}.")
    return ConfiguracaoMobile(resolvido, _url_publica_da_api(resolvido))
