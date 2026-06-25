"""
Resolução de caminhos para desenvolvimento e executável (PyInstaller).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def get_app_dir() -> Path:
    """Diretório ao lado do .exe (gravável) ou pasta backend/ em dev."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_bundle_dir() -> Path:
    """Recursos empacotados dentro do executável."""
    if is_frozen():
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def get_commands_path() -> str:
    """
    Retorna o caminho de commands.json.
    No .exe, prioriza commands/commands.json ao lado do Jarvis.exe
    (editável pelo usuário) e copia o padrão na primeira execução.
    """
    if is_frozen():
        user_commands = get_app_dir() / "commands" / "commands.json"
        bundled_commands = get_bundle_dir() / "commands" / "commands.json"

        if not user_commands.exists() and bundled_commands.exists():
            user_commands.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(bundled_commands, user_commands)

        return str(user_commands)

    return str(get_bundle_dir() / "commands" / "commands.json")


def get_settings_path() -> Path:
    """Preferências do usuário (nome do assistente, wake word)."""
    return get_app_dir() / "user_settings.json"


def get_frontend_dir() -> Path | None:
    """Pasta com o build estático do React (dist/ ou frontend/ no bundle)."""
    if is_frozen():
        candidate = get_bundle_dir() / "frontend"
    else:
        candidate = Path(__file__).resolve().parent.parent / "dist"

    return candidate if candidate.is_dir() else None
