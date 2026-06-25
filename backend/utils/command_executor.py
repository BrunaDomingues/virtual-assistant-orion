import json
import os
import re
import subprocess
from typing import List, Dict, Optional
from difflib import SequenceMatcher

from utils.spotify_actions import SPOTIFY_ACTIONS, extract_search_query


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
    
    def _command_labels(self, command: Dict) -> List[str]:
        labels = [command.get("label", "")]
        labels.extend(command.get("aliases", []))
        return [label.lower() for label in labels if label]

    def _find_playlist_command(self, spoken_text: str) -> Optional[Dict]:
        spoken_lower = spoken_text.lower().strip()
        playlist_prefixes = (
            "tocar playlist",
            "reproduzir playlist",
            "executar playlist",
            "abrir playlist",
            "colocar playlist",
        )

        if not any(spoken_lower.startswith(p) for p in playlist_prefixes):
            return None

        best_match = None
        best_similarity = 0.0

        for command in self.commands:
            if command.get("action") != "spotify_playlist":
                continue

            for label in self._command_labels(command):
                similarity = self._calculate_similarity(spoken_lower, label)
                spoken_words = spoken_lower.split()
                label_words = label.split()
                word_matches = sum(1 for word in label_words if word in spoken_words)
                word_similarity = word_matches / len(label_words) if label_words else 0
                final_similarity = max(similarity, word_similarity)

                if final_similarity > best_similarity:
                    best_similarity = final_similarity
                    best_match = command

        if best_match and best_similarity >= 0.85:
            print(f"Comando encontrado: '{best_match['label']}' (similaridade: {best_similarity:.2f})")
            return best_match

        for command in self.commands:
            if command.get("action") != "spotify_playlist_search":
                continue

            prefixes = command.get("prefixes") or [command.get("label", "")]
            query = extract_search_query(spoken_lower, prefixes)
            if query:
                print(f"Comando encontrado: '{command['label']}' (playlist: '{query}')")
                return {**command, "_query": query}

        return None

    def _find_prefix_command(self, spoken_text: str) -> Optional[Dict]:
        spoken_lower = spoken_text.lower().strip()

        for command in self.commands:
            if command.get("action") != "spotify_search":
                continue

            prefixes = command.get("prefixes") or [command.get("label", "")]
            query = extract_search_query(spoken_lower, prefixes)
            if query:
                print(f"Comando encontrado: '{command['label']}' (termo: '{query}')")
                return {**command, "_query": query}

        return None

    def _match_template_command(self, spoken_lower: str, label: str) -> Optional[int]:
        """Combina labels com {valor} e extrai o número falado."""
        if "{valor}" not in label:
            return None

        pattern = re.escape(label.lower()).replace(r"\{valor\}", r"(\d+)")
        match = re.fullmatch(pattern, spoken_lower)
        if match:
            return int(match.group(1))

        stem = label.lower().replace(" {valor}", "").replace("{valor}", "").strip()
        if stem and spoken_lower.startswith(stem):
            tail = spoken_lower[len(stem):].strip()
            num = re.search(r"\d+", tail)
            if num:
                return int(num.group())

        return None

    def _find_template_command(self, spoken_text: str) -> Optional[Dict]:
        spoken_lower = spoken_text.lower().strip()

        for command in self.commands:
            if command.get("action") not in ("spotify_volume_up", "spotify_volume_down"):
                continue

            for label in self._command_labels(command):
                amount = self._match_template_command(spoken_lower, label)
                if amount is not None:
                    print(f"Comando encontrado: '{command['label']}' (valor: {amount})")
                    return {**command, "_amount": amount}

        return None

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

        playlist_match = self._find_playlist_command(spoken_text)
        if playlist_match:
            return playlist_match

        template_match = self._find_template_command(spoken_text)
        if template_match:
            return template_match

        spoken_lower = spoken_text.lower().strip()
        best_match = None
        best_similarity = 0.0
        best_label_len = 0
        
        for command in self.commands:
            if command.get("prefixes") and command.get("action") in (
                "spotify_search",
                "spotify_playlist_search",
            ):
                continue

            for label in self._command_labels(command):
                similarity = self._calculate_similarity(spoken_lower, label)
                spoken_words = spoken_lower.split()
                label_words = label.split()
                word_matches = sum(1 for word in label_words if word in spoken_words)
                word_similarity = word_matches / len(label_words) if label_words else 0
                final_similarity = max(similarity, word_similarity)

                if final_similarity > best_similarity or (
                    final_similarity == best_similarity and len(label) > best_label_len
                ):
                    best_similarity = final_similarity
                    best_label_len = len(label)
                    best_match = command
        
        if best_similarity >= min_similarity:
            print(f"Comando encontrado: '{best_match['label']}' (similaridade: {best_similarity:.2f})")
            return best_match

        prefix_match = self._find_prefix_command(spoken_text)
        if prefix_match:
            return prefix_match

        print(f"Nenhum comando encontrado para: '{spoken_text}' (melhor similaridade: {best_similarity:.2f})")
        return None
    
    def _execute_action(self, command: Dict) -> bool:
        action = command.get("action")
        label = command.get("label", "Comando sem nome")
        handler = SPOTIFY_ACTIONS.get(action)

        if not handler:
            print(f"Ação desconhecida: {action}")
            return False

        print(f"Executando: {label}")

        if action == "spotify_search":
            query = command.get("_query", "")
            print(f"Busca: {query}")
            return handler(query)

        if action in ("spotify_playlist", "spotify_playlist_search"):
            arg = command.get("_query") or command.get("playlist_id", "")
            if action == "spotify_playlist_search":
                print(f"Playlist: {arg}")
            else:
                print(f"ID: {arg}")
            return handler(arg)

        if action in ("spotify_volume_up", "spotify_volume_down"):
            amount = command.get("_amount", 3)
            print(f"Passos de volume: {amount}")
            return handler(amount)

        return handler()

    def execute_command(self, command: Dict) -> bool:
        """
        Executa um comando
        
        Args:
            command (Dict): Comando a ser executado com 'label' e 'code' ou 'action'
            
        Returns:
            bool: True se executado com sucesso, False caso contrário
        """
        if not command:
            print("Comando inválido")
            return False

        if command.get("action"):
            try:
                return self._execute_action(command)
            except Exception as e:
                print(f"Erro ao executar ação: {e}")
                return False

        if "code" not in command:
            print("Comando inválido")
            return False
        
        code = command["code"]
        label = command.get("label", "Comando sem nome")
        
        try:
            print(f"Executando: {label}")
            print(f"Código: {code}")
            
            # Executa o comando usando subprocess para melhor controle
            if os.name == "nt":  # Windows
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
            label = command.get("label", "Sem nome")
            detail = command.get("code") or command.get("action", "Sem código")
            aliases = command.get("aliases", [])
            print(f"{i}. {label}")
            if aliases:
                print(f"   Variações: {', '.join(aliases)}")
            if command.get("action") in ("spotify_search", "spotify_playlist_search"):
                prefixes = command.get("prefixes", [])
                example = prefixes[0] if prefixes else command.get("label", "")
                print(f"   Ex.: \"{example} coldplay\"")
            elif command.get("action") == "spotify_playlist":
                print(f"   Playlist ID: {command.get('playlist_id', '—')}")
            print(f"   Detalhe: {detail}")
        print("-" * 50)
