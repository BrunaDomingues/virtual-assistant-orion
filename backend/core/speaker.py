import asyncio
import os
import tempfile
import time

import edge_tts
import pygame


class OrionSpeaker:
    """Sintetiza e reproduz fala em PT-BR de forma assincrona."""

    def __init__(self, voice: str = "pt-BR-AntonioNeural"):
        self.voice = voice
        self._mixer_ready = False
        self._mixer_lock = asyncio.Lock()

    async def _ensure_mixer(self) -> None:
        async with self._mixer_lock:
            if self._mixer_ready:
                return
            await asyncio.to_thread(pygame.mixer.init)
            self._mixer_ready = True

    @staticmethod
    def _play_audio_blocking(audio_path: str) -> None:
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
        pygame.mixer.music.unload()

    async def speak(self, text: str) -> None:
        """
        Converte texto em audio com edge-tts e reproduz com pygame sem
        bloquear o event-loop principal.
        """
        if not text or not text.strip():
            return

        await self._ensure_mixer()

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                temp_path = tmp.name

            communicate = edge_tts.Communicate(text=text.strip(), voice=self.voice)
            await communicate.save(temp_path)
            await asyncio.to_thread(self._play_audio_blocking, temp_path)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
