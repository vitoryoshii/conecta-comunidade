"""
Máscaras de digitação dos campos brasileiros.

As funções recebem o que o usuário digitou (com ou sem máscara) e devolvem o
texto já formatado. O app **exibe** com máscara e **envia** só os dígitos: o
backend guarda apenas números, e é ele quem valida de verdade — o que há aqui é
conveniência de digitação, não validação.
"""

from __future__ import annotations


def somente_digitos(texto: str) -> str:
    """Mantém apenas os algarismos do texto."""
    return "".join(c for c in (texto or "") if c.isdigit())


def cpf(texto: str) -> str:
    """Formata progressivamente como `000.000.000-00`."""
    numeros = somente_digitos(texto)[:11]

    partes = [numeros[:3], numeros[3:6], numeros[6:9]]
    formatado = ".".join(p for p in partes if p)
    if len(numeros) > 9:
        formatado += f"-{numeros[9:]}"
    return formatado


def telefone(texto: str) -> str:
    """Formata progressivamente como `(00) 00000-0000`.

    O ponto de corte muda com o tamanho: telefone fixo tem 4+4 depois do DDD e
    celular tem 5+4, então só dá para decidir quando o 11º dígito aparece.
    """
    numeros = somente_digitos(texto)[:11]
    if not numeros:
        return ""

    if len(numeros) <= 2:
        return f"({numeros}"

    ddd, resto = numeros[:2], numeros[2:]
    corte = 5 if len(numeros) > 10 else 4
    if len(resto) <= corte:
        return f"({ddd}) {resto}"
    return f"({ddd}) {resto[:corte]}-{resto[corte:]}"


def data(valor) -> str:
    """Formata uma `date` como `dd/mm/aaaa`, que é como o Brasil lê."""
    return valor.strftime("%d/%m/%Y") if valor else ""
