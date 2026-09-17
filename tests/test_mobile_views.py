"""
Testes de renderização das telas Flet.

Não abrem janela: montam cada view em memória, contra a API real servida pelo
`TestClient` do FastAPI (sem rede e sem Uvicorn). Isso garante que nenhuma tela quebre por um controle mal
construído ou por um campo que a API deixou de devolver — a falha aparece aqui,
e não durante a apresentação.
"""

from collections.abc import Generator
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import urlparse
from urllib.request import url2pathname

import flet as ft
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.database import get_session
from backend.main import app as api_fastapi
from backend.models import ONG, Categoria, Usuario
from mobile.api_client import ApiClient
from mobile import mapa_tiles
from mobile import theme as t
from mobile.views import mapa as mapa_view
from mobile.components.nav_bar import DESTINOS
from mobile.main import ABAS_PRINCIPAIS, ROTAS, App


class PaginaFalsa(SimpleNamespace):
    """Dublê da `ft.Page`: só precisa aceitar as chamadas feitas nos handlers."""

    def update(self) -> None:
        """Nenhuma renderização real acontece nos testes."""

    def show_dialog(self, dialogo: Any) -> None:
        """Registra o último diálogo/aviso exibido."""
        self.ultimo_dialogo = dialogo

    def pop_dialog(self) -> None:
        """Fecha o diálogo aberto."""


@pytest.fixture(name="app_mobile")
def fixture_app_mobile(
    session: Session,
    usuario_ana: Usuario,
    categorias: dict[str, Categoria],
    ong_verificada: ONG,
) -> Generator[App, None, None]:
    """App Flet conectado à API de teste, já autenticado como Ana."""

    def obter_sessao_de_teste() -> Generator[Session, None, None]:
        yield session

    api_fastapi.dependency_overrides[get_session] = obter_sessao_de_teste

    aplicacao = App(PaginaFalsa())
    # O TestClient do FastAPI é um `httpx.Client` que fala direto com o app,
    # sem rede: trocando o transporte do ApiClient por ele, as telas rodam
    # contra a API de verdade sem precisar subir o Uvicorn.
    aplicacao.api = ApiClient("http://teste")
    aplicacao.api._http = TestClient(api_fastapi, base_url="http://teste")

    resposta = aplicacao.api.login(usuario_ana.email, "senha123")
    aplicacao.api.definir_token(resposta["access_token"])
    aplicacao.state.entrar(resposta["access_token"], resposta["usuario"])

    yield aplicacao

    aplicacao.api.fechar()
    api_fastapi.dependency_overrides.clear()


def _parametros_da_rota(nome: str, app_mobile: App) -> dict[str, Any]:
    """Parâmetros mínimos exigidos por cada rota que depende de contexto."""
    if nome == "detalhe_solicitacao":
        return {"id": _id_da_primeira_solicitacao(app_mobile)}
    if nome == "quero_ajudar":
        return {
            "solicitacao": app_mobile.api.obter_solicitacao(
                _id_da_primeira_solicitacao(app_mobile)
            )
        }
    if nome == "chat":
        return {"com": app_mobile.state.usuario_id, "nome": "Conversa de teste"}
    if nome == "perfil_ong":
        return {"id": _id_da_primeira_ong(app_mobile)}
    return {}


def _id_da_primeira_solicitacao(app_mobile: App) -> int:
    """Cria (se preciso) e devolve o id de uma solicitação para os testes."""
    existentes = app_mobile.api.listar_solicitacoes()
    if existentes:
        return existentes[0]["id"]

    categoria = app_mobile.api.listar_categorias()[0]
    criada = app_mobile.api.criar_solicitacao(
        {
            "titulo": "Pedido para renderização",
            "descricao": "Criado pelo teste de views.",
            "categoria_id": categoria["id"],
            "urgencia": "alta",
            "emergencia": True,
        }
    )
    return criada["id"]


def _id_da_primeira_ong(app_mobile: App) -> int | None:
    """Id da primeira ONG cadastrada, ou `None` quando não houver nenhuma."""
    ongs = app_mobile.api.listar_ongs()
    return ongs[0]["id"] if ongs else None


@pytest.mark.parametrize("nome_da_rota", sorted(ROTAS))
def test_todas_as_telas_sao_construidas(app_mobile: App, nome_da_rota: str) -> None:
    """Cada rota registrada precisa devolver um controle Flet válido."""
    if nome_da_rota == "perfil_ong" and _id_da_primeira_ong(app_mobile) is None:
        pytest.skip("Sem ONG cadastrada neste cenário.")

    construtor, _ = ROTAS[nome_da_rota]
    app_mobile.state.reiniciar(nome_da_rota, **_parametros_da_rota(nome_da_rota, app_mobile))

    controle = construtor(app_mobile)

    assert isinstance(controle, ft.Control)


def test_navegacao_empilha_e_volta(app_mobile: App) -> None:
    """A pilha de rotas precisa suportar abrir e voltar telas."""
    app_mobile.state.reiniciar("home")
    app_mobile.state.empilhar("detalhe_solicitacao", id=1)

    assert app_mobile.state.rota_atual.nome == "detalhe_solicitacao"
    assert app_mobile.state.desempilhar() is True
    assert app_mobile.state.rota_atual.nome == "home"
    # Na raiz, não há mais para onde voltar.
    assert app_mobile.state.desempilhar() is False


def test_abas_principais_reiniciam_a_pilha(app_mobile: App) -> None:
    """Trocar de aba não deve acumular telas na pilha de navegação."""
    app_mobile.state.reiniciar("home")
    app_mobile.state.empilhar("detalhe_solicitacao", id=1)
    app_mobile.state.reiniciar("explorar")

    assert len(app_mobile.state.pilha) == 1
    assert app_mobile.state.rota_atual.nome == "explorar"


def test_sair_limpa_a_sessao(app_mobile: App) -> None:
    """Logout precisa apagar token, usuário e pilha."""
    app_mobile.state.sair()

    assert app_mobile.state.autenticado is False
    assert app_mobile.state.token is None
    assert app_mobile.state.pilha == []

def _descendentes(controle: ft.Control):
    """Percorre a árvore de controles de uma tela montada."""
    vistos: set[int] = set()
    pilha = [controle]
    while pilha:
        atual = pilha.pop()
        if id(atual) in vistos:
            continue
        vistos.add(id(atual))
        yield atual
        for campo in ("content", "controls"):
            valor = getattr(atual, campo, None)
            if isinstance(valor, list):
                pilha.extend(c for c in valor if isinstance(c, ft.Control))
            elif isinstance(valor, ft.Control):
                pilha.append(valor)


def _por_dica(tela: ft.Control, dica: str) -> Any:
    """Acha um campo ou seletor pelo `hint_text`.

    A busca é por dica, e não por posição na árvore, porque a ordem em que os
    controles aparecem na varredura não acompanha a ordem de montagem da tela.
    """
    for controle in _descendentes(tela):
        if getattr(controle, "hint_text", None) == dica:
            return controle
    raise AssertionError(f"nenhum controle com a dica {dica!r}")


def test_cadastro_carrega_cidades_no_formato_da_api(app_mobile: App) -> None:
    """Escolher a UF preenche o seletor de cidade com o que a API devolve hoje.

    Este teste existe porque os testes de API sozinhos não pegam um descompasso
    de formato: se `/localidades/.../cidades` voltar a devolver strings, ou o
    handler passar a esperar outra coisa, o cadastro quebra em runtime com
    `TypeError` e só a tela denuncia.
    """
    app_mobile.state.reiniciar("cadastro")
    tela = ROTAS["cadastro"][0](app_mobile)

    seletor_estado = _por_dica(tela, "Selecione seu estado")
    seletor_cidade = _por_dica(tela, "Escolha o estado primeiro")

    assert seletor_cidade.disabled is True, "cidade deve começar bloqueada"

    seletor_estado.value = "BA"
    seletor_estado.on_select(None)

    assert seletor_cidade.disabled is False
    assert len(seletor_cidade.options) == 417
    assert "Salvador" in [opcao.key for opcao in seletor_cidade.options]


def _digitar(tela: ft.Control, dica: str, valor: str) -> Any:
    """Escreve em um campo e dispara o `on_change`, como faria o teclado."""
    campo = _por_dica(tela, dica)
    campo.value = valor
    if campo.on_change is not None:
        campo.on_change(SimpleNamespace(control=campo))
    return campo


def _escolher_data(tela: ft.Control, app_mobile: App, escolhida: date) -> Any:
    """Clica no campo de nascimento e escolhe uma data no seletor que abrir.

    Vai pelo caminho do usuário — clique no campo, diálogo, confirmação — porque
    era justamente esse caminho que estava quebrado no desktop.
    """
    campo = _por_dica(tela, "dd/mm/aaaa")
    campo.on_click(None)

    seletor = app_mobile.page.ultimo_dialogo
    seletor.value = datetime(escolhida.year, escolhida.month, escolhida.day)
    seletor.on_change(SimpleNamespace(control=seletor))
    return campo


def _preencher_cadastro(
    tela: ft.Control,
    app_mobile: App,
    *,
    email: str = "salvador.tela@teste.com",
    senha: str = "senha123",
    confirmacao: str | None = None,
    aceitar: bool = True,
) -> ft.Checkbox:
    """Preenche o formulário inteiro como um usuário faria, e devolve o checkbox."""
    # A dica da cidade muda depois de carregar a lista: pegamos a referência antes.
    seletor_cidade = _por_dica(tela, "Escolha o estado primeiro")

    _digitar(tela, "Seu nome completo", "Pessoa de Salvador")
    _digitar(tela, "000.000.000-00", "529.982.247-25")
    _digitar(tela, "seu@email.com", email)
    _digitar(tela, "(00) 00000-0000", "(71) 98765-4321")
    _digitar(tela, "Mínimo 6 caracteres", senha)
    _digitar(tela, "Repita a senha", senha if confirmacao is None else confirmacao)
    _escolher_data(tela, app_mobile, date(1995, 4, 12))

    seletor_estado = _por_dica(tela, "Selecione seu estado")
    seletor_estado.value = "BA"
    seletor_estado.on_select(None)
    seletor_cidade.value = "Salvador"
    seletor_cidade.on_select(None)

    caixa = next(c for c in _descendentes(tela) if isinstance(c, ft.Checkbox))
    caixa.value = aceitar
    caixa.on_change(SimpleNamespace(control=caixa))
    return caixa


def test_cadastro_abre_o_seletor_de_data_pelo_proprio_campo(app_mobile: App) -> None:
    """Clicar no campo abre o calendário — e a seleção inicial é válida.

    Os dois detalhes que travavam o desktop estão aqui: o `on_click` precisa
    estar no `TextField` (um `Container` em volta nunca recebe o clique, porque o
    campo o consome) e o `value` do seletor precisa cair dentro de
    [`first_date`, `last_date`] — um calendário que abre em data proibida não
    abre.
    """
    app_mobile.state.reiniciar("cadastro")
    tela = ROTAS["cadastro"][0](app_mobile)

    campo = _por_dica(tela, "dd/mm/aaaa")
    assert campo.read_only is True, "a data não é digitada, é escolhida"
    assert campo.on_click is not None, "o clique tem de estar no próprio campo"

    campo.on_click(None)
    seletor = app_mobile.page.ultimo_dialogo
    assert isinstance(seletor, ft.DatePicker)

    hoje = date.today()
    assert seletor.first_date == date(1900, 1, 1)
    assert seletor.last_date == date(hoje.year - 18, hoje.month, hoje.day)
    assert seletor.first_date <= seletor.value <= seletor.last_date

    # O botão de calendário dentro do campo abre o mesmo seletor.
    assert campo.suffix.on_click is not None

    escolhida = _escolher_data(tela, app_mobile, date(1995, 4, 12))
    assert escolhida.value == "12/04/1995", "a data aparece no formato brasileiro"
    assert escolhida.data == date(1995, 4, 12), "e o `date` real vai para o envio"


def test_cadastro_exige_consentimento_lgpd(app_mobile: App) -> None:
    """O botão "Criar conta" só liga com o formulário cheio e os termos aceitos."""
    app_mobile.state.reiniciar("cadastro")
    tela = ROTAS["cadastro"][0](app_mobile)

    botao = next(c for c in _descendentes(tela) if isinstance(c, ft.FilledButton))
    assert botao.disabled is True, "cadastro não pode começar liberado"

    # Só o aceite, sem os campos: continua travado.
    caixa = next(c for c in _descendentes(tela) if isinstance(c, ft.Checkbox))
    caixa.value = True
    caixa.on_change(SimpleNamespace(control=caixa))
    assert botao.disabled is True, "aceitar os termos não supre os campos vazios"

    caixa = _preencher_cadastro(tela, app_mobile)
    assert botao.disabled is False

    caixa.value = False
    caixa.on_change(SimpleNamespace(control=caixa))
    assert botao.disabled is True, "desmarcar os termos precisa travar de novo"


def test_confirmacao_de_senha_avisa_ao_vivo(app_mobile: App) -> None:
    """A confirmação dá o retorno enquanto se digita, sem esperar o envio."""
    app_mobile.state.reiniciar("cadastro")
    tela = ROTAS["cadastro"][0](app_mobile)

    botao = next(c for c in _descendentes(tela) if isinstance(c, ft.FilledButton))
    confirmacao = _por_dica(tela, "Repita a senha")
    _digitar(tela, "Mínimo 6 caracteres", "senha123")

    # Vazio: nada é dito — a pessoa ainda não começou a confirmar.
    status = next(
        c for c in _descendentes(tela) if isinstance(c, ft.Container) and c.visible is False
    )
    assert status.content is None

    _digitar(tela, "Repita a senha", "senha1")
    assert status.visible is True
    assert "não coincidem" in status.content.controls[1].value

    _digitar(tela, "Repita a senha", "senha123")
    assert status.visible is True
    assert status.content.controls[1].value == "As senhas coincidem"
    assert confirmacao.error is None

    # Divergir de novo esconde o verde e volta a travar o botão.
    _preencher_cadastro(tela, app_mobile, confirmacao="outra-senha")
    assert "não coincidem" in status.content.controls[1].value
    assert botao.disabled is True


def test_cadastro_nao_envia_com_confirmacao_diferente(app_mobile: App) -> None:
    """Senha e confirmação diferentes não chegam à API: o campo acende e para."""
    app_mobile.state.reiniciar("cadastro")
    tela = ROTAS["cadastro"][0](app_mobile)

    _preencher_cadastro(
        tela, app_mobile, email="divergente@teste.com", confirmacao="outra-senha"
    )
    next(c for c in _descendentes(tela) if isinstance(c, ft.FilledButton)).on_click(None)

    assert _por_dica(tela, "Repita a senha").error == "As senhas não coincidem"
    # Nada de sessão nova: o cadastro não foi enviado.
    assert app_mobile.state.usuario["email"] != "divergente@teste.com"


def test_links_do_consentimento_abrem_os_documentos(app_mobile: App) -> None:
    """"Termos de Uso" e "Política de Privacidade" são clicáveis dentro da frase."""
    app_mobile.state.reiniciar("cadastro")
    tela = ROTAS["cadastro"][0](app_mobile)

    caixa = next(c for c in _descendentes(tela) if isinstance(c, ft.Checkbox))
    trechos = {span.text: span for span in caixa.label.spans}
    assert trechos["Termos de Uso"].on_click is not None
    assert trechos["Política de Privacidade"].on_click is not None

    trechos["Política de Privacidade"].on_click(None)

    rota = app_mobile.state.rota_atual
    assert rota.nome == "documento_legal"
    assert rota.parametros == {"documento": "privacidade"}
    # A tela do documento precisa montar com o texto do arquivo.
    documento = ROTAS["documento_legal"][0](app_mobile)
    markdown = next(c for c in _descendentes(documento) if isinstance(c, ft.Markdown))
    assert "Política de Privacidade" in markdown.value
    assert "LGPD" in markdown.value


def test_voltar_do_documento_preserva_o_cadastro(app_mobile: App) -> None:
    """Ler os termos no meio do cadastro não pode apagar o que já foi digitado."""
    app_mobile.state.reiniciar("cadastro")
    tela = ROTAS["cadastro"][0](app_mobile)
    _preencher_cadastro(tela, app_mobile, email="preservado@teste.com")

    caixa = next(c for c in _descendentes(tela) if isinstance(c, ft.Checkbox))
    next(span for span in caixa.label.spans if span.text == "Termos de Uso").on_click(None)
    assert app_mobile.state.rota_atual.nome == "documento_legal"

    # Voltar reconstrói o cadastro: o rascunho do `AppState` é que o repovoa.
    app_mobile.voltar()
    assert app_mobile.state.rota_atual.nome == "cadastro"
    de_volta = ROTAS["cadastro"][0](app_mobile)

    assert _por_dica(de_volta, "Seu nome completo").value == "Pessoa de Salvador"
    assert _por_dica(de_volta, "seu@email.com").value == "preservado@teste.com"
    assert _por_dica(de_volta, "000.000.000-00").value == "529.982.247-25"
    assert _por_dica(de_volta, "Repita a senha").value == "senha123"
    assert _por_dica(de_volta, "dd/mm/aaaa").data == date(1995, 4, 12)
    assert _por_dica(de_volta, "Selecione seu estado").value == "BA"
    # A cidade volta com a lista carregada, de onde saem as coordenadas do envio.
    assert _por_dica(de_volta, "Digite para buscar").value == "Salvador"
    assert next(c for c in _descendentes(de_volta) if isinstance(c, ft.Checkbox)).value is True
    # Com tudo de volta, o botão continua liberado.
    assert next(c for c in _descendentes(de_volta) if isinstance(c, ft.FilledButton)).disabled is False


def test_sair_do_cadastro_descarta_o_rascunho(app_mobile: App) -> None:
    """A senha guardada no rascunho não sobrevive a abandonar o fluxo."""
    app_mobile.state.reiniciar("cadastro")
    tela = ROTAS["cadastro"][0](app_mobile)
    _preencher_cadastro(tela, app_mobile)

    caixa = next(c for c in _descendentes(tela) if isinstance(c, ft.Checkbox))
    next(span for span in caixa.label.spans if span.text == "Termos de Uso").on_click(None)
    assert app_mobile.state.rascunho_cadastro, "o rascunho existe enquanto se lê o documento"

    app_mobile.voltar()
    tela = ROTAS["cadastro"][0](app_mobile)
    # Link "Entrar": sai do cadastro de vez.
    next(c for c in _descendentes(tela) if isinstance(c, ft.TextButton)).on_click(None)

    assert app_mobile.state.rascunho_cadastro == {}


def test_cadastro_envia_as_coordenadas_da_cidade(app_mobile: App) -> None:
    """O cadastro pela tela grava o usuário na cidade escolhida, não em (0, 0)."""
    app_mobile.state.reiniciar("cadastro")
    tela = ROTAS["cadastro"][0](app_mobile)

    # Digitado com máscara, como o usuário faria; a tela envia só os dígitos.
    _preencher_cadastro(tela, app_mobile)

    botao = next(c for c in _descendentes(tela) if isinstance(c, ft.FilledButton))
    botao.on_click(None)

    usuario = app_mobile.state.usuario
    assert usuario["estado"] == "BA"
    assert usuario["cidade"] == "Salvador"
    assert usuario["latitude"] != 0.0
    assert usuario["longitude"] != 0.0
    # O perfil público não carrega dado pessoal nenhum.
    for campo in ("cpf", "telefone", "data_nascimento"):
        assert campo not in usuario


def test_cadastro_acusa_campos_invalidos_antes_de_enviar(app_mobile: App) -> None:
    """Com os termos aceitos e o formulário vazio, os campos acendem em vermelho."""
    app_mobile.state.reiniciar("cadastro")
    tela = ROTAS["cadastro"][0](app_mobile)

    caixa = next(c for c in _descendentes(tela) if isinstance(c, ft.Checkbox))
    caixa.value = True
    caixa.on_change(SimpleNamespace(control=caixa))

    next(c for c in _descendentes(tela) if isinstance(c, ft.FilledButton)).on_click(None)

    # Todos de uma vez, e não um por envio.
    for dica in ("Seu nome completo", "000.000.000-00", "seu@email.com", "(00) 00000-0000"):
        assert _por_dica(tela, dica).error, f"{dica} deveria estar marcado"


# --------------------------------------------------------------------------- #
# Navegação: cinco destinos + FAB
# --------------------------------------------------------------------------- #
def test_barra_tem_cinco_destinos_uniformes_com_o_mapa() -> None:
    """A barra tem cinco destinos de mesmo peso; publicar não é destino."""
    rotas = [rota for rota, _, _, _ in DESTINOS]

    assert rotas == ["home", "explorar", "mapa", "conversas", "perfil"]
    assert "publicar" not in rotas, "publicar é ação do FAB, não um destino"
    # Toda rota da barra precisa existir e reiniciar a pilha ao ser tocada.
    assert set(rotas) == ABAS_PRINCIPAIS
    assert set(rotas) <= set(ROTAS)


def test_fab_aparece_nos_destinos_e_some_nas_telas_empilhadas(app_mobile: App) -> None:
    """O FAB acompanha os cinco destinos e sai do caminho nas telas de detalhe."""
    app_mobile.reiniciar("home")
    # `_fab` é da composição do App: o teste o lê para garantir que a camada
    # flutuante existe e que a visibilidade acompanha a rota.
    assert app_mobile._fab.visible is True

    app_mobile.navegar("detalhe_solicitacao", id=_id_da_primeira_solicitacao(app_mobile))
    assert app_mobile._fab.visible is False

    app_mobile.reiniciar("explorar")
    assert app_mobile._fab.visible is True


def test_fab_abre_a_tela_de_publicar(app_mobile: App) -> None:
    """A ação do FAB é a mesma de antes: escolher o que publicar."""
    app_mobile.reiniciar("home")

    app_mobile.publicar()

    assert app_mobile.state.rota_atual.nome == "publicar"
    # Empilhou: dá para voltar de onde veio.
    assert app_mobile.state.desempilhar() is True
    assert app_mobile.state.rota_atual.nome == "home"


def test_fab_exige_sessao_para_publicar(app_mobile: App) -> None:
    """Visitante que toca no FAB vai para o login, não para o formulário."""
    app_mobile.state.sair()

    app_mobile.publicar()

    assert app_mobile.state.rota_atual.nome == "login"


# --------------------------------------------------------------------------- #
# Padrão visual premium
# --------------------------------------------------------------------------- #
def test_cartao_separa_por_sombra_e_nao_por_traco() -> None:
    """A superfície padrão não desenha contorno: quem separa é a sombra."""
    comum = t.cartao(ft.Text("qualquer"))

    assert comum.border is None, "o traço cinza saiu do cartão padrão"
    assert comum.shadow is t.SOMBRA_CARD
    assert comum.border_radius == t.RAIO_CARD

    # A borda sobreviveu como exceção: hoje, só a emergência a usa.
    destacado = t.cartao(ft.Text("emergência"), borda=t.URGENCIA)
    assert destacado.border is not None


def test_telas_do_redesign_nao_tem_borda_cinza(app_mobile: App) -> None:
    """Nenhuma superfície das telas internas volta a desenhar traço cinza."""
    for rota in ("home", "explorar", "perfil", "mapa"):
        app_mobile.state.reiniciar(rota)
        tela = ROTAS[rota][0](app_mobile)

        for controle in _descendentes(tela):
            borda = getattr(controle, "border", None)
            if borda is None:
                continue
            lados = [getattr(borda, lado, None) for lado in ("top", "right", "bottom", "left")]
            cores = {getattr(s, "color", None) for s in lados if s is not None}
            assert t.BORDA not in cores, f"{rota}: sobrou contorno cinza em {controle}"


def test_cor_da_categoria_nao_depende_da_ordem_da_api() -> None:
    """A mesma categoria tem sempre o mesmo par de cores, pelo nome do ícone."""
    agua = t.cores_da_categoria("water_drop")
    alimentos = t.cores_da_categoria("restaurant")

    assert agua != alimentos
    assert agua == t.cores_da_categoria("water_drop"), "a cor não pode variar"
    # Categoria nova, criada no backend, cai no par neutro em vez de quebrar.
    assert t.cores_da_categoria("brinquedos") == t.COR_CATEGORIA_PADRAO
    assert t.cores_da_categoria(None) == t.COR_CATEGORIA_PADRAO


def test_impacto_do_perfil_divide_a_largura_em_tres(app_mobile: App) -> None:
    """Os três cartões de impacto expandem — nenhum fica cortado na tela estreita."""
    app_mobile.state.reiniciar("perfil")
    tela = ROTAS["perfil"][0](app_mobile)

    rotulos = ("Solicitações atendidas", "Doações recebidas", "Ações como voluntário")
    encontrados = [
        c
        for c in _descendentes(tela)
        if isinstance(c, ft.Container)
        and isinstance(c.content, ft.Column)
        and any(
            isinstance(f, ft.Text) and f.value in rotulos
            for f in c.content.controls
        )
    ]

    assert len(encontrados) == 3, "os três números de impacto precisam estar na tela"
    for cartao in encontrados:
        assert cartao.expand is True, "largura fixa volta a cortar o terceiro cartão"
        assert cartao.width is None


# --------------------------------------------------------------------------- #
# Mapa real (tiles do OpenStreetMap)
# --------------------------------------------------------------------------- #
def _imagens_de_tile(tela: ft.Control) -> list[ft.Image]:
    """Todas as imagens de tile do OSM presentes na tela do mapa."""
    return [
        c
        for c in _descendentes(tela)
        if isinstance(c, ft.Image) and "tile.openstreetmap.org" in (c.src or "")
    ]


def test_mapa_desenha_tiles_do_osm_e_nao_um_fundo_vazio(app_mobile: App) -> None:
    """A área do mapa é coberta por imagens de tile, com crédito ao OSM."""
    app_mobile.state.reiniciar("mapa")
    tela = ROTAS["mapa"][0](app_mobile)

    tiles = _imagens_de_tile(tela)
    assert tiles, "sem tile, a tela volta a ser o retângulo vazio"
    # Cada tile tem posição própria dentro da área e um fallback visual.
    for tile in tiles:
        assert tile.left is not None and tile.top is not None
        assert tile.error_content is not None, "sem rede, o buraco tem de ser discreto"

    creditos = [
        c
        for c in _descendentes(tela)
        if isinstance(c, ft.Text) and c.value == mapa_tiles.CREDITO
    ]
    assert creditos, "a atribuição ao OpenStreetMap é exigida pela licença"


def test_mapa_posiciona_os_pinos_sobre_os_tiles(app_mobile: App) -> None:
    """Cada ponto vira um pino dentro da área, na posição projetada."""
    app_mobile.state.reiniciar("mapa")
    pontos = app_mobile.api.pontos_do_mapa(**app_mobile.coordenadas())["pontos"]
    assert pontos, "o cenário de teste precisa de pontos no mapa"

    tela = ROTAS["mapa"][0](app_mobile)
    pinos = [
        c
        for c in _descendentes(tela)
        if isinstance(c, ft.Container)
        and c.tooltip
        and isinstance(c.content, ft.Icon)
        and c.left is not None
        and c.on_click is not None
    ]

    assert len(pinos) == len(pontos)
    for pino in pinos:
        assert 0 <= pino.left <= mapa_view.LARGURA_MAPA
        assert 0 <= pino.top <= mapa_view.ALTURA_MAPA


def test_filtros_do_mapa_mudam_pontos_e_contagem(app_mobile: App) -> None:
    """Desligar um tipo tira os pinos dele do mapa e do contador."""
    # Garante os dois tipos no cenário: uma solicitação (ajuda) e a ONG.
    _id_da_primeira_solicitacao(app_mobile)

    app_mobile.state.reiniciar("mapa")
    ROTAS["mapa"][0](app_mobile)
    total_de_pontos = len(
        app_mobile.api.pontos_do_mapa(**app_mobile.coordenadas())["pontos"]
    )

    # Só ONGs: o mesmo caminho que o toque no painel de filtros percorre.
    app_mobile.state.substituir("mapa", tipos=["ong"])
    filtrada = ROTAS["mapa"][0](app_mobile)

    so_ongs = app_mobile.api.pontos_do_mapa(tipos=["ong"], **app_mobile.coordenadas())
    assert all(p["tipo"] == "ong" for p in so_ongs["pontos"])
    assert len(so_ongs["pontos"]) < total_de_pontos, "o filtro precisa reduzir os pontos"

    # A contagem do cabeçalho acompanha o filtro.
    rotulo = f"{len(so_ongs['pontos'])} ponto"
    assert any(
        isinstance(c, ft.Text) and c.value and c.value.startswith(rotulo)
        for c in _descendentes(filtrada)
    ), "o chip de contagem não acompanhou o filtro"


def test_mapa_interativo_gera_pagina_leaflet_com_os_pontos(app_mobile: App) -> None:
    """O botão do mapa interativo abre uma página Leaflet com os mesmos pontos."""
    app_mobile.state.reiniciar("mapa")
    tela = ROTAS["mapa"][0](app_mobile)

    botao = next(
        c
        for c in _descendentes(tela)
        if isinstance(c, ft.Container) and c.tooltip == "Mapa com zoom e arrasto, no navegador"
    )

    abertos: list[str] = []
    app_mobile.page.launch_url = abertos.append
    botao.on_click(None)

    assert abertos, "o botão precisa abrir alguma coisa"
    caminho = Path(url2pathname(urlparse(abertos[0]).path))
    pagina = caminho.read_text(encoding="utf-8")
    caminho.unlink()

    assert "leaflet" in pagina.lower()
    assert "tile.openstreetmap.org" in pagina
    for ponto in app_mobile.api.pontos_do_mapa(**app_mobile.coordenadas())["pontos"]:
        assert f'"id": {ponto["id"]}' in pagina
