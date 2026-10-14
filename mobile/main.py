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

------------------------------------------------------------------------------
Largura no desktop
------------------------------------------------------------------------------
As telas são desenhadas para largura de celular. Para que a janela do desktop
não estique o conteúdo, a árvore inteira do app (conteúdo + FAB + barra
inferior) é montada dentro de uma `ColunaCentral`
(`mobile/components/layout.py`): acima de 440px ela vira uma coluna fixa e
centralizada, abaixo disso ocupa a largura toda, como num celular. Por estar
aqui — no ponto único onde a árvore é montada — nenhuma view precisa saber
disso.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Callable

import flet as ft

# Permite rodar tanto `flet run mobile/main.py` quanto `python mobile/main.py`:
# em ambos os casos a raiz do projeto precisa estar no sys.path para que os
# imports do pacote `mobile` funcionem.
RAIZ_DO_PROJETO = Path(__file__).resolve().parent.parent
if str(RAIZ_DO_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_DO_PROJETO))

from mobile import theme as t  # noqa: E402
from mobile.api_client import ApiClient, ErroApi  # noqa: E402
from mobile.config import obter_configuracao  # noqa: E402
from mobile.components.fab import botao_flutuante  # noqa: E402
from mobile.components.layout import ColunaCentral  # noqa: E402
from mobile.components.nav_bar import barra_de_navegacao  # noqa: E402
from mobile.state import AppState  # noqa: E402
from mobile.views import (  # noqa: E402
    ajuda,
    alterar_senha,
    cadastro,
    configuracoes,
    chat,
    conversas,
    detalhe_solicitacao,
    documento_legal,
    editar_perfil,
    explorar,
    favoritos,
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
    recuperar_senha,
    splash,
)

# No código-fonte os assets permanecem em ``mobile/assets``. No staging de
# distribuição eles ficam na raiz ``assets/``, que é o caminho que o runtime
# Android do Flet 0.86 extrai e serve como ``files/flet/app/assets``.
_ASSETS_DE_DISTRIBUICAO = RAIZ_DO_PROJETO / "assets"
ASSETS_DIR = (
    _ASSETS_DE_DISTRIBUICAO
    if _ASSETS_DE_DISTRIBUICAO.is_dir()
    else RAIZ_DO_PROJETO / "mobile" / "assets"
)
APP_ICON = "brand/logo/app-icon-256.png"
CHAVE_TOKEN = "br.edu.conectacomunidade.app.access_token"


# Registro de rotas: nome -> (função construtora, exibe navegação inferior?).
ROTAS: dict[str, tuple[Callable[["App"], ft.Control], bool]] = {
    "splash": (splash.construir, False),
    "login": (login.construir, False),
    "cadastro": (cadastro.construir, False),
    "recuperar_senha": (recuperar_senha.construir, False),
    # Termos de Uso e Política de Privacidade, abertos pelos links do cadastro.
    "documento_legal": (documento_legal.construir, False),
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
    # Telas abertas pelo menu do Perfil.
    "editar_perfil": (editar_perfil.construir, False),
    "configuracoes": (configuracoes.construir, False),
    "alterar_senha": (alterar_senha.construir, False),
    "ajuda": (ajuda.construir, False),
    "favoritos": (favoritos.construir, False),
    "nova_solicitacao": (nova_solicitacao.construir, False),
    "nova_oferta": (nova_oferta.construir, False),
}

# Rotas que correspondem a um destino da navegação inferior. `publicar` saiu
# daqui: virou a ação do FAB, e por isso empilha como qualquer outra tela.
ABAS_PRINCIPAIS = {"home", "explorar", "mapa", "conversas", "perfil"}
ROTAS_COM_DADOS = {
    "home",
    "favoritos",
    "editar_perfil",
    "configuracoes",
    "explorar",
    "conversas",
    "perfil",
    "detalhe_solicitacao",
    "chat",
    "mapa",
    "ongs",
    "perfil_ong",
    "minhas_solicitacoes",
}


class App:
    """Controlador do aplicativo: estado, navegação e acesso à API.

    Todas as views recebem uma instância desta classe e a usam para navegar,
    chamar a API e exibir avisos — elas nunca tocam na `page` diretamente,
    exceto para casos pontuais como abrir um diálogo.
    """

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.state = AppState()
        self.api = ApiClient(obter_configuracao().api_base_url)
        self.api.ao_sessao_invalida = self._sessao_invalida
        self.preferencias = ft.SharedPreferences()
        self.reduzir_movimento = False

        # Área onde a tela atual é desenhada.
        self._area = ft.Container(
            expand=True,
            bgcolor=t.FUNDO_CLARO,
            animate=ft.Animation(180, ft.AnimationCurve.EASE),
        )
        self._barra = ft.Container(visible=False)
        # O FAB flutua SOBRE a área de conteúdo, e não dentro da barra: daí a
        # área virar um `Stack`. Ele é criado uma vez e só troca de visibilidade
        # conforme a tela, para não recriar o controle a cada navegação.
        self._fab = botao_flutuante(lambda _: self.publicar())
        self._fab.visible = False
        self._camada = ft.Stack([self._area, self._fab], expand=True)
        self._raiz = ft.Column([self._camada, self._barra], spacing=0, expand=True)
        # Limite de largura no desktop. Envolve TUDO — inclusive o FAB e a
        # barra inferior, que por estarem dentro do `_raiz` ficam alinhados à
        # coluna em vez de grudarem nas bordas da janela.
        self._coluna_central = ColunaCentral(self._raiz)

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #
    def iniciar(self) -> None:
        """Configura a página e desenha a primeira tela."""
        self.page.title = "Conecta Comunidade"
        self.page.window.icon = APP_ICON
        # Fundo que aparece nas laterais da coluna central quando a janela é
        # mais larga que ela. No celular a coluna ocupa tudo e ele nunca é visto.
        self.page.bgcolor = t.FUNDO_MOLDURA
        self.page.padding = 0
        self.page.spacing = 0
        self.page.theme = t.tema_do_app()
        self.page.theme_mode = ft.ThemeMode.LIGHT
        # Proporção próxima de um celular, para a demonstração no desktop.
        self.page.window.width = 430
        self.page.window.height = 900
        self.page.on_view_pop = lambda _: self.voltar()
        self.page.on_resize = self._ao_redimensionar

        self._coluna_central.ajustar(getattr(self.page, "width", None))
        self.page.add(ft.SafeArea(content=self._coluna_central.raiz, expand=True))
        self.page.run_task(self._detectar_preferencias_de_acessibilidade)
        self.state.reiniciar("splash")
        self.renderizar()
        self.page.run_task(self._restaurar_sessao)

    async def _detectar_preferencias_de_acessibilidade(self) -> None:
        """Lê a preferência do sistema sem impedir a abertura do aplicativo."""
        try:
            recursos = await ft.SemanticsService().get_accessibility_features()
            self.reduzir_movimento = bool(recursos.reduce_motion)
        except Exception:
            # Algumas plataformas não expõem esse serviço; o app continua com o
            # indicador padrão em vez de falhar na inicialização.
            self.reduzir_movimento = False

    def _ao_redimensionar(self, evento: Any) -> None:
        """Reavalia o limite de largura quando a janela muda de tamanho."""
        # `ajustar` só devolve True quando o estado virou, então arrastar a
        # janela não gera um `update()` por pixel.
        if self._coluna_central.ajustar(getattr(evento, "width", None)):
            self.page.update()

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
            if rota.nome in ROTAS_COM_DADOS:
                self._area.content = (
                    t.esqueleto_da_home() if rota.nome == "home" else t.carregando("Carregando dados...")
                )
                self.page.update()
            conteudo = construtor(self)
        except ErroApi as erro:
            conteudo = self._tela_de_erro(erro.mensagem)

        self._area.content = conteudo
        self._barra.visible = mostra_barra
        self._barra.content = (
            barra_de_navegacao(rota.nome, self._selecionar_aba, self.nao_lidas())
            if mostra_barra
            else None
        )
        # O FAB acompanha os cinco destinos. Em telas empilhadas (detalhe, chat,
        # o próprio publicar) ele sumiria atrás do conteúdo ou duplicaria a ação
        # que a tela já oferece.
        self._fab.visible = rota.nome in ABAS_PRINCIPAIS
        self.page.update()

    def publicar(self) -> None:
        """Ação do FAB: abre a tela de publicar, exigindo sessão ativa."""
        if not self.state.autenticado:
            self.aviso("Entre na sua conta para publicar.", erro=True)
            self.reiniciar("login")
            return
        self.navegar("publicar")

    def _selecionar_aba(self, rota: str) -> None:
        """Trata o clique na navegação inferior (exige sessão ativa)."""
        if rota in {"conversas", "perfil"} and not self.state.autenticado:
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

    def alternar_favorito(self, solicitacao_id: int, favoritada: bool) -> None:
        """Guarda (ou solta) um pedido nos favoritos e redesenha a tela.

        Vive aqui, e não em cada view, porque o coração aparece na Home, no
        Explorar, no detalhe e na própria tela de Favoritos — quatro cópias da
        mesma regra sairiam do lugar na primeira mudança.
        """
        if not self.state.autenticado:
            self.aviso("Entre na sua conta para guardar pedidos.", erro=True)
            self.reiniciar("login")
            return

        try:
            if favoritada:
                self.api.desfavoritar(solicitacao_id)
            else:
                self.api.favoritar(solicitacao_id)
        except ErroApi as erro:
            self.aviso(erro.mensagem, erro=True)
            return

        self.aviso("Removido dos favoritos." if favoritada else "Guardado nos favoritos.")
        self.renderizar()

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
            self._tratar_erro_api(erro)
            return None

        if mensagem_sucesso:
            self.aviso(mensagem_sucesso)
        return resultado

    async def executar_assincrono(self, acao: Callable[[], Any]) -> Any:
        """Executa I/O síncrono sem bloquear o loop que atualiza o Flet."""
        try:
            return await asyncio.to_thread(acao)
        except ErroApi as erro:
            self._tratar_erro_api(erro)
            return None

    def _mostrar_preparacao_de_acesso(self) -> None:
        """Mantém uma superfície útil na transição entre autenticação e Home."""
        self._area.content = ft.Semantics(
            live_region=True,
            container=True,
            label="Preparando seu acesso. Aguarde.",
            value="ocupado",
            content=t.carregando("Preparando seu acesso…"),
        )
        self._barra.visible = False
        self._fab.visible = False
        self.page.update()

    async def _remover_token_persistido(self) -> None:
        await self.preferencias.remove(CHAVE_TOKEN)

    def _sessao_invalida(self) -> None:
        self.state.sair()
        self.api.definir_token(None)
        self.page.run_task(self._remover_token_persistido)

    def _tratar_erro_api(self, erro: ErroApi) -> None:
        if erro.status == 401:
            self._sessao_invalida()
            self.reiniciar("login")
        self.aviso(erro.mensagem, erro=True)

    async def concluir_autenticacao(self, token: str) -> bool:
        """Confirma a sessão e prepara os dados indispensáveis antes da Home.

        A resposta de login/cadastro só é considerada uma sessão válida após a
        confirmação em `/auth/me`. As categorias são pré-carregadas na mesma
        transição, evitando uma tela inicial parcialmente pronta.
        """
        self.api.definir_token(token)
        usuario = await self.executar_assincrono(self.api.eu)
        if usuario is None:
            self.api.definir_token(None)
            return False

        # `/auth/me` inclui dados privados para telas específicas. O estado
        # global segue o contrato público para não replicar CPF, telefone ou
        # nascimento por toda a árvore de views.
        campos_privados = {
            "cpf", "telefone", "data_nascimento", "aceite_termos", "data_aceite",
            "notificar_solicitacoes", "notificar_mensagens", "notificar_atualizacoes",
        }
        usuario_publico = {chave: valor for chave, valor in usuario.items() if chave not in campos_privados}
        self.state.entrar(token, usuario_publico)
        await self.preferencias.set(CHAVE_TOKEN, token)
        self._mostrar_preparacao_de_acesso()
        categorias = await self.executar_assincrono(self.api.listar_categorias)
        # Categorias não impedem o acesso; a Home já tem estado de ausência para
        # esse dado secundário. Ainda assim, aguardamos a solicitação real antes
        # de trocar de tela para não haver redirecionamento prematuro.
        self.state.categorias = categorias or []
        self.reiniciar("home")
        return True

    async def _restaurar_sessao(self) -> None:
        token = await self.preferencias.get(CHAVE_TOKEN)
        if not isinstance(token, str) or not token:
            return
        if await self.concluir_autenticacao(token):
            return
        await self._remover_token_persistido()
        self.state.sair()
        self.reiniciar("login")

    def _tela_de_erro(self, mensagem: str) -> ft.Control:
        """Tela de fallback quando a API não responde durante a montagem."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(t.ICONES["sem_conexao"], size=56, color=t.TEXTO_SECUNDARIO),
                    t.titulo("Sem conexão com a API", 18),
                    ft.Text(
                        mensagem,
                        size=13,
                        color=t.TEXTO_SECUNDARIO,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=8),
                    t.botao_primario(
                        "Tentar novamente", lambda _: self.renderizar(), t.ICONES["recarregar"], 220
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
    ft.run(main, assets_dir=str(ASSETS_DIR))
