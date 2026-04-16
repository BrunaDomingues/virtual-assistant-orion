"""
Arquivo de configuração do AssistenteOrion
"""

# Wake Word e suas variações fonéticas
WAKE_WORD = "orion"

# Variações fonéticas aceitas para a wake word
# Adicione aqui novas variações que você perceber que o Google reconhece
WAKE_WORD_VARIATIONS = [
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
    "aurio",     # Variação que pode ocorrer
    "óleo",      # Às vezes confunde com esta palavra (removível se não quiser)
]

# Configurações de timeout
LISTENING_TIMEOUT = 1  # Timeout para escuta contínua da wake word (segundos)
COMMAND_TIMEOUT = 5    # Timeout para captura de comandos (segundos)
PHRASE_TIMEOUT = 0.3   # Timeout entre frases (segundos)

# Configurações de reconhecimento
MAX_COMMAND_ATTEMPTS = 3  # Número máximo de tentativas para capturar comando
COMMAND_SIMILARITY_THRESHOLD = 0.6  # Similaridade mínima para matching de comandos (0 a 1)

# Arquivos
COMMANDS_FILE = "commands/commands.json"
