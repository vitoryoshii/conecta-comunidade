"""Enumerações compartilhadas pelos modelos de domínio."""

from enum import Enum


class TipoUsuario(str, Enum):
    """Papel que a pessoa exerce dentro da plataforma."""

    SOLICITANTE = "solicitante"   # quem pede ajuda
    DOADOR = "doador"             # quem doa itens ou recursos
    VOLUNTARIO = "voluntario"     # quem oferece tempo/transporte
    ONG = "ong"                   # representante de uma instituição


class Urgencia(str, Enum):
    """Nível de urgência de uma solicitação (define a cor do badge no app)."""

    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"


class StatusSolicitacao(str, Enum):
    """Ciclo de vida de uma solicitação de ajuda."""

    ATIVA = "ativa"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"


class TipoAjuda(str, Enum):
    """Forma como a pessoa pretende ajudar ao criar uma oferta."""

    TENHO_ITEM = "tenho_item"
    POSSO_ENTREGAR = "posso_entregar"
    PONTO_RETIRADA = "ponto_retirada"


class StatusOferta(str, Enum):
    """Ciclo de vida de uma oferta de ajuda."""

    DISPONIVEL = "disponivel"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"


class StatusEntrega(str, Enum):
    """Situação de uma entrega agendada no chat."""

    AGENDADA = "agendada"
    REALIZADA = "realizada"
    CANCELADA = "cancelada"


class TipoPontoMapa(str, Enum):
    """Categoria de pin exibido na tela de Mapa."""

    AJUDA = "ajuda"                    # solicitações (quem precisa)
    OFERECENDO = "oferecendo"          # ofertas (quem tem item para doar)
    ONG = "ong"                        # instituições
    PONTO_RETIRADA = "ponto_retirada"  # locais de coleta/retirada
