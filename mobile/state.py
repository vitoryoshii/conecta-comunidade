"""
Estado da sessão do aplicativo.

Guarda o token JWT, o usuário logado e a pilha de navegação. É a única fonte de
verdade consultada pelas views — nenhuma tela guarda estado global por conta
própria.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Rota:
    """Uma entrada da pilha de navegação."""

    nome: str
    parametros: dict[str, Any] = field(default_factory=dict)


@dataclass
class AppState:
    """Estado global compartilhado entre todas as telas."""

    # --- Sessão ------------------------------------------------------------
    token: str | None = None
    usuario: dict[str, Any] | None = None
    visitante: bool = False  # entrou pelo botão "Continuar como visitante"

    # --- Navegação ---------------------------------------------------------
    # A pilha permite que o botão "voltar" funcione em qualquer profundidade.
    pilha: list[Rota] = field(default_factory=list)

    # --- Cache leve --------------------------------------------------------
    # As categorias mudam pouco e são usadas em várias telas; buscamos uma vez.
    categorias: list[dict[str, Any]] = field(default_factory=list)

    # --- Rascunho do cadastro ----------------------------------------------
    # As telas são reconstruídas a cada navegação (`App.renderizar`), então
    # abrir os Termos de Uso no meio do cadastro apagaria o formulário. O
    # rascunho guarda o que já foi digitado para a volta. Vive só na memória
    # desta sessão e é apagado quando a conta é criada ou o fluxo é abandonado.
    rascunho_cadastro: dict[str, Any] = field(default_factory=dict)

    # --- Propriedades de conveniência --------------------------------------
    @property
    def autenticado(self) -> bool:
        """Indica se existe uma sessão com token válido."""
        return self.token is not None and self.usuario is not None

    @property
    def usuario_id(self) -> int | None:
        """Id do usuário logado, ou `None` no modo visitante."""
        return self.usuario.get("id") if self.usuario else None

    @property
    def nome(self) -> str:
        """Primeiro nome, usado na saudação da Home."""
        if not self.usuario:
            return "visitante"
        return str(self.usuario.get("nome", "")).split(" ")[0] or "visitante"

    @property
    def latitude(self) -> float | None:
        """Latitude do usuário, base do cálculo de distância."""
        return self.usuario.get("latitude") if self.usuario else None

    @property
    def longitude(self) -> float | None:
        """Longitude do usuário, base do cálculo de distância."""
        return self.usuario.get("longitude") if self.usuario else None

    # --- Ciclo de sessão ---------------------------------------------------
    def entrar(self, token: str, usuario: dict[str, Any]) -> None:
        """Registra a sessão após um login ou cadastro bem-sucedido."""
        self.token = token
        self.usuario = usuario
        self.visitante = False

    def entrar_como_visitante(self) -> None:
        """Ativa o modo somente-leitura, sem token."""
        self.token = None
        self.usuario = None
        self.visitante = True

    def sair(self) -> None:
        """Limpa a sessão e a pilha de navegação."""
        self.token = None
        self.usuario = None
        self.visitante = False
        self.pilha.clear()
        # O rascunho carrega senha: não pode sobreviver ao fim da sessão.
        self.rascunho_cadastro = {}

    def atualizar_usuario(self, usuario: dict[str, Any]) -> None:
        """Substitui os dados do usuário logado (após editar o perfil)."""
        self.usuario = usuario

    # --- Rascunho do cadastro ----------------------------------------------
    def guardar_rascunho(self, campos: dict[str, Any]) -> None:
        """Guarda o formulário de cadastro antes de sair da tela."""
        self.rascunho_cadastro = campos

    def limpar_rascunho(self) -> None:
        """Descarta o rascunho — inclusive a senha que ele carrega."""
        self.rascunho_cadastro = {}

    # --- Pilha de navegação ------------------------------------------------
    @property
    def rota_atual(self) -> Rota:
        """Rota no topo da pilha (a tela visível)."""
        return self.pilha[-1] if self.pilha else Rota("splash")

    def empilhar(self, nome: str, /, **parametros: Any) -> None:
        """Abre uma tela por cima da atual (permite voltar).

        `nome` é posicional-only (`/`) porque os parâmetros de rota são chaves
        livres: sem isso, uma tela com um parâmetro chamado `nome` colidiria
        com o próprio argumento do método.
        """
        self.pilha.append(Rota(nome, parametros))

    def substituir(self, nome: str, /, **parametros: Any) -> None:
        """Troca a tela atual sem crescer a pilha."""
        if self.pilha:
            self.pilha.pop()
        self.pilha.append(Rota(nome, parametros))

    def reiniciar(self, nome: str, /, **parametros: Any) -> None:
        """Zera a pilha e começa de novo (usado ao entrar e ao sair)."""
        self.pilha.clear()
        self.pilha.append(Rota(nome, parametros))

    def desempilhar(self) -> bool:
        """Volta uma tela. Retorna `False` quando já está na raiz."""
        if len(self.pilha) <= 1:
            return False
        self.pilha.pop()
        return True
