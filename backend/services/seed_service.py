"""
Serviço de carga inicial (seed).

Popula o banco com um cenário realista de São Paulo para que o app abra com
conteúdo já na primeira execução — essencial na apresentação acadêmica, em que
telas vazias não mostram nada do que foi construído.

Todos os usuários de exemplo usam a mesma senha: **senha123**.
"""

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, func, select

from backend.database import engine, init_db
from backend.models import (
    ONG,
    Categoria,
    Entrega,
    Mensagem,
    Oferta,
    Solicitacao,
    StatusEntrega,
    StatusOferta,
    StatusSolicitacao,
    TipoAjuda,
    TipoUsuario,
    Urgencia,
    Usuario,
)
from backend.services.auth_service import gerar_hash_senha

SENHA_PADRAO = "senha123"

# Categorias fixas da plataforma. O `icone` é o nome de um Material Icon,
# consumido diretamente pelo Flet (ft.Icons.<NOME>).
CATEGORIAS = [
    ("Água", "water_drop"),
    ("Alimentos", "restaurant"),
    ("Roupas", "checkroom"),
    ("Abrigo", "home"),
    ("Medicamentos", "medical_services"),
    ("Material Escolar", "school"),
    ("Móveis", "chair"),
    ("Outros", "category"),
]


def _horas_atras(horas: int) -> datetime:
    """Data/hora no passado, usada para variar o "tempo desde a publicação"."""
    return datetime.now(timezone.utc) - timedelta(hours=horas)


def banco_vazio(session: Session) -> bool:
    """Indica se ainda não há usuários cadastrados."""
    total = session.exec(select(func.count()).select_from(Usuario)).one()
    return int(total) == 0


def limpar(session: Session) -> None:
    """Remove todos os registros, na ordem que respeita as chaves estrangeiras."""
    for modelo in (Entrega, Mensagem, Oferta, Solicitacao, ONG, Usuario, Categoria):
        for registro in session.exec(select(modelo)).all():
            session.delete(registro)
    session.commit()


def _criar_categorias(session: Session) -> dict[str, Categoria]:
    """Cria as categorias e devolve um índice por nome."""
    categorias: dict[str, Categoria] = {}
    for nome, icone in CATEGORIAS:
        categoria = Categoria(nome=nome, icone=icone)
        session.add(categoria)
        categorias[nome] = categoria
    session.commit()
    for categoria in categorias.values():
        session.refresh(categoria)
    return categorias


def _criar_usuarios(session: Session) -> dict[str, Usuario]:
    """Cria os cinco usuários de demonstração, espalhados pela cidade."""
    senha = gerar_hash_senha(SENHA_PADRAO)
    definicoes = [
        # (chave, nome, email, tipo, cidade, lat, long, impacto)
        ("ana", "Ana Ribeiro", "ana@conecta.com", TipoUsuario.SOLICITANTE,
         "Vila Madalena - São Paulo/SP", -23.5545, -46.6896, (0, 2, 0)),
        ("carlos", "Carlos Mendes", "carlos@conecta.com", TipoUsuario.DOADOR,
         "Pinheiros - São Paulo/SP", -23.5670, -46.7020, (5, 0, 3)),
        ("juliana", "Juliana Souza", "juliana@conecta.com", TipoUsuario.VOLUNTARIO,
         "Butantã - São Paulo/SP", -23.5710, -46.7200, (8, 1, 12)),
        ("marcos", "Marcos Lima", "marcos@conecta.com", TipoUsuario.SOLICITANTE,
         "Capão Redondo - São Paulo/SP", -23.6600, -46.7700, (0, 4, 1)),
        ("beatriz", "Beatriz Alves", "beatriz@semear.org", TipoUsuario.ONG,
         "Centro - São Paulo/SP", -23.5460, -46.6360, (23, 0, 30)),
    ]

    usuarios: dict[str, Usuario] = {}
    for chave, nome, email, tipo, cidade, lat, lon, impacto in definicoes:
        atendidas, recebidas, voluntario = impacto
        usuario = Usuario(
            nome=nome,
            email=email,
            senha_hash=senha,
            tipo=tipo,
            cidade=cidade,
            latitude=lat,
            longitude=lon,
            solicitacoes_atendidas=atendidas,
            doacoes_recebidas=recebidas,
            acoes_voluntario=voluntario,
        )
        session.add(usuario)
        usuarios[chave] = usuario

    session.commit()
    for usuario in usuarios.values():
        session.refresh(usuario)
    return usuarios


def _criar_ongs(session: Session) -> list[ONG]:
    """Cria as cinco instituições parceiras exibidas na aba de ONGs."""
    definicoes = [
        (
            "Instituto Semear",
            "Distribuição de cestas básicas e apoio a famílias em situação de "
            "vulnerabilidade na região central de São Paulo.",
            4.8, 132, True, -23.5460, -46.6360, "Rua Sete de Abril, 200 - Centro",
            [
                {"nome": "Cestas básicas", "quantidade": 120, "icone": "shopping_basket"},
                {"nome": "Kits de higiene", "quantidade": 80, "icone": "soap"},
                {"nome": "Água mineral (L)", "quantidade": 400, "icone": "water_drop"},
            ],
        ),
        (
            "Casa Acolher",
            "Abrigo temporário com 60 vagas, refeições e encaminhamento para "
            "assistência social.",
            4.6, 87, True, -23.5590, -46.6620, "Av. São João, 1450 - República",
            [
                {"nome": "Vagas de abrigo", "quantidade": 18, "icone": "home"},
                {"nome": "Cobertores", "quantidade": 95, "icone": "bed"},
                {"nome": "Refeições/dia", "quantidade": 180, "icone": "restaurant"},
            ],
        ),
        (
            "Rede Solidária Zona Sul",
            "Coleta e redistribuição de roupas, móveis e material escolar em "
            "bairros da zona sul.",
            4.3, 54, False, -23.6480, -46.7310, "Rua Ibiapina, 77 - Campo Limpo",
            [
                {"nome": "Peças de roupa", "quantidade": 640, "icone": "checkroom"},
                {"nome": "Móveis", "quantidade": 22, "icone": "chair"},
                {"nome": "Kits escolares", "quantidade": 130, "icone": "school"},
            ],
        ),
        (
            "Farmácia Comunitária Vida",
            "Doação de medicamentos de uso contínuo mediante receita e "
            "atendimento farmacêutico gratuito.",
            4.9, 210, True, -23.5730, -46.6410, "Rua Vergueiro, 980 - Liberdade",
            [
                {"nome": "Medicamentos", "quantidade": 310, "icone": "medical_services"},
                {"nome": "Consultas/semana", "quantidade": 40, "icone": "health_and_safety"},
            ],
        ),
        (
            "Ação Oeste Voluntária",
            "Rede de voluntários para transporte de doações e mutirões de "
            "reforma em comunidades da zona oeste.",
            4.1, 38, False, -23.5680, -46.7350, "Rua Alvarenga, 310 - Butantã",
            [
                {"nome": "Voluntários ativos", "quantidade": 64, "icone": "volunteer_activism"},
                {"nome": "Veículos para entrega", "quantidade": 7, "icone": "local_shipping"},
            ],
        ),
    ]

    ongs: list[ONG] = []
    for nome, descricao, nota, total, verificada, lat, lon, endereco, recursos in definicoes:
        ong = ONG(
            nome=nome,
            descricao=descricao,
            avaliacao=nota,
            total_avaliacoes=total,
            verificada=verificada,
            recursos_disponiveis=recursos,
            endereco=f"{endereco} - São Paulo/SP",
            latitude=lat,
            longitude=lon,
        )
        session.add(ong)
        ongs.append(ong)

    session.commit()
    for ong in ongs:
        session.refresh(ong)
    return ongs


def _criar_solicitacoes(
    session: Session, usuarios: dict[str, Usuario], categorias: dict[str, Categoria]
) -> list[Solicitacao]:
    """Cria oito pedidos variados em urgência, status e distância."""
    definicoes = [
        (
            "ana", "Água potável para 4 famílias",
            "Estamos sem abastecimento há três dias no condomínio. Precisamos de "
            "água mineral para crianças e idosos.",
            "Água", "50 litros", Urgencia.ALTA, StatusSolicitacao.ATIVA, 16,
            -23.5561, -46.6890, "Rua Harmonia, 420 - Vila Madalena", True, 2,
        ),
        (
            "marcos", "Cestas básicas para famílias desabrigadas",
            "Sete famílias perderam tudo no alagamento da semana passada e "
            "precisam de alimentos não perecíveis.",
            "Alimentos", "7 cestas", Urgencia.ALTA, StatusSolicitacao.ATIVA, 28,
            -23.6612, -46.7688, "Rua Cabo Diogo, 15 - Capão Redondo", True, 5,
        ),
        (
            "ana", "Roupas de frio para adultos",
            "Com a chegada da frente fria, precisamos de casacos e cobertores "
            "para moradores em situação de rua da região.",
            "Roupas", "30 peças", Urgencia.MEDIA, StatusSolicitacao.ATIVA, 30,
            -23.5528, -46.6845, "Praça Benedito Calixto - Pinheiros", False, 9,
        ),
        (
            "marcos", "Medicamentos para pressão alta",
            "Minha mãe usa losartana de uso contínuo e a UBS está sem estoque "
            "há duas semanas.",
            "Medicamentos", "2 caixas", Urgencia.ALTA, StatusSolicitacao.EM_ANDAMENTO, 1,
            -23.6570, -46.7702, "Rua Ernesto Rocha, 88 - Capão Redondo", False, 20,
        ),
        (
            "ana", "Material escolar para o 5º ano",
            "Estamos montando kits para 12 crianças da escola municipal do bairro.",
            "Material Escolar", "12 kits", Urgencia.BAIXA, StatusSolicitacao.ATIVA, 12,
            -23.5502, -46.6930, "Rua Fidalga, 300 - Vila Madalena", False, 34,
        ),
        (
            "marcos", "Colchões e cobertores",
            "Abrigo improvisado na igreja do bairro precisa de colchões "
            "solteiro e cobertores.",
            "Abrigo", "10 colchões", Urgencia.MEDIA, StatusSolicitacao.ATIVA, 22,
            -23.6501, -46.7590, "Rua Pilar do Sul, 45 - Jardim São Luís", False, 48,
        ),
        (
            "ana", "Geladeira para família recém-chegada",
            "Família com dois bebês se mudou para o bairro e não tem onde "
            "guardar leite e remédios.",
            "Móveis", "1 unidade", Urgencia.MEDIA, StatusSolicitacao.ATIVA, 4,
            -23.5588, -46.6975, "Rua Teodoro Sampaio, 1500 - Pinheiros", False, 72,
        ),
        (
            "marcos", "Fraldas geriátricas tamanho G",
            "Pedido atendido pela comunidade — obrigado a todos que ajudaram!",
            "Outros", "6 pacotes", Urgencia.BAIXA, StatusSolicitacao.CONCLUIDA, 1,
            -23.6625, -46.7745, "Rua Nova Canaã, 210 - Capão Redondo", False, 168,
        ),
    ]

    solicitacoes: list[Solicitacao] = []
    for (
        autor, titulo, descricao, categoria, quantidade, urgencia, status,
        pessoas, lat, lon, endereco, emergencia, horas,
    ) in definicoes:
        solicitacao = Solicitacao(
            usuario_id=usuarios[autor].id,  # type: ignore[arg-type]
            titulo=titulo,
            descricao=descricao,
            categoria_id=categorias[categoria].id,  # type: ignore[arg-type]
            quantidade=quantidade,
            urgencia=urgencia,
            status=status,
            pessoas_beneficiadas=pessoas,
            latitude=lat,
            longitude=lon,
            endereco=f"{endereco} - São Paulo/SP",
            fotos=[],
            emergencia=emergencia,
            criada_em=_horas_atras(horas),
        )
        session.add(solicitacao)
        solicitacoes.append(solicitacao)

    session.commit()
    for solicitacao in solicitacoes:
        session.refresh(solicitacao)
    return solicitacoes


def _criar_ofertas(
    session: Session,
    usuarios: dict[str, Usuario],
    categorias: dict[str, Categoria],
    solicitacoes: list[Solicitacao],
) -> list[Oferta]:
    """Cria quatro ofertas, uma delas já vinculada a um pedido."""
    definicoes = [
        (
            "carlos", "Tenho 60 litros de água mineral",
            "Sobrou estoque de um evento da empresa. Posso separar hoje mesmo.",
            "Água", TipoAjuda.TENHO_ITEM, solicitacoes[0].id,
            -23.5670, -46.7020, "Pinheiros - São Paulo/SP", 1,
        ),
        (
            "juliana", "Posso transportar doações na zona oeste",
            "Tenho uma van e disponibilidade nas terças e quintas à tarde.",
            "Outros", TipoAjuda.POSSO_ENTREGAR, None,
            -23.5710, -46.7200, "Butantã - São Paulo/SP", 6,
        ),
        (
            "carlos", "Ponto de retirada de roupas em Pinheiros",
            "Deixei duas caixas de roupas de frio na portaria do prédio, "
            "retirada das 8h às 20h.",
            "Roupas", TipoAjuda.PONTO_RETIRADA, None,
            -23.5652, -46.7005, "Rua dos Pinheiros, 900 - Pinheiros", 14,
        ),
        (
            "beatriz", "Cestas básicas disponíveis no Instituto Semear",
            "Retirada mediante cadastro simples, de segunda a sexta.",
            "Alimentos", TipoAjuda.PONTO_RETIRADA, None,
            -23.5460, -46.6360, "Rua Sete de Abril, 200 - Centro", 26,
        ),
    ]

    ofertas: list[Oferta] = []
    for (
        autor, titulo, descricao, categoria, tipo, solicitacao_id,
        lat, lon, endereco, horas,
    ) in definicoes:
        oferta = Oferta(
            usuario_id=usuarios[autor].id,  # type: ignore[arg-type]
            titulo=titulo,
            descricao=descricao,
            categoria_id=categorias[categoria].id,  # type: ignore[arg-type]
            tipo_ajuda=tipo,
            status=StatusOferta.DISPONIVEL,
            solicitacao_id=solicitacao_id,
            latitude=lat,
            longitude=lon,
            endereco=f"{endereco} - São Paulo/SP",
            criada_em=_horas_atras(horas),
        )
        session.add(oferta)
        ofertas.append(oferta)

    session.commit()
    for oferta in ofertas:
        session.refresh(oferta)
    return ofertas


def _criar_conversa_e_entrega(
    session: Session, usuarios: dict[str, Usuario], solicitacoes: list[Solicitacao]
) -> None:
    """Cria o chat de exemplo entre Carlos e Ana e a entrega já agendada."""
    ana = usuarios["ana"]
    carlos = usuarios["carlos"]
    pedido_agua = solicitacoes[0]

    falas = [
        (carlos, ana, "Oi, Ana! Vi seu pedido de água. Tenho 60 litros aqui em Pinheiros.", 20),
        (ana, carlos, "Carlos, que notícia boa! A gente precisa muito, obrigada!", 19),
        (carlos, ana, "Consigo levar amanhã à tarde. Às 14h funciona para você?", 18),
        (ana, carlos, "Perfeito. Pode deixar na portaria da Rua Harmonia, 420.", 17),
        (carlos, ana, "Combinado, já deixei o agendamento marcado aqui no app.", 16),
    ]

    for remetente, destinatario, texto, horas in falas:
        session.add(
            Mensagem(
                remetente_id=remetente.id,  # type: ignore[arg-type]
                destinatario_id=destinatario.id,  # type: ignore[arg-type]
                solicitacao_id=pedido_agua.id,
                texto=texto,
                criada_em=_horas_atras(horas),
                lida=True,
            )
        )

    # Uma mensagem não lida para a Ana, para o badge de "não lidas" aparecer.
    session.add(
        Mensagem(
            remetente_id=carlos.id,  # type: ignore[arg-type]
            destinatario_id=ana.id,  # type: ignore[arg-type]
            solicitacao_id=pedido_agua.id,
            texto="Estou saindo agora, chego em uns 30 minutos!",
            criada_em=_horas_atras(1),
            lida=False,
        )
    )

    # Conversa curta entre Juliana e Marcos, para a aba Mensagens ter volume.
    session.add(
        Mensagem(
            remetente_id=usuarios["juliana"].id,  # type: ignore[arg-type]
            destinatario_id=usuarios["marcos"].id,  # type: ignore[arg-type]
            solicitacao_id=solicitacoes[1].id,
            texto="Marcos, consigo buscar as cestas no Instituto Semear e levar até vocês.",
            criada_em=_horas_atras(4),
            lida=False,
        )
    )

    session.add(
        Entrega(
            solicitacao_id=pedido_agua.id,  # type: ignore[arg-type]
            doador_id=carlos.id,  # type: ignore[arg-type]
            data=(datetime.now(timezone.utc) + timedelta(days=1)).strftime("%d/%m/%Y"),
            hora="14:00",
            local="Rua Harmonia, 420 - Vila Madalena - São Paulo/SP",
            status=StatusEntrega.AGENDADA,
        )
    )

    # O pedido de água já está sendo atendido.
    pedido_agua.status = StatusSolicitacao.EM_ANDAMENTO
    session.add(pedido_agua)
    session.commit()


def popular(forcar: bool = False) -> dict[str, int]:
    """Executa a carga completa.

    Args:
        forcar: quando `True`, apaga os dados existentes antes de popular.

    Returns:
        Um resumo com a contagem de registros criados por entidade.
    """
    init_db()

    with Session(engine) as session:
        if not banco_vazio(session) and not forcar:
            return {"ignorado": 1}

        if forcar:
            limpar(session)

        categorias = _criar_categorias(session)
        usuarios = _criar_usuarios(session)
        ongs = _criar_ongs(session)
        solicitacoes = _criar_solicitacoes(session, usuarios, categorias)
        ofertas = _criar_ofertas(session, usuarios, categorias, solicitacoes)
        _criar_conversa_e_entrega(session, usuarios, solicitacoes)

        return {
            "categorias": len(categorias),
            "usuarios": len(usuarios),
            "ongs": len(ongs),
            "solicitacoes": len(solicitacoes),
            "ofertas": len(ofertas),
            "mensagens": int(
                session.exec(select(func.count()).select_from(Mensagem)).one()
            ),
            "entregas": int(session.exec(select(func.count()).select_from(Entrega)).one()),
        }
