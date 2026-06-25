"""
Configuração do Assistente Jarvis
"""

ASSISTANT_NAME = "Jarvis"
DEFAULT_ASSISTANT_NAME = "jarvis"

# Wake word padrão (usado só se ainda não houver user_settings.json)
WAKE_WORD = "oi jarvis"

# Configurações de timeout
LISTENING_TIMEOUT = 5
COMMAND_TIMEOUT = 8
PHRASE_TIMEOUT = 0.3

# Detecção de fim de fala
PAUSE_THRESHOLD = 1.1
NON_SPEAKING_DURATION = 0.6
WAKE_PHRASE_TIME_LIMIT = 8
COMMAND_PHRASE_TIME_LIMIT = 30

# Resposta ao acionar com a wake word (texto dinâmico usa o nome salvo)
SPEAK_WAKE_GREETING = True

# Primeira execução: pergunta "Como você quer me chamar?"
ASK_ASSISTANT_NAME_ON_FIRST_RUN = True
SETUP_PROMPT = "Olá! Como você quer me chamar?"
SETUP_LISTEN_TIMEOUT = 12
SETUP_PHRASE_TIME_LIMIT = 15
SETUP_MAX_ROUNDS = 3

# Configurações de reconhecimento
MAX_COMMAND_ATTEMPTS = 3
COMMAND_SIMILARITY_THRESHOLD = 0.6

USE_WAKE_WORD = True

COMMANDS_FILE = "commands/commands.json"

SPEAK_ON_SUCCESS = False
SPEAK_ON_ERROR = False

# Interface desktop — bichinho flutuante (sem abrir Chrome/Edge externo)
DESKTOP_PET_MODE = True
PET_WINDOW_TITLE = "Jarvis"
PET_WINDOW_WIDTH = 360
PET_WINDOW_HEIGHT = 420
