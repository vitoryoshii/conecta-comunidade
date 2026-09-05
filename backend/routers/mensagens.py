"""
Rotas de mensagens.

Duas leituras diferentes convivem aqui:

* `GET /mensagens/conversas` — a lista de conversas da aba *Mensagens*;
* `GET /mensagens?com=<id>` — o histórico completo do chat com uma pessoa.
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import col, or_, select

from backend.deps import SessionDep, UsuarioAtual
from backend.models import Mensagem, Solicitacao, Usuario
from backend.schemas import ConversaLer, MensagemCriar, MensagemLer
from backend.services.apresentacao import carregar_mapa_usuarios

router = APIRouter(prefix="/mensagens", tags=["Mensagens"])


@router.get(
    "/conversas",
    response_model=list[ConversaLer],
    summary="Minhas conversas",
    description=(
        "Agrupa as mensagens por interlocutor e devolve a última fala de cada "
        "conversa, com a contagem de mensagens não lidas. **Requer JWT.**"
    ),
)
def listar_conversas(usuario: UsuarioAtual, session: SessionDep) -> list[ConversaLer]:
    """Monta a lista de conversas do usuário logado."""
    mensagens = list(
        session.exec(
            select(Mensagem)
            .where(
                or_(
                    Mensagem.remetente_id == usuario.id,
                    Mensagem.destinatario_id == usuario.id,
                )
            )
            .order_by(col(Mensagem.criada_em).asc())
        ).all()
    )

    # Percorremos em ordem cronológica e sobrescrevemos: ao final, cada chave
    # guarda a última mensagem daquela conversa.
    resumo: dict[int, ConversaLer] = {}
    nao_lidas: dict[int, int] = {}

    for mensagem in mensagens:
        outro_id = (
            mensagem.destinatario_id
            if mensagem.remetente_id == usuario.id
            else mensagem.remetente_id
        )
        if mensagem.destinatario_id == usuario.id and not mensagem.lida:
            nao_lidas[outro_id] = nao_lidas.get(outro_id, 0) + 1

        resumo[outro_id] = ConversaLer(
            interlocutor_id=outro_id,
            interlocutor_nome="",
            solicitacao_id=mensagem.solicitacao_id,
            ultima_mensagem=mensagem.texto,
            ultima_em=mensagem.criada_em,
        )

    if not resumo:
        return []

    # Preenche nomes e títulos em lote (evita uma query por conversa).
    interlocutores = carregar_mapa_usuarios(session, set(resumo.keys()))
    ids_solicitacoes = {c.solicitacao_id for c in resumo.values() if c.solicitacao_id}
    titulos: dict[int, str] = {}
    if ids_solicitacoes:
        for solicitacao in session.exec(
            select(Solicitacao).where(col(Solicitacao.id).in_(ids_solicitacoes))
        ).all():
            titulos[solicitacao.id] = solicitacao.titulo  # type: ignore[index]

    conversas: list[ConversaLer] = []
    for outro_id, conversa in resumo.items():
        pessoa = interlocutores.get(outro_id)
        conversa.interlocutor_nome = pessoa.nome if pessoa else "Usuário"
        conversa.interlocutor_avatar = pessoa.avatar_url if pessoa else None
        conversa.solicitacao_titulo = titulos.get(conversa.solicitacao_id or -1)
        conversa.nao_lidas = nao_lidas.get(outro_id, 0)
        conversas.append(conversa)

    conversas.sort(key=lambda c: c.ultima_em, reverse=True)
    return conversas


@router.get(
    "",
    response_model=list[MensagemLer],
    summary="Histórico do chat",
    description=(
        "Devolve as mensagens trocadas entre o usuário logado e o interlocutor "
        "indicado em `com`, em ordem cronológica. As mensagens recebidas são "
        "marcadas como lidas nesta chamada. **Requer JWT.**"
    ),
)
def listar_mensagens(
    usuario: UsuarioAtual,
    session: SessionDep,
    com: Annotated[int, Query(description="Id do outro participante da conversa")],
    solicitacao_id: Annotated[
        int | None, Query(description="Restringe ao contexto de uma solicitação")
    ] = None,
) -> list[MensagemLer]:
    """Lista o histórico e marca como lidas as mensagens recebidas."""
    if session.get(Usuario, com) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    consulta = select(Mensagem).where(
        or_(
            (col(Mensagem.remetente_id) == usuario.id) & (col(Mensagem.destinatario_id) == com),
            (col(Mensagem.remetente_id) == com) & (col(Mensagem.destinatario_id) == usuario.id),
        )
    )
    if solicitacao_id is not None:
        consulta = consulta.where(Mensagem.solicitacao_id == solicitacao_id)

    registros = list(session.exec(consulta.order_by(col(Mensagem.criada_em).asc())).all())

    # Efeito colateral desejado: abrir o chat marca o que chegou como lido.
    houve_leitura = False
    for mensagem in registros:
        if mensagem.destinatario_id == usuario.id and not mensagem.lida:
            mensagem.lida = True
            session.add(mensagem)
            houve_leitura = True
    if houve_leitura:
        session.commit()

    nomes = carregar_mapa_usuarios(session, {usuario.id, com})  # type: ignore[arg-type]

    # `model_validate` lê os atributos do objeto (e não o `__dict__`), o que é
    # necessário aqui: o commit acima expira as instâncias da sessão.
    itens: list[MensagemLer] = []
    for mensagem in registros:
        item = MensagemLer.model_validate(mensagem)
        remetente = nomes.get(mensagem.remetente_id)
        item.remetente_nome = remetente.nome if remetente else ""
        itens.append(item)
    return itens


@router.post(
    "",
    response_model=MensagemLer,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar mensagem",
    description="Envia uma mensagem para outro usuário da plataforma. **Requer JWT.**",
)
def enviar_mensagem(
    dados: MensagemCriar, usuario: UsuarioAtual, session: SessionDep
) -> MensagemLer:
    """Grava a mensagem e devolve a bolha pronta para o chat."""
    if dados.destinatario_id == usuario.id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Não é possível enviar mensagem para si mesmo.",
        )
    if session.get(Usuario, dados.destinatario_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Destinatário não encontrado."
        )

    mensagem = Mensagem(
        remetente_id=usuario.id,  # type: ignore[arg-type]
        destinatario_id=dados.destinatario_id,
        solicitacao_id=dados.solicitacao_id,
        texto=dados.texto.strip(),
    )
    session.add(mensagem)
    session.commit()
    session.refresh(mensagem)

    item = MensagemLer.model_validate(mensagem)
    item.remetente_nome = usuario.nome
    return item
