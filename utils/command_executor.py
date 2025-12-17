import json
import os
import subprocess
from typing import List, Dict, Optional
from difflib import SequenceMatcher


class CommandExecutor:
    """
    Classe responsável por carregar comandos do JSON e executá-los
    """
    
    def __init__(self, commands_file: str = "commands/commands.json"):
        """
        Inicializa o executor de comandos
        
        Args:
            commands_file (str): Caminho para o arquivo JSON com os comandos
        """
        self.commands_file = commands_file
        self.commands = []
        self.load_commands()
    
    def load_commands(self) -> None:
        """
        Carrega os comandos do arquivo JSON
        """
        try:
            if not os.path.exists(self.commands_file):
                raise FileNotFoundError(f"Arquivo {self.commands_file} não encontrado")
            
            with open(self.commands_file, 'r', encoding='utf-8') as file:
                self.commands = json.load(file)
            
            print(f"Carregados {len(self.commands)} comandos do arquivo {self.commands_file}")
            
        except FileNotFoundError as e:
            print(f"Erro: {e}")
            self.commands = []
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON: {e}")
            self.commands = []
        except Exception as e:
            print(f"Erro inesperado ao carregar comandos: {e}")
            self.commands = []
    
    def reload_commands(self) -> None:
        """
        Recarrega os comandos do arquivo JSON
        """
        print("Recarregando comandos...")
        self.load_commands()
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calcula a similaridade entre duas strings
        
        Args:
            text1 (str): Primeira string
            text2 (str): Segunda string
            
        Returns:
            float: Valor de similaridade entre 0 e 1
        """
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def find_command(self, spoken_text: str, min_similarity: float = 0.6) -> Optional[Dict]:
        """
        Encontra o comando mais similar ao texto falado
        
        Args:
            spoken_text (str): Texto reconhecido pela voz
            min_similarity (float): Similaridade mínima para considerar uma correspondência
            
        Returns:
            Optional[Dict]: Comando encontrado ou None se não encontrar
        """
        if not self.commands:
            print("Nenhum comando carregado")
            return None
        
        best_match = None
        best_similarity = 0.0
        
        for command in self.commands:
            label = command.get('label', '').lower()
            similarity = self._calculate_similarity(spoken_text, label)
            
            # Verifica também se o texto falado contém palavras-chave do comando
            spoken_words = spoken_text.split()
            label_words = label.split()
            
            # Conta quantas palavras do comando estão presentes no texto falado
            word_matches = sum(1 for word in label_words if word in spoken_words)
            word_similarity = word_matches / len(label_words) if label_words else 0
            
            # Usa a maior similaridade entre os dois métodos
            final_similarity = max(similarity, word_similarity)
            
            if final_similarity > best_similarity:
                best_similarity = final_similarity
                best_match = command
        
        if best_similarity >= min_similarity:
            print(f"Comando encontrado: '{best_match['label']}' (similaridade: {best_similarity:.2f})")
            return best_match
        else:
            print(f"Nenhum comando encontrado para: '{spoken_text}' (melhor similaridade: {best_similarity:.2f})")
            return None
    
    def execute_command(self, command: Dict) -> bool:
        """
        Executa um comando
        
        Args:
            command (Dict): Comando a ser executado com 'label' e 'code'
            
        Returns:
            bool: True se executado com sucesso, False caso contrário
        """
        if not command or 'code' not in command:
            print("Comando inválido")
            return False
        
        code = command['code']
        label = command.get('label', 'Comando sem nome')
        
        try:
            print(f"Executando: {label}")
            print(f"Código: {code}")
            
            # Executa o comando usando subprocess para melhor controle
            if os.name == 'nt':  # Windows
                # No Windows, usa shell=True para comandos como 'start'
                result = subprocess.run(
                    code, 
                    shell=True, 
                    capture_output=True, 
                    text=True,
                    timeout=30
                )
            else:  # Linux/macOS
                result = subprocess.run(
                    code.split(), 
                    capture_output=True, 
                    text=True,
                    timeout=30
                )
            
            if result.returncode == 0:
                print("Comando executado com sucesso!")
                return True
            else:
                print(f"Comando falhou com código de saída: {result.returncode}")
                if result.stderr:
                    print(f"Erro: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("Comando expirou (timeout)")
            return False
        except Exception as e:
            print(f"Erro ao executar comando: {e}")
            return False
    
    def process_voice_command(self, spoken_text: str) -> bool:
        """
        Processa um comando de voz completo: encontra e executa
        
        Args:
            spoken_text (str): Texto reconhecido pela voz
            
        Returns:
            bool: True se comando foi encontrado e executado, False caso contrário
        """
        command = self.find_command(spoken_text)
        if command:
            return self.execute_command(command)
        return False
    
    def list_available_commands(self) -> None:
        """
        Lista todos os comandos disponíveis
        """
        if not self.commands:
            print("Nenhum comando disponível")
            return
        
        print("\nComandos disponíveis:")
        print("-" * 50)
        for i, command in enumerate(self.commands, 1):
            label = command.get('label', 'Sem nome')
            code = command.get('code', 'Sem código')
            print(f"{i}. {label}")
            print(f"   Código: {code}")
        print("-" * 50)
