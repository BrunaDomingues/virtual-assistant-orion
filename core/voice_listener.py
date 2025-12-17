import speech_recognition as sr
import time
from typing import Optional, List


class VoiceListener:
    """
    Classe responsável pela escuta contínua de voz e detecção da wake word "Orion"
    """
    
    def __init__(self, wake_word: str = "orion", wake_word_variations: Optional[List[str]] = None, 
                 timeout: int = 1, phrase_timeout: float = 0.3):
        """
        Inicializa o listener de voz
        
        Args:
            wake_word (str): Palavra-chave para ativar o assistente
            wake_word_variations (List[str]): Lista de variações fonéticas aceitas
            timeout (int): Timeout para escuta em segundos
            phrase_timeout (float): Timeout para pausa entre frases
        """
        self.wake_word = wake_word.lower()
        
        # Se não informar variações, usa as padrões
        if wake_word_variations is None:
            self.wake_word_variations = [
                "orion",     # Original
                "órion",     # Com acento
                "orio",      # Comum quando o 'n' não é reconhecido
                "ório",      # Com acento sem o 'n'
                "orião",     # Variação com til
                "hórion",    # Com 'h' aspirado
                "oriom",     # Variação do 'n' para 'm'
                "o rion",    # Separado
                "o rio",     # Separado e sem 'n'
                "oryon",     # Variação com 'y'
            ]
        else:
            self.wake_word_variations = [v.lower() for v in wake_word_variations]
        
        self.timeout = timeout
        self.phrase_timeout = phrase_timeout
        
        # Configurar o reconhecedor
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Ajustar para ruído ambiente
        self._calibrate_microphone()
    
    def _calibrate_microphone(self) -> None:
        """
        Calibra o microfone para o ruído ambiente
        """
        print("Calibrando microfone para ruído ambiente...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        print("Calibração concluída!")
    
    def _listen_for_audio(self) -> Optional[str]:
        """
        Escuta por áudio e converte para texto
        
        Returns:
            Optional[str]: Texto reconhecido ou None se não conseguir reconhecer
        """
        try:
            print("[DEBUG] 🎤 Escutando áudio...")
            with self.microphone as source:
                # Escuta por áudio
                audio = self.recognizer.listen(
                    source, 
                    timeout=self.timeout, 
                    phrase_time_limit=5
                )
            
            print("[DEBUG] 🔄 Processando áudio capturado...")
            # Converte áudio para texto em português
            text = self.recognizer.recognize_google(audio, language='pt-BR')
            text_lower = text.lower().strip()
            
            # LOG IMPORTANTE: Mostra o que foi reconhecido
            print(f"[DEBUG] ✅ Texto reconhecido: '{text}' (normalizado: '{text_lower}')")
            
            return text_lower
            
        except sr.WaitTimeoutError:
            # Timeout normal - continua escutando
            print("[DEBUG] ⏱️ Timeout - nenhum som detectado")
            return None
        except sr.UnknownValueError:
            # Não conseguiu entender o áudio
            print("[DEBUG] ❌ Áudio capturado mas não foi possível entender")
            return None
        except sr.RequestError as e:
            print(f"[ERRO] ⚠️ Erro no serviço de reconhecimento: {e}")
            return None
        except Exception as e:
            print(f"[ERRO] ⚠️ Erro inesperado: {e}")
            return None
    
    def wait_for_wake_word(self) -> bool:
        """
        Fica escutando até detectar a wake word "Orion" ou suas variações fonéticas
        
        Returns:
            bool: True se a wake word foi detectada
        """
        print(f"\n{'='*60}")
        print(f"🔊 AGUARDANDO WAKE WORD: '{self.wake_word.upper()}'")
        print(f"   Variações aceitas: {', '.join(self.wake_word_variations)}")
        print(f"{'='*60}\n")
        
        while True:
            text = self._listen_for_audio()
            
            if text:
                # Verifica se alguma variação da wake word está presente no texto
                detected_variation = None
                for variation in self.wake_word_variations:
                    if variation in text:
                        detected_variation = variation
                        break
                
                if detected_variation:
                    print(f"\n{'='*60}")
                    print(f"🎯 WAKE WORD DETECTADA!")
                    print(f"   Texto completo: '{text}'")
                    print(f"   Variação detectada: '{detected_variation}'")
                    print(f"{'='*60}\n")
                    return True
                else:
                    print(f"[DEBUG] ❌ Wake word NÃO encontrada em: '{text}'")
    
    def listen_for_command(self, max_attempts: int = 3) -> Optional[str]:
        """
        Após detectar a wake word, escuta por um comando
        
        Args:
            max_attempts (int): Número máximo de tentativas para capturar o comando
            
        Returns:
            Optional[str]: Comando reconhecido ou None se não conseguir
        """
        print("🎤 Aguardando comando...")
        
        for attempt in range(max_attempts):
            try:
                print(f"[DEBUG] Tentativa {attempt + 1}/{max_attempts}")
                with self.microphone as source:
                    # Escuta por um comando com timeout maior
                    audio = self.recognizer.listen(
                        source, 
                        timeout=5,  # Timeout maior para comando
                        phrase_time_limit=10
                    )
                
                print("[DEBUG] 🔄 Processando comando...")
                # Converte para texto
                command = self.recognizer.recognize_google(audio, language='pt-BR')
                command = command.lower().strip()
                
                print(f"[DEBUG] ✅ Comando capturado: '{command}'")
                return command
                
            except sr.WaitTimeoutError:
                print(f"[DEBUG] ⏱️ Timeout na tentativa {attempt + 1}/{max_attempts}")
                continue
            except sr.UnknownValueError:
                print(f"[DEBUG] ❌ Não foi possível entender o áudio - tentativa {attempt + 1}/{max_attempts}")
                continue
            except sr.RequestError as e:
                print(f"[ERRO] ⚠️ Erro no serviço de reconhecimento: {e}")
                break
            except Exception as e:
                print(f"[ERRO] ⚠️ Erro inesperado: {e}")
                break
        
        print("❌ Não foi possível capturar um comando válido")
        return None