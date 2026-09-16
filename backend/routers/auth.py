"""Rotas de autenticação: cadastro, login, recuperação de senha e perfil do token."""

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from backend.deps import SessionDep, UsuarioAtual
from backend.models import Usuario
from backend.schemas import (
    RecuperarSenha,
    RecuperarSenhaResposta,
    Token,
    UsuarioCriar,
    UsuarioLer,
    UsuarioLogin,
    UsuarioPrivadoLer,
)
from backend.services import dados_pessoais_service, localidades_service
from backend.services.auth_service import criar_access_token, gerar_hash_senha, verificar_senha

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# Resposta única do pedido de redefinição: por segurança, ela não muda
# conforme o e-mail exista ou não na base.
MENSAGEM_RECUPERACAO = "Se o e-mail existir, enviamos um link para redefinir a senha."


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Criar conta",
    description=(
        "Cadastra um novo usuário, grava a senha como hash bcrypt e já devolve "
        "um token JWT — assim o app entra direto na Home após o cadastro."
    ),
)
def registrar(dados: UsuarioCriar, session: SessionDep) -> Token:
    """Cria o usuário e retorna o token de acesso."""
    email_normalizado = dados.email.strip().lower()

    ja_existe = session.exec(select(Usuario).where(Usuario.email == email_normalizado)).first()
    if ja_existe:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma conta cadastrada com este e-mail.",
        )

    # Dados pessoais: dígito verificador do CPF, DDD do telefone e idade mínima.
    # Tudo volta normalizado (só dígitos), que é o formato gravado.
    try:
        cpf = dados_pessoais_service.validar_cpf(dados.cpf)
        telefone = dados_pessoais_service.validar_telefone(dados.telefone)
        nascimento = dados_pessoais_service.validar_data_de_nascimento(dados.data_nascimento)
    except ValueError as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(erro)
        ) from erro

    # A unicidade também é garantida por índice no banco; a checagem aqui existe
    # para devolver uma mensagem que faça sentido em vez de um erro de constraint.
    cpf_em_uso = session.exec(select(Usuario).where(Usuario.cpf == cpf)).first()
    if cpf_em_uso:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma conta cadastrada com este CPF.",
        )

    # A dupla estado/cidade é conferida contra a base do IBGE, que devolve a
    # sigla em maiúsculas, o nome oficial do município e as coordenadas da sede.
    try:
        local = localidades_service.validar_estado_e_cidade(dados.estado, dados.cidade)
    except ValueError as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(erro)
        ) from erro

    # As coordenadas vêm da cidade escolhida. O cliente ainda pode mandar um
    # ponto próprio (um GPS de verdade, no futuro); só não pode ficar em (0, 0)
    # por omissão, que era o que acontecia antes.
    latitude = dados.latitude or local.latitude
    longitude = dados.longitude or local.longitude

    usuario = Usuario(
        nome=dados.nome.strip(),
        email=email_normalizado,
        senha_hash=gerar_hash_senha(dados.senha),
        tipo=dados.tipo,
        cpf=cpf,
        telefone=telefone,
        data_nascimento=nascimento,
        estado=local.estado,
        cidade=local.cidade,
        latitude=latitude,
        longitude=longitude,
        avatar_url=dados.avatar_url,
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)

    return Token(
        access_token=criar_access_token(usuario.id),  # type: ignore[arg-type]
        usuario=UsuarioLer.model_validate(usuario),
    )


@router.post(
    "/login",
    response_model=Token,
    summary="Entrar",
    description="Valida e-mail e senha e devolve um JWT válido por 7 dias.",
)
def login(dados: UsuarioLogin, session: SessionDep) -> Token:
    """Autentica o usuário e retorna o token de acesso."""
    email_normalizado = dados.email.strip().lower()
    usuario = session.exec(select(Usuario).where(Usuario.email == email_normalizado)).first()

    # A mesma mensagem para e-mail inexistente e senha errada evita revelar
    # quais e-mails estão cadastrados na plataforma.
    if usuario is None or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
        )

    return Token(
        access_token=criar_access_token(usuario.id),  # type: ignore[arg-type]
        usuario=UsuarioLer.model_validate(usuario),
    )


@router.post(
    "/recuperar-senha",
    response_model=RecuperarSenhaResposta,
    summary="Recuperar senha",
    description=(
        "Inicia a redefinição de senha. Responde **sempre** 200 com a mesma "
        "mensagem, exista ou não uma conta com o e-mail informado — assim a "
        "rota não pode ser usada para descobrir quem está cadastrado."
    ),
)
def recuperar_senha(dados: RecuperarSenha, session: SessionDep) -> RecuperarSenhaResposta:
    """Registra o pedido de redefinição e devolve a confirmação genérica."""
    email_normalizado = dados.email.strip().lower()
    usuario = session.exec(select(Usuario).where(Usuario.email == email_normalizado)).first()

    if usuario is not None:
        # TODO: gerar um token de redefinição com validade curta, gravá-lo e
        # disparar o e-mail com o link. Enquanto não há serviço de e-mail
        # configurado, o fluxo termina aqui — a resposta já é a definitiva.
        pass

    return RecuperarSenhaResposta(mensagem=MENSAGEM_RECUPERACAO)


@router.get(
    "/me",
    response_model=UsuarioPrivadoLer,
    summary="Usuário autenticado",
    description=(
        "Devolve os dados do usuário dono do token enviado no header, incluindo "
        "os dados pessoais que o perfil público não expõe. O CPF vem **mascarado** "
        "(`***.456.789-**`) — o número completo não sai da API em nenhuma rota."
    ),
)
def eu(usuario: UsuarioAtual) -> UsuarioPrivadoLer:
    """Retorna o perfil do usuário logado, com o CPF mascarado."""
    privado = UsuarioPrivadoLer.model_validate(usuario)
    privado.cpf = dados_pessoais_service.mascarar_cpf(usuario.cpf)
    return privado
