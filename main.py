#!/usr/bin/env python3
"""
AssistenteOrion - Assistente Virtual por Voz
============================================

Um assistente virtual que roda em segundo plano, sempre ouvindo pela wake word "Orion"
e executando comandos de voz configurados em um arquivo JSON.

Autor: AssistenteOrion
Data: 2024
"""

import os
import sys
import signal
import time
from typing import Optional

# Adiciona o diretório raiz ao path para importações
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.voice_listener import VoiceListener
from utils.command_executor import CommandExecutor


class AssistenteOrion:
    """
    Classe principal do Assistente Orion
    """
    
    def __init__(self):
        """
        Inicializa o assistente
        """
        self.voice_listener = None
        self.command_executor = None
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
            print("           ASSISTENTE ORION - INICIANDO")
            print("=" * 60)
            
            # Verifica se os arquivos necessários existem
            if not os.path.exists("commands/commands.json"):
                print("ERRO: Arquivo commands/commands.json não encontrado!")
                return False
            
            # Inicializa o executor de comandos
            print("Inicializando executor de comandos...")
            self.command_executor = CommandExecutor()
            
            if not self.command_executor.commands:
                print("ERRO: Nenhum comando foi carregado!")
                return False
            
            # Lista os comandos disponíveis
            self.command_executor.list_available_commands()
            
            # Inicializa o listener de voz
            print("\nInicializando listener de voz...")
            self.voice_listener = VoiceListener()
            
            print("✅ AssistenteOrion inicializado com sucesso!")
            print("\n" + "=" * 60)
            print("Para parar o assistente, pressione Ctrl+C")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"ERRO na inicialização: {e}")
            return False
    
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
                    # Aguarda pela wake word "Orion"
                    if self.voice_listener.wait_for_wake_word():
                        print("🎙️  Wake word detectada! Aguardando comando...")
                        
                        # Escuta por um comando
                        command_text = self.voice_listener.listen_for_command()
                        
                        if command_text:
                            print(f"📝 Processando comando: '{command_text}'")
                            
                            # Processa o comando
                            success = self.command_executor.process_voice_command(command_text)
                            
                            if success:
                                print("✅ Comando executado com sucesso!")
                            else:
                                print("❌ Comando não reconhecido ou falhou na execução")
                                print("💡 Diga 'Orion' novamente e tente outro comando")
                        else:
                            print("❌ Não foi possível capturar um comando")
                            print("💡 Diga 'Orion' novamente e tente falar mais claramente")
                        
                        print("\n" + "-" * 60)
                        print("Voltando ao modo de escuta da wake word...")
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


def check_dependencies() -> bool:
    """
    Verifica se as dependências estão instaladas
    
    Returns:
        bool: True se todas as dependências estão disponíveis
    """
    try:
        import speech_recognition
        import pyaudio
        return True
    except ImportError as e:
        print(f"ERRO: Dependência não encontrada - {e}")
        print("\nPor favor, instale as dependências executando:")
        print("pip install -r requirements.txt")
        return False


def main():
    """
    Função principal
    """
    print("Verificando dependências...")
    if not check_dependencies():
        sys.exit(1)
    
    # Cria e executa o assistente
    assistente = AssistenteOrion()
    assistente.run()


if __name__ == "__main__":
    main()
