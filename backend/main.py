#!/usr/bin/env python3
"""
AssistenteOrion - Assistente Virtual por Voz
============================================

Um assistente virtual que roda em segundo plano ouvindo comandos de voz
configurados em um arquivo JSON.

Autor: AssistenteOrion
Data: 2024
"""

import os
import sys
import signal
import time
import asyncio
from typing import Optional

# Adiciona o diretório raiz ao path para importações
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.voice_listener import VoiceListener
from core.speaker import OrionSpeaker
from config import (
    ASK_ASSISTANT_NAME_ON_FIRST_RUN,
    SETUP_LISTEN_TIMEOUT,
    SETUP_MAX_ROUNDS,
    SETUP_PHRASE_TIME_LIMIT,
    SETUP_PROMPT,
    SPEAK_ON_ERROR,
    SPEAK_ON_SUCCESS,
    SPEAK_WAKE_GREETING,
    USE_WAKE_WORD,
)
from paths import get_app_dir, get_commands_path, get_frontend_dir, get_settings_path, is_frozen
from utils.command_executor import CommandExecutor
from utils.user_settings import UserSettings, setup_confirmation_for, wake_greeting_for


class AssistenteOrion:
    """
    Classe principal do Assistente Orion
    """
    
    def __init__(self):
        """
        Inicializa o assistente
        """
        self.voice_listener = None
        self.speaker = OrionSpeaker()
        self.command_executor = None
        self.settings = UserSettings.load()
        self.running = False
        
        # Configura o handler para interrupção (Ctrl+C)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """
        Handler para sinais de interrupção
        """
        print("\n\nRecebido sinal de interrupção. Encerrando AssistenteOrion...")
        self.running = False
    
    def initialize(self) -> bool:
        """
        Inicializa os componentes do assistente
        
        Returns:
            bool: True se inicializado com sucesso
        """
        try:
            print("=" * 60)
            print(f"           ASSISTENTE {self.settings.display_name().upper()} - INICIANDO")
            print("=" * 60)
            
            commands_path = get_commands_path()
            if not os.path.exists(commands_path):
                print(f"ERRO: Arquivo de comandos não encontrado: {commands_path}")
                return False

            # Inicializa o executor de comandos
            print("Inicializando executor de comandos...")
            self.command_executor = CommandExecutor(commands_file=commands_path)
            
            if not self.command_executor.commands:
                print("ERRO: Nenhum comando foi carregado!")
                return False
            
            # Lista os comandos disponíveis
            self.command_executor.list_available_commands()
            
            # Inicializa o listener de voz
            print("\nInicializando listener de voz...")
            self.voice_listener = VoiceListener()
            self._run_name_setup()

            print("✅ AssistenteOrion inicializado com sucesso!")
            if USE_WAKE_WORD:
                print(f'Diga "{self.settings.wake_word}" para ativar.')
            print("\n" + "=" * 60)
            print("Para parar o assistente, pressione Ctrl+C")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"ERRO na inicialização: {e}")
            return False
    
    def _run_name_setup(self) -> None:
        if not ASK_ASSISTANT_NAME_ON_FIRST_RUN or self.settings.configured:
            self.voice_listener.apply_assistant_name(self.settings.assistant_name)
            return

        print("\nPrimeira execução — configurando nome do assistente...")
        self.speak_response(SETUP_PROMPT)

        saved = False
        for round_idx in range(SETUP_MAX_ROUNDS):
            spoken = self.voice_listener.listen_for_assistant_name(
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
                self.speak_response("Desculpe, não entendi. Como você quer me chamar?")

        if not saved:
            print("Nome não configurado — será perguntado novamente na próxima execução.")
            self.voice_listener.apply_assistant_name(self.settings.assistant_name)
            return

        self.voice_listener.apply_assistant_name(self.settings.assistant_name)
        self.speak_response(setup_confirmation_for(self.settings.assistant_name))
        print(f'Wake word: "{self.settings.wake_word}"')
        print(f"Salvo em: {get_settings_path()}")
    
    def run(self) -> None:
        """
        Loop principal do assistente
        """
        if not self.initialize():
            print("Falha na inicialização. Encerrando...")
            return
        
        self.running = True
        
        try:
            while self.running:
                try:
                    if USE_WAKE_WORD:
                        detected, inline_command = self.voice_listener.wait_for_wake_word(
                            lambda: self.running
                        )
                        if not detected:
                            continue
                        if inline_command:
                            command_text = inline_command
                        else:
                            if SPEAK_WAKE_GREETING:
                                self.speak_response(wake_greeting_for(self.settings.assistant_name))
                            command_text = self.voice_listener.listen_for_command()
                    else:
                        command_text = self.voice_listener.listen_for_command(max_attempts=1)

                    if command_text:
                        print(f"📝 Processando comando: '{command_text}'")

                        # Processa o comando
                        success = self.command_executor.process_voice_command(command_text)

                        if success:
                            print("✅ Comando executado com sucesso!")
                            if SPEAK_ON_SUCCESS:
                                self.speak_response(f"Comando {command_text} executado com sucesso.")
                        else:
                            print("❌ Comando não reconhecido ou falhou na execução")
                            if SPEAK_ON_ERROR:
                                self.speak_response(f"Nao consegui executar o comando {command_text}.")

                        print("\n" + "-" * 60)
                        print("Continuando em escuta contínua...")
                        print("-" * 60 + "\n")
                
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Erro no loop principal: {e}")
                    print("Continuando execução...")
                    time.sleep(1)
        
        except Exception as e:
            print(f"Erro crítico: {e}")
        
        finally:
            print("\n🔴 AssistenteOrion encerrado.")

    def speak_response(self, text: str) -> None:
        """
        Fala um texto de resposta em modo legado.
        Pode ser usado para feedback de comandos e respostas do Gemini.
        """
        if not text or not text.strip():
            return
        try:
            asyncio.run(self.speaker.speak(text))
        except Exception as e:
            print(f"[TTS] Falha ao reproduzir audio: {e}")


def _setup_frozen_logging() -> None:
    """Sem console no .exe — grava logs em jarvis.log ao lado do executável."""
    if not is_frozen():
        return

    log_path = get_app_dir() / "jarvis.log"
    try:
        log_file = open(log_path, "a", encoding="utf-8", buffering=1)
        sys.stdout = log_file
        sys.stderr = log_file
        print(f"\n--- Jarvis iniciado ---")
    except OSError:
        pass


def check_dependencies() -> bool:
    """
    Verifica se as dependências estão instaladas
    
    Returns:
        bool: True se todas as dependências estão disponíveis
    """
    try:
        import speech_recognition  # noqa: F401
        import sounddevice  # noqa: F401
        return True
    except ImportError as e:
        print(f"ERRO: Dependência não encontrada - {e}")
        print("\nPor favor, instale as dependências executando:")
        print("pip install -r requirements.txt")
        return False


def _start_frontend(use_browser: bool = False) -> None:
    """Abre a interface quando empacotado em .exe ou com --with-ui."""
    if not is_frozen() and "--with-ui" not in sys.argv and "--browser" not in sys.argv:
        return

    frontend_dir = get_frontend_dir()
    if frontend_dir is None:
        if is_frozen():
            print("AVISO: Interface não encontrada no pacote.")
        else:
            print("AVISO: Pasta dist/ não encontrada. Execute 'npm run build' na raiz do projeto.")
        return

    from desktop_window import start_ui

    start_ui(str(frontend_dir), use_browser=use_browser)


def main():
    """
    Função principal.

    Modo padrão: servidor WebSocket + assistente flutuante na área de trabalho (.exe).

    Flags:
        python main.py --legacy     terminal, sem interface
        python main.py --with-ui    interface pet (dev)
        python main.py --browser      abre no navegador em vez da janela flutuante
    """
    if "--legacy" in sys.argv:
        print("Verificando dependências...")
        if not check_dependencies():
            sys.exit(1)
        assistente = AssistenteOrion()
        assistente.run()
    else:
        from app_launcher import run_with_desktop_pet, should_show_ui, use_browser_ui
        from config import DESKTOP_PET_MODE
        from server import OrionWebSocketServer, _check_dependencies

        if not _check_dependencies():
            sys.exit(1)

        def _run_server() -> None:
            try:
                asyncio.run(OrionWebSocketServer().start())
            except KeyboardInterrupt:
                print("\nServidor encerrado.")

        def _start_ui(**kwargs) -> None:
            _start_frontend(use_browser=kwargs.get("use_browser", False))

        if should_show_ui(is_frozen, sys.argv) and DESKTOP_PET_MODE and not use_browser_ui(sys.argv):
            frontend_dir = get_frontend_dir()
            if frontend_dir is None:
                if is_frozen():
                    print("AVISO: Interface não encontrada no pacote.")
                else:
                    print("AVISO: Pasta dist/ não encontrada. Execute 'npm run build' na raiz do projeto.")
                _run_server()
                return

            def _launch() -> None:
                from desktop_window import start_ui as open_ui
                open_ui(str(frontend_dir), use_browser=False)

            run_with_desktop_pet(_launch, _run_server)
        else:
            _start_frontend(use_browser=use_browser_ui(sys.argv))
            _run_server()


if __name__ == "__main__":
    _setup_frozen_logging()
    main()
