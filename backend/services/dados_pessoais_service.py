"""
Validação e normalização dos dados pessoais do cadastro.

Concentra as regras de CPF, telefone e data de nascimento em um lugar só, para
que o router apenas traduza `ValueError` em 422. Tudo o que sai daqui já vem
normalizado — **somente dígitos** para CPF e telefone —, de modo que o banco
nunca guarda a máscara digitada pelo usuário.
"""

from __future__ import annotations

from datetime import date

# Idade mínima para usar a plataforma. Fica explícito aqui porque é uma regra de
# produto, não um detalhe de validação: mudá-la é uma decisão, não um ajuste.
IDADE_MINIMA = 18

# DDDs em uso no país. A lista evita aceitar telefones com DDD inexistente
# (como 00 ou 10), que passariam por uma checagem só de tamanho.
DDDS_VALIDOS = {
    11, 12, 13, 14, 15, 16, 17, 18, 19,
    21, 22, 24, 27, 28,
    31, 32, 33, 34, 35, 37, 38,
    41, 42, 43, 44, 45, 46, 47, 48, 49,
    51, 53, 54, 55,
    61, 62, 63, 64, 65, 66, 67, 68, 69,
    71, 73, 74, 75, 77, 79,
    81, 82, 83, 84, 85, 86, 87, 88, 89,
    91, 92, 93, 94, 95, 96, 97, 98, 99,
}


def somente_digitos(texto: str) -> str:
    """Remove máscara e espaços, deixando apenas os algarismos."""
    return "".join(c for c in (texto or "") if c.isdigit())


def _digito_verificador(digitos: str, peso_inicial: int) -> int:
    """Calcula um dígito verificador de CPF pela regra oficial (módulo 11)."""
    soma = sum(int(d) * peso for d, peso in zip(digitos, range(peso_inicial, 1, -1)))
    resto = (soma * 10) % 11
    # Resto 10 conta como zero — é o caso que uma implementação ingênua erra.
    return 0 if resto == 10 else resto


def cpf_valido(cpf: str) -> bool:
    """Confere os dois dígitos verificadores do CPF.

    Rejeita também as sequências de algarismo repetido (111.111.111-11 e
    companhia): elas passam no cálculo do módulo 11, mas não são CPFs reais.
    """
    numeros = somente_digitos(cpf)
    if len(numeros) != 11 or numeros == numeros[0] * 11:
        return False

    primeiro = _digito_verificador(numeros[:9], 10)
    segundo = _digito_verificador(numeros[:10], 11)
    return numeros[9:] == f"{primeiro}{segundo}"


def validar_cpf(cpf: str) -> str:
    """Devolve o CPF só com dígitos, ou levanta `ValueError`."""
    numeros = somente_digitos(cpf)
    if not numeros:
        raise ValueError("Informe o CPF.")
    if not cpf_valido(numeros):
        raise ValueError("CPF inválido. Confira os números digitados.")
    return numeros


def validar_telefone(telefone: str) -> str:
    """Devolve o telefone só com dígitos (DDD + número), ou levanta `ValueError`."""
    numeros = somente_digitos(telefone)
    if not numeros:
        raise ValueError("Informe o telefone.")
    if len(numeros) not in (10, 11):
        raise ValueError("Telefone deve ter DDD + 8 ou 9 dígitos.")
    if int(numeros[:2]) not in DDDS_VALIDOS:
        raise ValueError(f"DDD {numeros[:2]} não existe.")
    # Celular com 9 dígitos sempre começa por 9 depois do DDD.
    if len(numeros) == 11 and numeros[2] != "9":
        raise ValueError("Celular com 9 dígitos deve começar com 9 após o DDD.")
    return numeros


def idade_em(nascimento: date, referencia: date | None = None) -> int:
    """Idade completa em anos na data de referência (hoje, por padrão)."""
    hoje = referencia or date.today()
    # O `<` compara (mês, dia): o aniversário ainda não chegou neste ano.
    return hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))


def validar_data_de_nascimento(nascimento: date, referencia: date | None = None) -> date:
    """Confere que a data não é futura e que a pessoa tem a idade mínima."""
    hoje = referencia or date.today()
    if nascimento > hoje:
        raise ValueError("Data de nascimento não pode estar no futuro.")

    idade = idade_em(nascimento, hoje)
    if idade < IDADE_MINIMA:
        raise ValueError(f"É preciso ter ao menos {IDADE_MINIMA} anos para usar a plataforma.")
    # Barreira de sanidade: uma data como 1800 é erro de digitação, não idade.
    if idade > 120:
        raise ValueError("Data de nascimento inválida.")
    return nascimento


def mascarar_cpf(cpf: str | None) -> str | None:
    """Esconde os dígitos identificadores, deixando só o miolo: `***.456.789-**`.

    É o formato devolvido ao próprio dono do cadastro: suficiente para ele
    reconhecer o número, insuficiente para reconstruí-lo se a resposta vazar.
    """
    numeros = somente_digitos(cpf or "")
    if len(numeros) != 11:
        return None
    return f"***.{numeros[3:6]}.{numeros[6:9]}-**"
