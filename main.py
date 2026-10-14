"""Entrypoint Flet do pacote Android, executado a partir da raiz do projeto."""

import flet as ft

from mobile.main import ASSETS_DIR, main


# `tool.flet.app.module = "main"` executa este módulo no Android. O desktop
# executava `mobile/main.py` diretamente; por isso, o `ft.run()` precisa estar
# também neste entrypoint efetivamente empacotado.
ft.run(main, assets_dir=str(ASSETS_DIR))
