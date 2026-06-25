"""
Nome do assistente escolhido pelo usuário e wake word dinâmica.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict
from typing import List

from config import DEFAULT_ASSISTANT_NAME
from paths import get_settings_path


def build_wake_variations(assistant_name: str) -> List[str]:
    name = assistant_name.lower().strip()
    if not name:
        name = DEFAULT_ASSISTANT_NAME

    variations = [
        f"oi {name}",
        f"olá {name}",
        f"ola {name}",
        f"hey {name}",
        f"ei {name}",
        f"oi, {name}",
        f"oi {name},",
    ]

    if name == "jarvis":
        variations.extend([
            "oi jervis",
            "oi jar viz",
            "oi jarvís",
        ])

    return list(dict.fromkeys(variations))


def normalize_assistant_name(spoken: str) -> str:
    """Extrai o nome falado, removendo frases comuns."""
    if not spoken:
        return ""

    text = spoken.lower().strip()
    prefixes = (
        "me chame de ",
        "pode me chamar de ",
        "quero te chamar de ",
        "seu nome é ",
        "seu nome e ",
        "nome ",
        "de ",
    )
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()

    text = re.sub(r"[^\w\sáàâãéêíóôõúüç-]", " ", text, flags=re.I)
    text = " ".join(text.split())
    if not text:
        return ""

    # Usa a frase inteira se for curta; senão, a primeira palavra significativa
    words = text.split()
    if len(words) == 1:
        return words[0]
    if len(text) <= 24:
        return text
    return words[0]


def wake_greeting_for(name: str) -> str:
    display = name.strip().title() or "Jarvis"
    return f"Oi! {display} ouvindo."


def setup_confirmation_for(name: str) -> str:
    display = name.strip().title() or "Jarvis"
    return (
        f"Perfeito! Me chame de {display}. "
        f"Para me ativar, diga: oi {name.lower()}."
    )


@dataclass
class UserSettings:
    assistant_name: str = DEFAULT_ASSISTANT_NAME
    wake_word: str = f"oi {DEFAULT_ASSISTANT_NAME}"
    configured: bool = False

    @classmethod
    def load(cls) -> "UserSettings":
        path = get_settings_path()
        if not path.exists():
            return cls()

        try:
            with open(path, encoding="utf-8") as file:
                data = json.load(file)
            name = normalize_assistant_name(data.get("assistant_name", "")) or DEFAULT_ASSISTANT_NAME
            wake = data.get("wake_word") or f"oi {name}"
            return cls(
                assistant_name=name,
                wake_word=wake.lower().strip(),
                configured=bool(data.get("configured", False)),
            )
        except (json.JSONDecodeError, OSError):
            return cls()

    @classmethod
    def save_name(cls, spoken_name: str) -> "UserSettings | None":
        name = normalize_assistant_name(spoken_name)
        if not name:
            return None

        settings = cls(
            assistant_name=name,
            wake_word=f"oi {name}",
            configured=True,
        )
        settings.persist()
        return settings

    def persist(self) -> None:
        path = get_settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(asdict(self), file, ensure_ascii=False, indent=2)
            file.flush()
            os.fsync(file.fileno())

    def display_name(self) -> str:
        return self.assistant_name.strip().title() or "Jarvis"

    def wake_variations(self) -> List[str]:
        return build_wake_variations(self.assistant_name)
