import re
import speech_recognition as sr
from typing import Callable, Optional, List, Tuple

from config import (
    COMMAND_PHRASE_TIME_LIMIT,
    COMMAND_TIMEOUT,
    DEFAULT_ASSISTANT_NAME,
    LISTENING_TIMEOUT,
    MAX_COMMAND_ATTEMPTS,
    NON_SPEAKING_DURATION,
    PAUSE_THRESHOLD,
    PHRASE_TIMEOUT,
    WAKE_PHRASE_TIME_LIMIT,
)
from core.sd_microphone import SoundDeviceMicrophone
from utils.user_settings import build_wake_variations


class VoiceListener:
    """
    Escuta contínua com detecção da wake word antes do comando.
    Aguarda silêncio (fim de fala) antes de processar cada frase.
    """

    def __init__(
        self,
        wake_word: str | None = None,
        wake_word_variations: Optional[List[str]] = None,
        timeout: int = LISTENING_TIMEOUT,
        command_timeout: int = COMMAND_TIMEOUT,
        phrase_timeout: float = PHRASE_TIMEOUT,
        max_command_attempts: int = MAX_COMMAND_ATTEMPTS,
    ):
        self.timeout = timeout
        self.command_timeout = command_timeout
        self.phrase_timeout = phrase_timeout
        self.max_command_attempts = max_command_attempts
        self.wake_word = ""
        self.wake_word_variations: List[str] = []

        if wake_word_variations is not None:
            self.wake_word_variations = [v.lower() for v in wake_word_variations]
            self.wake_word = (wake_word or self.wake_word_variations[0]).lower()
        elif wake_word:
            self.wake_word = wake_word.lower()
            self.wake_word_variations = build_wake_variations(
                wake_word.removeprefix("oi ").strip() or DEFAULT_ASSISTANT_NAME
            )
        else:
            self.apply_assistant_name(DEFAULT_ASSISTANT_NAME)

        self.recognizer = sr.Recognizer()
        self._configure_recognizer()
        self.microphone = SoundDeviceMicrophone()
        self._calibrate_microphone()

    def apply_assistant_name(self, assistant_name: str) -> None:
        name = assistant_name.lower().strip() or DEFAULT_ASSISTANT_NAME
        self.wake_word = f"oi {name}"
        self.wake_word_variations = build_wake_variations(name)

    def _configure_recognizer(self) -> None:
        """Ajusta sensibilidade ao silêncio — espera você terminar de falar."""
        self.recognizer.pause_threshold = PAUSE_THRESHOLD
        self.recognizer.non_speaking_duration = NON_SPEAKING_DURATION
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.operation_timeout = None

    def _calibrate_microphone(self) -> None:
        print("Calibrando microfone para ruído ambiente...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        print("Calibração concluída!")

    def _listen_phrase(
        self,
        wait_timeout: float,
        phrase_time_limit: float,
        label: str = "frase",
    ) -> Optional[str]:
        try:
            print(f"[DEBUG] Escutando {label} (aguardando fim da fala)...")
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=wait_timeout,
                    phrase_time_limit=phrase_time_limit,
                )

            text = self.recognizer.recognize_google(audio, language="pt-BR")
            text_lower = text.lower().strip()
            print(f"[DEBUG] Texto reconhecido: '{text}'")
            return text_lower

        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            print("[DEBUG] Áudio capturado mas não foi possível entender")
            return None
        except sr.RequestError as e:
            print(f"[ERRO] Serviço de reconhecimento: {e}")
            return None
        except Exception as e:
            print(f"[ERRO] Inesperado na escuta: {e}")
            return None

    def _find_wake_word_and_remainder(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        text = text.lower().strip()
        best_match: Optional[Tuple[int, int, str]] = None

        for variation in sorted(self.wake_word_variations, key=len, reverse=True):
            pattern = re.compile(
                rf"(^|\s){re.escape(variation)}(\s|$|[,.])",
                re.IGNORECASE,
            )
            match = pattern.search(text)
            if match and (best_match is None or match.start() < best_match[0]):
                best_match = (match.start(), match.end(), variation)

        if best_match is None:
            return None, None

        _, end, variation = best_match
        remainder = text[end:].strip(" ,.")
        return variation, remainder or None

    def strip_wake_word(self, text: str) -> str:
        _, remainder = self._find_wake_word_and_remainder(text.lower().strip())
        if remainder:
            return remainder
        cleaned = text.lower().strip()
        for variation in sorted(self.wake_word_variations, key=len, reverse=True):
            cleaned = re.sub(
                rf"(^|\s){re.escape(variation)}(\s|$|[,.])",
                " ",
                cleaned,
                count=1,
            ).strip()
        return " ".join(cleaned.split())

    def wait_for_wake_word(self, should_continue: Callable[[], bool]) -> Tuple[bool, Optional[str]]:
        """
        Aguarda a wake word. Retorna (detectou, comando_na_mesma_frase_ou_none).
        """
        print(f"\nAguardando wake word '{self.wake_word.upper()}'...")

        while should_continue():
            text = self._listen_phrase(
                wait_timeout=self.timeout,
                phrase_time_limit=WAKE_PHRASE_TIME_LIMIT,
                label="wake word",
            )
            if not text:
                continue

            variation, inline_command = self._find_wake_word_and_remainder(text)
            if variation:
                print(f"Wake word detectada ('{variation}')")
                if inline_command:
                    print(f"Comando na mesma frase: '{inline_command}'")
                return True, inline_command

            print(f"[DEBUG] Wake word não encontrada em: '{text}'")

        return False, None

    def listen_for_command(self, max_attempts: Optional[int] = None) -> Optional[str]:
        attempts = self.max_command_attempts if max_attempts is None else max_attempts
        print("Aguardando comando (fale e pause ao terminar)...")

        for attempt in range(attempts):
            text = self._listen_phrase(
                wait_timeout=self.command_timeout,
                phrase_time_limit=COMMAND_PHRASE_TIME_LIMIT,
                label=f"comando ({attempt + 1}/{attempts})",
            )
            if not text:
                print(f"[DEBUG] Timeout aguardando comando — tentativa {attempt + 1}/{attempts}")
                continue

            command = self.strip_wake_word(text)
            if not command:
                print("[DEBUG] Comando vazio após remover wake word")
                continue

            print(f"[DEBUG] Comando capturado: '{command}'")
            return command

        print("Não foi possível capturar um comando válido")
        return None

    def listen_for_assistant_name(
        self,
        max_attempts: int = 5,
        wait_timeout: float = 12,
        phrase_time_limit: float = 15,
    ) -> Optional[str]:
        """Captura o nome falado na configuração inicial (sem exigir wake word)."""
        print("Aguardando nome do assistente...")

        for attempt in range(max_attempts):
            text = self._listen_phrase(
                wait_timeout=wait_timeout,
                phrase_time_limit=phrase_time_limit,
                label=f"nome ({attempt + 1}/{max_attempts})",
            )
            if text:
                print(f"[DEBUG] Nome capturado: '{text}'")
                return text

            print(f"[DEBUG] Não ouvi o nome — tentativa {attempt + 1}/{max_attempts}")

        return None

    def capture_command(
        self,
        should_continue: Callable[[], bool],
        on_wake_detected: Optional[Callable[[bool], None]] = None,
    ) -> Optional[str]:
        """
        Fluxo completo: wake word → (callback opcional) → comando.
        on_wake_detected(reprecisa_escutar_comando) é chamado após detectar o 'oi'.
        """
        detected, inline_command = self.wait_for_wake_word(should_continue)
        if not detected:
            return None

        if on_wake_detected:
            on_wake_detected(inline_command is None)

        if inline_command:
            return inline_command

        return self.listen_for_command()
