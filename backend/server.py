#!/usr/bin/env python3
"""
OrionWebSocketServer
====================
Servidor WebSocket que expõe os eventos do loop de voz para o frontend React.

Porta padrão: ws://localhost:8765

Mensagens emitidas (JSON):
  {"type": "state",      "state": "idle"|"listening"|"speaking"}
  {"type": "recognized", "text": "<texto reconhecido>"}
  {"type": "command",    "label": "<texto>", "success": true|false}
  {"type": "error",      "message": "<mensagem>"}

Mensagens recebidas do frontend:
  {"type": "ping"}             -> keep-alive
  {"type": "start_listening"}  -> ativa escuta continua sem wake word
  {"type": "stop_listening"}   -> interrompe escuta e volta para idle
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
from utils.command_executor import CommandExecutor

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
        self._listening_enabled = threading.Event()
        self._state_lock = threading.Lock()
        self._current_state = "idle"
        self.listener: VoiceListener = None
        self.speaker = OrionSpeaker()
        self.executor: CommandExecutor = None

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
        return "listening" if self._listening_enabled.is_set() else "idle"

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
            print("       ASSISTENTE ORION - SERVIDOR WebSocket")
            print(f"       ws://{self.host}:{self.port}")
            print("=" * 60)

            commands_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "commands", "commands.json")
            if not os.path.exists(commands_path):
                self._emit("error", message="commands/commands.json não encontrado")
                return False

            print("Inicializando executor de comandos...")
            self.executor = CommandExecutor(commands_file=commands_path)
            if not self.executor.commands:
                self._emit("error", message="Nenhum comando carregado")
                return False
            self.executor.list_available_commands()

            print("\nInicializando listener de voz...")
            self.listener = VoiceListener()

            print("✅ Componentes inicializados com sucesso!")
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

        self._set_state("idle")

        while self._running:
            try:
                # Aguarda ativação manual de escuta sem bloquear o shutdown.
                if not self._listening_enabled.wait(timeout=0.2):
                    continue
                if not self._running:
                    break

                self._set_state("listening")

                # Escuta comando diretamente (sem wake word).
                command_text = self.listener.listen_for_command(max_attempts=1)

                if command_text:
                    self._emit("recognized", text=command_text)

                    # Executa o comando reconhecido.
                    success = self.executor.process_voice_command(command_text)
                    self._emit("command", label=command_text, success=success)
                    feedback = (
                        f"Comando {command_text} executado com sucesso."
                        if success
                        else f"Nao consegui executar o comando {command_text}."
                    )
                    self._speak_feedback(feedback)

                # Se ainda ativo, volta a escutar continuamente; caso contrário, idle.
                if self._listening_enabled.is_set():
                    self._set_state("listening")
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
                        self._listening_enabled.set()
                        self._set_state("listening")
                    elif msg_type == "stop_listening":
                        self._listening_enabled.clear()
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

        # Trata Ctrl+C graciosamente
        loop = self._loop
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self._shutdown)
            except NotImplementedError:
                # Windows não suporta add_signal_handler para todos os sinais
                signal.signal(sig, lambda s, f: self._shutdown())

        print(f"[WS] Servidor iniciado em ws://{self.host}:{self.port}")

        async with websockets.serve(self._handler, self.host, self.port):
            await self._broadcast_loop()

    def _shutdown(self) -> None:
        print("\n[WS] Encerrando servidor...")
        self._running = False
        self._listening_enabled.clear()


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
