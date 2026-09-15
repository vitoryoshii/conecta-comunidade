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
)
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

    usuario = Usuario(
        nome=dados.nome.strip(),
        email=email_normalizado,
        senha_hash=gerar_hash_senha(dados.senha),
        tipo=dados.tipo,
        cidade=dados.cidade,
        latitude=dados.latitude,
        longitude=dados.longitude,
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
    response_model=UsuarioLer,
    summary="Usuário autenticado",
    description="Devolve os dados do usuário dono do token enviado no header.",
)
def eu(usuario: UsuarioAtual) -> Usuario:
    """Retorna o perfil do usuário logado."""
    return usuario
