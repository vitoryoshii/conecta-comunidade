"""Política CORS compartilhada pela API FastAPI e pelos testes."""

from collections.abc import Sequence

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import CORS_HEADERS, CORS_METODOS


def configurar_cors(app: FastAPI, origens: Sequence[str]) -> None:
    """Aplica CORS para a PWA sem cookies ou wildcard."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(origens),
        allow_credentials=False,
        allow_methods=CORS_METODOS,
        allow_headers=CORS_HEADERS,
    )
