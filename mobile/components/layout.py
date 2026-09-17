"""
Coluna central: o app é mobile-first, e a janela do desktop não é.

Todas as telas foram desenhadas para ~390px de largura. Numa janela larga o
conteúdo esticava — cartões com metros de espaço vazio, textos atravessando o
monitor, e a barra de navegação com os cinco destinos jogados nas bordas.

A correção é uma só, aplicada no ponto onde a árvore do app é montada
(`mobile/main.py`): o app inteiro — conteúdo, FAB e barra inferior — passa a
viver dentro de uma coluna de largura máxima, centralizada, com o fundo da
página aparecendo nas laterais.

O Flet não tem `max-width`: `width` é fixo e, num celular de 360px, um
`width=440` cortaria a tela. Então a largura é **decidida em tempo de execução**
(`ajustar`) e reavaliada no `page.on_resize`: acima do limite a coluna é fixa e
centralizada; abaixo dele ela volta a ser `expand=True` e ocupa tudo, que é o
comportamento de celular.
"""

from typing import Optional

import flet as ft

from mobile import theme as t

# Largura da coluna no desktop. Um pouco acima dos 390px de referência do
# desenho: sobra a folga que os cartões já esperavam, sem virar tablet.
LARGURA_MAXIMA = 440


class ColunaCentral:
    """Envolve a árvore do app numa coluna de largura máxima centralizada.

    Uso:

        coluna = ColunaCentral(arvore_do_app)
        coluna.ajustar(page.width)
        page.add(coluna.raiz)
        page.on_resize = lambda e: coluna.ajustar(e.width) and page.update()
    """

    def __init__(self, conteudo: ft.Control, largura_maxima: int = LARGURA_MAXIMA) -> None:
        self.largura_maxima = largura_maxima
        # `limitada` guarda o estado atual para que `ajustar` só devolva True
        # quando algo realmente mudou — sem isso, cada pixel de arrasto da
        # janela dispararia um `page.update()`.
        self.limitada: Optional[bool] = None

        self.coluna = ft.Container(
            content=conteudo,
            bgcolor=t.FUNDO_CLARO,
            expand=True,
        )
        # STRETCH é o que faz a coluna ocupar a altura inteira: o padrão do Row
        # é CENTER, que a deixaria com a altura do conteúdo, flutuando no meio.
        self.raiz = ft.Row(
            [self.coluna],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            spacing=0,
            expand=True,
        )

    def ajustar(self, largura_da_pagina: Optional[float]) -> bool:
        """Liga ou desliga o limite conforme a largura disponível.

        Args:
            largura_da_pagina: largura da página em pixels lógicos. `None`
                (primeira renderização, testes) é tratado como tela estreita —
                o padrão seguro, porque ocupar tudo nunca corta nada.

        Returns:
            `True` quando o layout mudou e a página precisa ser atualizada.
        """
        limitar = largura_da_pagina is not None and largura_da_pagina > self.largura_maxima
        if limitar == self.limitada:
            return False

        if limitar:
            # A ordem importa: com `expand` ligado o Row ignora o `width`.
            self.coluna.expand = False
            self.coluna.width = self.largura_maxima
            # Fio nas laterais para a coluna se ler como o app, e não como um
            # bloco de conteúdo solto no meio da janela.
            # `horizontal` no Flet é o par esquerda/direita (`vertical` seria
            # topo/base, que não é o que queremos aqui).
            self.coluna.border = ft.Border.symmetric(
                horizontal=ft.BorderSide(1, t.BORDA)
            )
        else:
            self.coluna.width = None
            self.coluna.expand = True
            self.coluna.border = None

        self.limitada = limitar
        return True
