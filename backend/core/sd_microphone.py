"""
Fonte de áudio compatível com speech_recognition.Recognizer sem PyAudio.
Usa sounddevice (PortAudio via wheels), adequado para Windows e Python 3.13+.
"""

from __future__ import annotations

import numpy as np
import sounddevice as sd
import speech_recognition as sr


class _RawStreamAdapter:
    """Expõe read(frames) -> bytes como o MicrophoneStream do PyAudio."""

    def __init__(self, raw: sd.RawInputStream) -> None:
        self._raw = raw

    def read(self, num_frames: int) -> bytes:
        data, _overflow = self._raw.read(num_frames)
        if data is None:
            return b""
        if isinstance(data, np.ndarray):
            if data.size == 0:
                return b""
            if data.ndim > 1:
                data = data[:, 0]
            return np.ascontiguousarray(data, dtype=np.int16).tobytes()
        # sounddevice pode devolver buffer CFFI / memoryview em vez de ndarray
        try:
            raw = bytes(memoryview(data))
        except TypeError:
            raw = bytes(data)
        return raw if raw else b""

    def close(self) -> None:
        pass


class SoundDeviceMicrophone(sr.AudioSource):
    """
    Substitui sr.Microphone: mesmos atributos usados por adjust_for_ambient_noise e listen.
    """

    def __init__(
        self,
        device: int | None = None,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
    ) -> None:
        self.device = device
        self.SAMPLE_RATE = int(sample_rate)
        self.CHUNK = int(chunk_size)
        self.SAMPLE_WIDTH = 2  # int16, igual ao paInt16 do PyAudio
        self._raw: sd.RawInputStream | None = None
        self.stream: _RawStreamAdapter | None = None

    def __enter__(self) -> SoundDeviceMicrophone:
        assert self.stream is None, "This audio source is already inside a context manager"
        self._raw = sd.RawInputStream(
            samplerate=self.SAMPLE_RATE,
            device=self.device,
            channels=1,
            dtype="int16",
            blocksize=self.CHUNK,
        )
        self._raw.start()
        self.stream = _RawStreamAdapter(self._raw)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        try:
            if self.stream is not None:
                self.stream.close()
        finally:
            self.stream = None
        if self._raw is not None:
            self._raw.stop()
            self._raw.close()
            self._raw = None
