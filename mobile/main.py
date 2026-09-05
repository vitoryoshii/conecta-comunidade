"""
Aplicativo Flet do Conecta Comunidade.

Executar com:

    flet run mobile/main.py

A API precisa estar no ar (`uvicorn backend.main:app --reload`).

------------------------------------------------------------------------------
Como a navegação funciona
------------------------------------------------------------------------------
O app mantém a **própria pilha de rotas** dentro do `AppState`, em vez de usar o
roteamento por URL do Flet. Cada tela é uma função `construir(app)` que devolve
um controle; ao navegar, a pilha muda e a árvore é redesenhada. A vantagem é
que o botão "voltar" funciona em qualquer profundidade e a navegação inferior
continua sendo apenas uma troca de rota-raiz.
"""

import sys
from pathlib import Path
from typing import Any, Callable

import flet as ft

# Permite rodar tanto `flet run mobile/main.py` quanto `python mobile/main.py`:
# em ambos os casos a raiz do projeto precisa estar no sys.path para que os
# imports `from mobile...` e `from backend...` funcionem.
RAIZ_DO_PROJETO = Path(__file__).resolve().parent.parent
if str(RAIZ_DO_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_DO_PROJETO))

from mobile import theme as t  # noqa: E402
from mobile.api_client import ApiClient, ErroApi  # noqa: E402
from mobile.components.comuns import navegacao_inferior  # noqa: E402
from mobile.state import AppState  # noqa: E402
from mobile.views import (  # noqa: E402
    cadastro,
    chat,
    conversas,
    detalhe_solicitacao,
    explorar,
    home,
    login,
    mapa,
    minhas_solicitacoes,
    nova_oferta,
    nova_solicitacao,
    ongs,
    perfil,
    perfil_ong,
    publicar,
    quero_ajudar,
    splash,
)

# URL da API. Pode ser sobrescrita pela variável de ambiente API_BASE_URL.
API_BASE_URL = "http://127.0.0.1:8000"

# Registro de rotas: nome -> (função construtora, exibe navegação inferior?).
ROTAS: dict[str, tuple[Callable[["App"], ft.Control], bool]] = {
    "splash": (splash.construir, False),
    "login": (login.construir, False),
    "cadastro": (cadastro.construir, False),
    "home": (home.construir, True),
    "explorar": (explorar.construir, True),
    "publicar": (publicar.construir, True),
    "conversas": (conversas.construir, True),
    "perfil": (perfil.construir, True),
    "detalhe_solicitacao": (detalhe_solicitacao.construir, False),
    "quero_ajudar": (quero_ajudar.construir, False),
    "chat": (chat.construir, False),
    "mapa": (mapa.construir, True),
    "ongs": (ongs.construir, True),
    "perfil_ong": (perfil_ong.construir, False),
    "minhas_solicitacoes": (minhas_solicitacoes.construir, False),
    "nova_solicitacao": (nova_solicitacao.construir, False),
    "nova_oferta": (nova_oferta.construir, False),
}

# Rotas que correspondem a uma aba da navegação inferior.
ABAS_PRINCIPAIS = {"home", "explorar", "publicar", "conversas", "perfil"}


class App:
    """Controlador do aplicativo: estado, navegação e acesso à API.

    Todas as views recebem uma instância desta classe e a usam para navegar,
    chamar a API e exibir avisos — elas nunca tocam na `page` diretamente,
    exceto para casos pontuais como abrir um diálogo.
    """

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.state = AppState()
        self.api = ApiClient(API_BASE_URL)

        # Área onde a tela atual é desenhada.
        self._area = ft.Container(expand=True, bgcolor=t.FUNDO_CLARO)
        self._barra = ft.Container(visible=False)
        self._raiz = ft.Column([self._area, self._barra], spacing=0, expand=True)

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #
    def iniciar(self) -> None:
        """Configura a página e desenha a primeira tela."""
        self.page.title = "Conecta Comunidade"
        self.page.bgcolor = t.FUNDO_CLARO
        self.page.padding = 0
        self.page.spacing = 0
        self.page.theme = t.tema_do_app()
        self.page.theme_mode = ft.ThemeMode.LIGHT
        # Proporção próxima de um celular, para a demonstração no desktop.
        self.page.window.width = 430
        self.page.window.height = 900
        self.page.on_view_pop = lambda _: self.voltar()

        self.page.add(ft.SafeArea(content=self._raiz, expand=True))
        self.state.reiniciar("splash")
        self.renderizar()

    # ------------------------------------------------------------------ #
    # Navegação
    # ------------------------------------------------------------------ #
    def navegar(self, rota: str, /, **parametros: Any) -> None:
        """Abre uma tela nova por cima da atual.

        `rota` é posicional-only: os parâmetros de tela são chaves livres
        (`nome`, `id`, `busca`...) e não podem colidir com o argumento.
        """
        # As abas principais nunca empilham: elas reiniciam a navegação.
        if rota in ABAS_PRINCIPAIS:
            self.state.reiniciar(rota, **parametros)
        else:
            self.state.empilhar(rota, **parametros)
        self.renderizar()

    def substituir(self, rota: str, /, **parametros: Any) -> None:
        """Troca a tela atual sem crescer a pilha."""
        self.state.substituir(rota, **parametros)
        self.renderizar()

    def reiniciar(self, rota: str, /, **parametros: Any) -> None:
        """Zera a pilha e começa em uma nova rota (login, logout, entrada)."""
        self.state.reiniciar(rota, **parametros)
        self.renderizar()

    def voltar(self, _: Any = None) -> None:
        """Volta uma tela; na raiz, cai para a Home."""
        if not self.state.desempilhar():
            self.state.reiniciar("home")
        self.renderizar()

    def renderizar(self) -> None:
        """Redesenha a tela do topo da pilha, com tratamento de erro."""
        rota = self.state.rota_atual
        construtor, mostra_barra = ROTAS.get(rota.nome, ROTAS["home"])

        try:
            conteudo = construtor(self)
        except ErroApi as erro:
            conteudo = self._tela_de_erro(erro.mensagem)

        self._area.content = conteudo
        self._barra.visible = mostra_barra
        self._barra.content = (
            navegacao_inferior(rota.nome, self._selecionar_aba, self.nao_lidas())
            if mostra_barra
            else None
        )
        self.page.update()

    def _selecionar_aba(self, rota: str) -> None:
        """Trata o clique na navegação inferior (exige sessão ativa)."""
        if rota in {"publicar", "conversas", "perfil"} and not self.state.autenticado:
            self.aviso("Entre na sua conta para usar esta área.", erro=True)
            self.reiniciar("login")
            return
        self.navegar(rota)

    # ------------------------------------------------------------------ #
    # Apoio às views
    # ------------------------------------------------------------------ #
    def aviso(self, mensagem: str, erro: bool = False) -> None:
        """Exibe uma mensagem rápida no rodapé da tela (snackbar)."""
        self.page.show_dialog(
            ft.SnackBar(
                content=ft.Text(mensagem, color=t.BRANCO),
                bgcolor=t.URGENCIA if erro else t.VERDE_ESCURO,
                duration=3000,
            )
        )

    def nao_lidas(self) -> int:
        """Total de mensagens não lidas, exibido no badge da aba Mensagens."""
        if not self.state.autenticado:
            return 0
        try:
            return sum(conversa.get("nao_lidas", 0) for conversa in self.api.listar_conversas())
        except ErroApi:
            return 0

    def categorias(self) -> list[dict[str, Any]]:
        """Categorias da API, buscadas uma única vez por sessão."""
        if not self.state.categorias:
            try:
                self.state.categorias = self.api.listar_categorias()
            except ErroApi:
                self.state.categorias = []
        return self.state.categorias

    def coordenadas(self) -> dict[str, float]:
        """Lat/long do usuário logado, no formato aceito pelos filtros da API."""
        if self.state.latitude is None or self.state.longitude is None:
            return {}
        return {"lat": self.state.latitude, "long": self.state.longitude}

    def executar(self, acao: Callable[[], Any], mensagem_sucesso: str | None = None) -> Any:
        """Roda uma chamada à API tratando `ErroApi` com um aviso na tela.

        Devolve o resultado da ação ou `None` quando ela falhou — o que permite
        às views escreverem `if resultado is None: return`.
        """
        try:
            resultado = acao()
        except ErroApi as erro:
            self.aviso(erro.mensagem, erro=True)
            return None

        if mensagem_sucesso:
            self.aviso(mensagem_sucesso)
        return resultado

    def _tela_de_erro(self, mensagem: str) -> ft.Control:
        """Tela de fallback quando a API não responde durante a montagem."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.CLOUD_OFF, size=56, color=t.TEXTO_SECUNDARIO),
                    t.titulo("Sem conexão com a API", 18),
                    ft.Text(
                        mensagem,
                        size=13,
                        color=t.TEXTO_SECUNDARIO,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=8),
                    t.botao_primario(
                        "Tentar novamente", lambda _: self.renderizar(), ft.Icons.REFRESH, 220
                    ),
                    t.botao_secundario(
                        "Voltar ao início", lambda _: self.reiniciar("splash"), largura=220
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12,
            ),
            padding=30,
            expand=True,
            alignment=ft.Alignment.CENTER,
        )


def main(page: ft.Page) -> None:
    """Ponto de entrada chamado pelo Flet."""
    App(page).iniciar()


if __name__ == "__main__":
    ft.run(main)
