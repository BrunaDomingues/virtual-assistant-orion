#!/usr/bin/env python3
"""
OrionWebSocketServer
====================
Servidor WebSocket que expõe os eventos do loop de voz para o frontend React.

Porta padrão: ws://localhost:8765

Mensagens emitidas (JSON):
  {"type": "state",      "state": "idle"|"standby"|"listening"|"speaking"}
  {"type": "recognized", "text": "<texto reconhecido>"}
  {"type": "command",    "label": "<texto>", "success": true|false}
  {"type": "error",      "message": "<mensagem>"}

Mensagens recebidas do frontend:
  {"type": "ping"}             -> keep-alive
  {"type": "start_listening"}  -> reativa escuta por voz
  {"type": "stop_listening"}   -> silencia o microfone (idle)
"""

import asyncio
import json
import os
import signal
import sys
import threading
import time
from typing import Set
from concurrent.futures import TimeoutError as FutureTimeoutError

import websockets
from websockets.asyncio.server import ServerConnection

# Adiciona o diretório atual ao path para importações relativas
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.voice_listener import VoiceListener
from core.speaker import OrionSpeaker
from config import (
    SPEAK_ON_ERROR,
    SPEAK_ON_SUCCESS,
    SPEAK_WAKE_GREETING,
    USE_WAKE_WORD,
)
from paths import get_commands_path, get_settings_path
from utils.command_executor import CommandExecutor
from utils.user_settings import UserSettings, setup_confirmation_for, wake_greeting_for

HOST = "localhost"
PORT = 8765


class OrionWebSocketServer:
    """
    Servidor WebSocket + loop de voz em thread separada.

    A thread de voz é bloqueante (speech_recognition). Ela se comunica com
    o event-loop asyncio via asyncio.Queue + loop.call_soon_threadsafe para
    não bloquear as corrotinas do servidor.
    """

    def __init__(self, host: str = HOST, port: int = PORT):
        self.host = host
        self.port = port
        self._clients: Set[ServerConnection] = set()
        self._clients_lock = threading.Lock()
        self._queue: asyncio.Queue = None        # criada em start()
        self._loop: asyncio.AbstractEventLoop = None
        self._running = False
        self._voice_thread: threading.Thread = None
        self._voice_enabled = threading.Event()
        self._voice_enabled.set()
        self._state_lock = threading.Lock()
        self._current_state = "idle"
        self.listener: VoiceListener = None
        self.speaker = OrionSpeaker()
        self.executor: CommandExecutor = None
        self.settings = UserSettings.load()

    def _apply_user_settings(self) -> None:
        if self.listener:
            self.listener.apply_assistant_name(self.settings.assistant_name)

    def _emit_config(self) -> None:
        self._emit(
            "config",
            assistant_name=self.settings.display_name(),
            wake_word=self.settings.wake_word,
            configured=self.settings.configured,
        )

    def _wake_greeting(self) -> str:
        return wake_greeting_for(self.settings.assistant_name)

    def _run_name_setup(self) -> None:
        from config import (
            ASK_ASSISTANT_NAME_ON_FIRST_RUN,
            SETUP_LISTEN_TIMEOUT,
            SETUP_MAX_ROUNDS,
            SETUP_PHRASE_TIME_LIMIT,
            SETUP_PROMPT,
        )

        if not ASK_ASSISTANT_NAME_ON_FIRST_RUN or self.settings.configured:
            self._apply_user_settings()
            self._emit_config()
            return

        print("\nPrimeira execução — configurando nome do assistente...")
        self._set_state("listening")
        self._speak_feedback(SETUP_PROMPT)

        saved = False
        for round_idx in range(SETUP_MAX_ROUNDS):
            spoken = self.listener.listen_for_assistant_name(
                max_attempts=3,
                wait_timeout=SETUP_LISTEN_TIMEOUT,
                phrase_time_limit=SETUP_PHRASE_TIME_LIMIT,
            )
            if spoken:
                settings = UserSettings.save_name(spoken)
                if settings:
                    self.settings = settings
                    saved = True
                    break

            if round_idx < SETUP_MAX_ROUNDS - 1:
                self._speak_feedback("Desculpe, não entendi. Como você quer me chamar?")

        if not saved:
            print("Nome não configurado — será perguntado novamente na próxima execução.")
            self._apply_user_settings()
            self._emit_config()
            return

        self._apply_user_settings()
        self._emit_config()
        self._speak_feedback(setup_confirmation_for(self.settings.assistant_name))
        print(f"Assistente configurado como: {self.settings.display_name()}")
        print(f'Wake word: "{self.settings.wake_word}"')
        print(f"Salvo em: {get_settings_path()}")

    # ── Event emission (thread-safe) ──────────────────────────────────────────

    def _emit(self, type_: str, **kwargs) -> None:
        """Enfileira uma mensagem JSON para broadcast. Pode ser chamado de qualquer thread."""
        if self._loop is None or self._queue is None:
            return
        msg = json.dumps({"type": type_, **kwargs})
        self._loop.call_soon_threadsafe(self._queue.put_nowait, msg)

    def _set_state(self, state: str) -> None:
        """Atualiza estado interno e emite evento somente quando houver mudança."""
        with self._state_lock:
            if self._current_state == state:
                return
            self._current_state = state
        self._emit("state", state=state)

    def _post_speech_state(self) -> str:
        if not self._voice_enabled.is_set():
            return "idle"
        return "standby" if USE_WAKE_WORD else "listening"

    async def _speak_with_state(self, text: str) -> None:
        """
        Emite estado speaking durante TTS e restaura para listening/idle ao final.
        """
        if not text or not text.strip():
            return
        self._set_state("speaking")
        try:
            await self.speaker.speak(text)
        finally:
            self._set_state(self._post_speech_state())

    def _speak_feedback(self, text: str) -> None:
        """
        Dispara TTS no loop asyncio do servidor sem bloquear as corrotinas WS.
        Chamado da thread de voz.
        """
        if not text or not text.strip():
            return
        if self._loop is None:
            return
        try:
            future = asyncio.run_coroutine_threadsafe(self._speak_with_state(text), self._loop)
            future.result()
        except FutureTimeoutError:
            self._emit("error", message="Timeout ao reproduzir audio de resposta")
        except Exception as exc:
            self._emit("error", message=f"Erro no TTS: {exc}")

    # ── Voice loop (runs in background thread) ────────────────────────────────

    def _initialize_components(self) -> bool:
        """Inicializa VoiceListener e CommandExecutor. Roda na thread de voz."""
        try:
            print("=" * 60)
            print(f"       ASSISTENTE {self.settings.display_name().upper()} - SERVIDOR WebSocket")
            print(f"       ws://{self.host}:{self.port}")
            print("=" * 60)

            commands_path = get_commands_path()
            if not os.path.exists(commands_path):
                self._emit("error", message=f"Arquivo de comandos não encontrado: {commands_path}")
                return False

            print("Inicializando executor de comandos...")
            self.executor = CommandExecutor(commands_file=commands_path)
            if not self.executor.commands:
                self._emit("error", message="Nenhum comando carregado")
                return False
            self.executor.list_available_commands()

            print("\nInicializando listener de voz...")
            self.listener = VoiceListener()
            self._run_name_setup()

            print("✅ Componentes inicializados com sucesso!")
            if USE_WAKE_WORD:
                print(f'Diga "{self.settings.wake_word}" para ativar — escuta automática ligada.')
            print(f"\nFrontend pode conectar em ws://{self.host}:{self.port}")
            print("=" * 60)
            return True

        except Exception as exc:
            self._emit("error", message=f"Erro na inicialização: {exc}")
            print(f"ERRO na inicialização: {exc}")
            return False

    def _voice_loop(self) -> None:
        """Loop principal de voz — bloqueante, roda em thread dedicada."""
        if not _check_dependencies():
            self._emit("error", message="Dependências ausentes (speech_recognition, sounddevice)")
            return

        if not self._initialize_components():
            return

        self._set_state("standby" if USE_WAKE_WORD and self._voice_enabled.is_set() else "idle")

        while self._running:
            try:
                if not self._voice_enabled.is_set():
                    self._set_state("idle")
                    if not self._voice_enabled.wait(timeout=0.2):
                        continue
                    if not self._running:
                        break

                should_listen = lambda: self._voice_enabled.is_set() and self._running

                if USE_WAKE_WORD:
                    self._set_state("standby")
                    detected, inline_command = self.listener.wait_for_wake_word(should_listen)
                    if not detected or not self._running:
                        continue

                    if inline_command:
                        command_text = inline_command
                    else:
                        if SPEAK_WAKE_GREETING:
                            self._speak_feedback(self._wake_greeting())
                        self._set_state("listening")
                        command_text = self.listener.listen_for_command()
                else:
                    self._set_state("listening")
                    command_text = self.listener.listen_for_command(max_attempts=1)

                if command_text:
                    self._emit("recognized", text=command_text)

                    success = self.executor.process_voice_command(command_text)
                    self._emit("command", label=command_text, success=success)

                    if success and SPEAK_ON_SUCCESS:
                        self._speak_feedback(f"Comando {command_text} executado com sucesso.")
                    elif not success and SPEAK_ON_ERROR:
                        self._speak_feedback(f"Nao consegui executar o comando {command_text}.")

                if self._voice_enabled.is_set():
                    self._set_state("standby" if USE_WAKE_WORD else "listening")
                else:
                    self._set_state("idle")

            except Exception as exc:
                print(f"Erro no loop de voz: {exc}")
                self._emit("error", message=str(exc))
                self._set_state("idle")
                time.sleep(1)

    # ── WebSocket handlers ────────────────────────────────────────────────────

    async def _handler(self, websocket: ServerConnection) -> None:
        """Gerencia um cliente WebSocket conectado."""
        with self._clients_lock:
            self._clients.add(websocket)
        client_addr = websocket.remote_address
        print(f"[WS] Cliente conectado: {client_addr}  (total: {len(self._clients)})")

        # Envia estado atual ao conectar
        try:
            with self._state_lock:
                state = self._current_state
            await websocket.send(json.dumps({"type": "state", "state": state}))
            await websocket.send(json.dumps({
                "type": "config",
                "assistant_name": self.settings.display_name(),
                "wake_word": self.settings.wake_word,
                "configured": self.settings.configured,
            }))
        except Exception:
            pass

        try:
            async for raw in websocket:
                try:
                    msg = json.loads(raw)
                    msg_type = msg.get("type")
                    if msg_type == "ping":
                        await websocket.send(json.dumps({"type": "pong"}))
                    elif msg_type == "start_listening":
                        self._voice_enabled.set()
                        self._set_state("standby" if USE_WAKE_WORD else "listening")
                    elif msg_type == "stop_listening":
                        self._voice_enabled.clear()
                        self._set_state("idle")
                except (json.JSONDecodeError, KeyError):
                    pass
        except websockets.exceptions.ConnectionClosedOK:
            pass
        except websockets.exceptions.ConnectionClosedError:
            pass
        finally:
            with self._clients_lock:
                self._clients.discard(websocket)
            print(f"[WS] Cliente desconectado: {client_addr}  (total: {len(self._clients)})")

    # ── Broadcast loop ────────────────────────────────────────────────────────

    async def _broadcast_loop(self) -> None:
        """Consome a fila de eventos e os envia a todos os clientes conectados."""
        while self._running:
            try:
                msg = await asyncio.wait_for(self._queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue

            with self._clients_lock:
                clients = list(self._clients)

            if not clients:
                continue

            results = await asyncio.gather(
                *[c.send(msg) for c in clients],
                return_exceptions=True,
            )
            for client, result in zip(clients, results):
                if isinstance(result, Exception):
                    with self._clients_lock:
                        self._clients.discard(client)

    # ── Entry point ───────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Inicia o servidor WebSocket e a thread de voz."""
        self._loop  = asyncio.get_running_loop()
        self._queue = asyncio.Queue()
        self._running = True

        # Inicia thread de voz em background
        self._voice_thread = threading.Thread(target=self._voice_loop, daemon=True, name="voice-loop")
        self._voice_thread.start()

        # Trata Ctrl+C graciosamente (só na thread principal — no modo pet o WS roda em background)
        if threading.current_thread() is threading.main_thread():
            loop = self._loop
            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    loop.add_signal_handler(sig, self._shutdown)
                except NotImplementedError:
                    try:
                        signal.signal(sig, lambda _s, _f: self._shutdown())
                    except ValueError:
                        pass

        print(f"[WS] Servidor iniciado em ws://{self.host}:{self.port}")

        async with websockets.serve(self._handler, self.host, self.port):
            await self._broadcast_loop()

    def _shutdown(self) -> None:
        print("\n[WS] Encerrando servidor...")
        self._running = False
        self._voice_enabled.clear()


# ── Dependency check ──────────────────────────────────────────────────────────

def _check_dependencies() -> bool:
    try:
        import speech_recognition  # noqa: F401
        import sounddevice         # noqa: F401
        return True
    except ImportError as exc:
        print(f"ERRO: Dependência ausente — {exc}")
        print("Execute: pip install -r requirements.txt")
        return False


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not _check_dependencies():
        sys.exit(1)
    try:
        asyncio.run(OrionWebSocketServer().start())
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
