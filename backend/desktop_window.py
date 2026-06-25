"""
Janela desktop flutuante do assistente (sem abrir o navegador).
"""

from __future__ import annotations

import time

from config import (
    DESKTOP_PET_MODE,
    PET_WINDOW_HEIGHT,
    PET_WINDOW_TITLE,
    PET_WINDOW_WIDTH,
)
from static_server import FRONTEND_URL, start_static_server


def pet_url() -> str:
    return f"{FRONTEND_URL}?mode=pet"


def run_desktop_pet() -> None:
    try:
        import webview
    except ImportError as exc:
        raise RuntimeError(
            "pywebview não instalado. Execute: pip install pywebview"
        ) from exc

    print(f"[UI] Abrindo assistente na área de trabalho ({PET_WINDOW_WIDTH}x{PET_WINDOW_HEIGHT})")

    window = webview.create_window(
        title=PET_WINDOW_TITLE,
        url=pet_url(),
        width=PET_WINDOW_WIDTH,
        height=PET_WINDOW_HEIGHT,
        frameless=True,
        easy_drag=True,
        on_top=True,
        resizable=True,
        min_size=(280, 340),
        background_color="#050505",
        transparent=False,
    )

    try:
        webview.start(gui="edgechromium")
    except Exception:
        webview.start()


def start_ui(frontend_dir: str, use_browser: bool = False) -> None:
    """Inicia servidor estático e abre UI como pet ou navegador."""
    start_static_server(frontend_dir)

    if use_browser or not DESKTOP_PET_MODE:
        from static_server import open_browser

        open_browser(FRONTEND_URL if not DESKTOP_PET_MODE else pet_url())
        print(f"[UI] Interface no navegador: {pet_url() if DESKTOP_PET_MODE else FRONTEND_URL}")
        return

    time.sleep(0.8)
    run_desktop_pet()
