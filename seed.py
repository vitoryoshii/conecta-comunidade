"""
Popula o banco do Conecta Comunidade com dados de demonstração.

Uso:

    python seed.py            # popula apenas se o banco estiver vazio
    python seed.py --forcar   # apaga tudo e popula novamente

Todos os usuários criados usam a senha **senha123**.
"""

import argparse
import sys

from backend.services.seed_service import SENHA_PADRAO, popular

# O console do Windows usa cp1252 por padrão e quebraria nos acentos do resumo.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    """Interpreta os argumentos da linha de comando e roda a carga."""
    parser = argparse.ArgumentParser(description="Carga de dados de exemplo.")
    parser.add_argument(
        "--forcar",
        action="store_true",
        help="apaga os registros existentes antes de popular o banco",
    )
    argumentos = parser.parse_args()

    resumo = popular(forcar=argumentos.forcar)

    if resumo.get("ignorado"):
        print("O banco já possui dados. Rode 'python seed.py --forcar' para recriar.")
        return 0

    print("Banco populado com sucesso:")
    for entidade, quantidade in resumo.items():
        print(f"  - {entidade:14s} {quantidade}")
    print()
    print("Contas de demonstração (senha: " + SENHA_PADRAO + "):")
    # A cidade de todos é São Paulo/SP; o que muda é o bairro em que as
    # coordenadas os colocam, e é ele que aparece na última coluna.
    print("  e-mail               perfil       bairro (todos em São Paulo/SP)")
    print("  ana@conecta.com      solicitante  Vila Madalena")
    print("  carlos@conecta.com   doador       Pinheiros")
    print("  juliana@conecta.com  voluntário   Butantã")
    print("  marcos@conecta.com   solicitante  Capão Redondo")
    print("  beatriz@semear.org   ONG          Centro")
    return 0


if __name__ == "__main__":
    sys.exit(main())
