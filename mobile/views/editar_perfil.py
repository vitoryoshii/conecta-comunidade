"""Tela de edição do próprio perfil.

Edita o que o usuário pode mudar sozinho: nome, e-mail, telefone, região e foto.

O **CPF** continua somente para leitura, e mascarado como a API o entrega
(`***.456.789-**`): documento não se troca pela tela de perfil, e nem esta tela
vê o número inteiro. O **e-mail** passou a ser editável — quem troca de endereço
precisa conseguir continuar entrando na conta —, com unicidade conferida pela
API. A troca ainda não é confirmada por link; veja o TODO em
`backend/routers/usuarios.py`.

A região usa os mesmos dois passos do cadastro (estado e depois cidade, do
IBGE), porque mudar de cidade também move o usuário no mapa.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from mobile import avatares, mascaras
from mobile import theme as t
from mobile.components import campos
from mobile.api_client import ErroApi
from mobile.components.avatar import avatar
from mobile.components.comuns import cabecalho

if TYPE_CHECKING:  # pragma: no cover
    from mobile.main import App

LADO_DO_AVATAR = 96


def construir(app: App) -> ft.Control:
    """Formulário de edição do perfil."""
    usuario: dict[str, Any] = app.state.usuario or {}
    # O perfil da sessão é o schema público (sem telefone e sem CPF); os dados
    # do titular vêm de `/auth/me`, que só o dono recebe.
    privado: dict[str, Any] = app.executar(lambda: app.api.eu()) or {}

    campo_nome = campos.campo_texto("Seu nome completo", icone=t.ICONES["nome"])
    campo_nome.value = usuario.get("nome") or ""

    campo_email = campos.campo_texto(
        "seu@email.com",
        icone=t.ICONES["email"],
        tipo_teclado=ft.KeyboardType.EMAIL,
    )
    campo_email.value = usuario.get("email") or ""
    # Limpa o erro assim que a pessoa mexe: manter "já está em uso" embaixo de
    # um endereço que ela acabou de corrigir é a tela mentindo.
    campo_email.on_change = lambda _: _limpar_erro(app, campo_email)

    campo_telefone = campos.campo_texto(
        "(00) 00000-0000",
        icone=t.ICONES["telefone"],
        tipo_teclado=ft.KeyboardType.PHONE,
        maximo=15,
    )
    campo_telefone.value = mascaras.telefone(privado.get("telefone") or "")
    campo_telefone.on_change = lambda _: _formatar(app, campo_telefone)

    seletor_cidade = campos.campo_dropdown(
        [],
        dica="Escolha o estado primeiro",
        icone=t.ICONES["cidade"],
        desabilitado=True,
        filtravel=True,
    )
    coordenadas: dict[str, tuple[float, float]] = {}

    def preencher_cidades(sigla: str | None, manter: str | None = None) -> None:
        """Carrega os municípios da UF e, se possível, mantém a cidade atual."""
        coordenadas.clear()
        cidades = app.executar(lambda: app.api.listar_cidades(sigla)) if sigla else None

        if cidades is None:
            seletor_cidade.options = []
            seletor_cidade.disabled = True
            seletor_cidade.hint_text = "Escolha o estado primeiro"
            return

        coordenadas.update({c["nome"]: (c["lat"], c["lng"]) for c in cidades})
        seletor_cidade.options = [
            ft.DropdownOption(key=c["nome"], text=c["nome"]) for c in cidades
        ]
        seletor_cidade.disabled = False
        seletor_cidade.hint_text = "Digite para buscar"
        seletor_cidade.value = manter if manter in coordenadas else None

    def trocar_estado(_: ft.ControlEvent) -> None:
        """Ao trocar a UF, a cidade recomeça: ela pertence ao estado."""
        preencher_cidades(seletor_estado.value)
        app.page.update()

    estados = app.api.listar_estados()
    seletor_estado = campos.campo_dropdown(
        [ft.DropdownOption(key=e["sigla"], text=e["nome"]) for e in estados],
        valor=usuario.get("estado"),
        dica="Selecione seu estado",
        icone=t.ICONES["estado"],
        filtravel=True,
        ao_selecionar=trocar_estado,
    )
    if usuario.get("estado"):
        preencher_cidades(usuario["estado"], usuario.get("cidade"))

    # --------------------------------------------------------------------- #
    # Foto
    # --------------------------------------------------------------------- #
    async def trocar_foto(_: ft.ControlEvent) -> None:
        """Escolhe uma imagem e a grava como avatar (mesmo fluxo do Perfil)."""
        seletor = ft.FilePicker()
        escolhidos = await seletor.pick_files(
            dialog_title="Escolha sua foto de perfil",
            file_type=ft.FilePickerFileType.IMAGE,
            allow_multiple=False,
        )
        if not escolhidos:
            return

        origem = escolhidos[0].path
        if not origem:
            app.aviso("Trocar a foto só funciona no aplicativo instalado.", erro=True)
            return

        try:
            caminho = avatares.salvar(int(usuario.get("id", 0)), origem)
        except (ValueError, OSError) as erro:
            app.aviso(str(erro) or "Não foi possível salvar a imagem.", erro=True)
            return

        atualizado = app.executar(lambda: app.api.atualizar_perfil({"avatar_url": caminho}))
        if atualizado is None:
            return

        app.state.atualizar_usuario(atualizado)
        app.aviso("Foto de perfil atualizada.")
        app.renderizar()

    foto = ft.Stack(
        [
            avatar(usuario, LADO_DO_AVATAR),
            ft.Container(
                content=ft.Icon(ft.Icons.PHOTO_CAMERA_ROUNDED, size=16, color=t.BRANCO),
                width=34,
                height=34,
                bgcolor=t.VERDE_PRIMARIO,
                border_radius=17,
                alignment=ft.Alignment.CENTER,
                border=ft.Border.all(2.5, t.BRANCO),
                on_click=trocar_foto,
                ink=True,
                tooltip="Trocar foto",
                right=0,
                bottom=0,
            ),
        ],
        width=LADO_DO_AVATAR,
        height=LADO_DO_AVATAR,
    )

    # --------------------------------------------------------------------- #
    # Salvar
    # --------------------------------------------------------------------- #
    def salvar(_: ft.ControlEvent) -> None:
        """Valida e envia só o que mudou."""
        nome = (campo_nome.value or "").strip()
        email = (campo_email.value or "").strip().lower()
        telefone = mascaras.somente_digitos(campo_telefone.value)

        campo_nome.error = None if len(nome) >= 2 else "Informe seu nome completo."
        # Mesma checagem do cadastro. O juiz do formato é o `EmailStr` da API;
        # aqui só evitamos a ida ao servidor no erro óbvio.
        campo_email.error = None if "@" in email else "Informe um e-mail válido."
        campo_telefone.error = (
            None if len(telefone) in (10, 11) else "Informe DDD + número."
        )
        app.page.update()
        if campo_nome.error or campo_email.error or campo_telefone.error:
            return

        if not seletor_estado.value or not seletor_cidade.value:
            app.aviso("Escolha o estado e a cidade.", erro=True)
            return

        # Patch parcial: mandar só o que mudou evita revalidar a região (e
        # remover o ponto do mapa) quando a pessoa só corrigiu o nome.
        mudancas: dict[str, Any] = {}
        if nome != (usuario.get("nome") or ""):
            mudancas["nome"] = nome
        if email != (usuario.get("email") or "").lower():
            mudancas["email"] = email
        if telefone != (privado.get("telefone") or ""):
            mudancas["telefone"] = telefone
        if (
            seletor_estado.value != usuario.get("estado")
            or seletor_cidade.value != usuario.get("cidade")
        ):
            latitude, longitude = coordenadas.get(seletor_cidade.value, (0.0, 0.0))
            mudancas.update(
                estado=seletor_estado.value,
                cidade=seletor_cidade.value,
                latitude=latitude,
                longitude=longitude,
            )

        if not mudancas:
            app.aviso("Nada mudou por aqui.")
            return

        # Sem `app.executar` aqui: o erro de e-mail precisa marcar o campo, e
        # não sumir num aviso de rodapé que some em três segundos.
        try:
            atualizado = app.api.atualizar_perfil(mudancas)
        except ErroApi as erro:
            if "email" in mudancas and erro.status in (409, 422):
                campo_email.error = erro.mensagem
                app.page.update()
            else:
                app.aviso(erro.mensagem, erro=True)
            return

        app.state.atualizar_usuario(atualizado)
        app.aviso("Perfil atualizado com sucesso.")
        app.voltar()

    def _cpf_exibido() -> str:
        """O CPF já chega mascarado da API; sem ele, um traço."""
        return privado.get("cpf") or "—"

    corpo = ft.Container(
        content=ft.Column(
            [
                ft.Row([foto], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=4),
                campos.com_rotulo("Nome completo", campo_nome),
                campos.com_rotulo("E-mail", campo_email),
                campos.com_rotulo("Telefone / WhatsApp", campo_telefone),
                campos.com_rotulo("Estado", seletor_estado),
                campos.com_rotulo("Cidade", seletor_cidade),
                t.subtitulo("Sua região define quais pedidos aparecem perto de você."),
                ft.Container(height=6),
                campos.com_rotulo(
                    "CPF",
                    campos.campo_travado(_cpf_exibido(), t.ICONES["cpf"]),
                    apoio="Guardamos só os dígitos e nunca mostramos o número inteiro.",
                ),
                ft.Container(height=8),
                t.botao_primario("Salvar alterações", salvar, t.ICONES["concluido"], 400),
                ft.Container(height=20),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=16),
        expand=True,
        bgcolor=t.FUNDO_CLARO,
    )

    return ft.Column(
        [cabecalho("Editar perfil", ao_voltar=app.voltar), corpo],
        spacing=0,
        expand=True,
    )


def _limpar_erro(app: App, campo: ft.TextField) -> None:
    """Apaga a mensagem de erro do campo assim que ele é editado."""
    if campo.error:
        campo.error = None
        app.page.update()


def _formatar(app: App, campo: ft.TextField) -> None:
    """Aplica a máscara de telefone enquanto se digita."""
    campo.value = mascaras.telefone(campo.value)
    campo.error = None
    app.page.update()
