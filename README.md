# AssistenteOrion 🤖🎙️

Um assistente virtual por voz que roda em segundo plano no PC, sempre ouvindo pela wake word "Orion" e executando comandos de voz configurados dinamicamente através de um arquivo JSON.

## 🚀 Funcionalidades

- **Wake Word**: Ativação por voz com a palavra "Orion"
- **Reconhecimento de Voz**: Processamento de comandos em português brasileiro
- **Comandos Dinâmicos**: Comandos carregados de arquivo JSON (sem hard-coding)
- **Execução em Segundo Plano**: Loop infinito aguardando comandos
- **Fácil Expansão**: Adicione novos comandos apenas editando o JSON

## 📁 Estrutura do Projeto

```
AssistenteOrion/
├── main.py                 # Ponto de entrada do assistente
├── requirements.txt        # Dependências Python
├── README.md              # Este arquivo
├── core/                  # Lógica principal
│   ├── __init__.py
│   └── voice_listener.py  # Escuta e reconhecimento de voz
├── utils/                 # Funções auxiliares
│   ├── __init__.py
│   └── command_executor.py # Executor de comandos
└── commands/              # Configurações de comandos
    └── commands.json      # Comandos disponíveis
```

## ⚙️ Instalação

### 1. Pré-requisitos
- Python 3.7 ou superior
- Microfone funcional
- Windows (testado no Windows 10/11)

### 2. Clonar o projeto
```bash
git clone <url-do-repositorio>
cd AssistenteOrion
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

**Nota**: Se houver problemas com `pyaudio` no Windows, você pode tentar:
```bash
pip install pipwin
pipwin install pyaudio
```

### 4. Executar o assistente
```bash
python main.py
```

## 🎯 Como Usar

1. **Execute o assistente**: `python main.py`
2. **Aguarde a calibração**: O assistente ajustará para o ruído ambiente
3. **Diga a wake word**: "Orion" (aceita variações fonéticas como "orio", "órion", etc.)
4. **Aguarde o feedback**: O assistente confirmará que ouviu
5. **Diga seu comando**: Por exemplo, "abrir chrome"
6. **O comando será executado**: Se reconhecido corretamente

### 🎙️ Variações Fonéticas da Wake Word

O assistente aceita automaticamente estas variações de "Orion":
- `orion` - Original
- `órion` - Com acento
- `orio` - Sem o 'n' final (comum no reconhecimento)
- `ório` - Com acento e sem o 'n'
- `orião` - Com til
- `hórion` - Com 'h' aspirado
- `oriom` - Com 'm' no lugar do 'n'
- `o rion` - Separado
- `o rio` - Separado e sem 'n'
- `oryon` - Com 'y'

Isso resolve problemas de reconhecimento fonético!

### Exemplo de Uso
```
Usuário: "Orion"
Assistente: "Wake word detectada! Aguardando comando..."
Usuário: "abrir bloco de notas"
Assistente: "Comando executado com sucesso!"
[Bloco de notas é aberto]
```

## 📝 Adicionando Novos Comandos

Para adicionar novos comandos, edite o arquivo `commands/commands.json`:

```json
[
  {
    "label": "seu comando de voz",
    "code": "comando do sistema operacional"
  }
]
```

### Estrutura do JSON

- **label**: Como você vai falar o comando (em português)
- **code**: Comando que será executado no sistema operacional

### Exemplos de Comandos

```json
[
  {
    "label": "abrir chrome",
    "code": "start chrome"
  },
  {
    "label": "abrir bloco de notas",
    "code": "notepad"
  },
  {
    "label": "bloquear tela",
    "code": "rundll32.exe user32.dll, LockWorkStation"
  },
  {
    "label": "abrir calculadora",
    "code": "calc"
  },
  {
    "label": "abrir pasta documentos",
    "code": "explorer %USERPROFILE%\\Documents"
  },
  {
    "label": "verificar ip",
    "code": "ipconfig"
  },
  {
    "label": "abrir prompt",
    "code": "cmd"
  },
  {
    "label": "desligar computador",
    "code": "shutdown /s /t 0"
  },
  {
    "label": "reiniciar computador",
    "code": "shutdown /r /t 0"
  }
]
```

## 🔧 Comandos Pré-configurados

O assistente vem com os seguintes comandos já configurados:

| Comando de Voz | Ação |
|---|---|
| "abrir chrome" | Abre o Google Chrome |
| "abrir bloco de notas" | Abre o Notepad |
| "bloquear tela" | Bloqueia a tela do Windows |
| "abrir calculadora" | Abre a Calculadora |
| "abrir explorador de arquivos" | Abre o Windows Explorer |
| "desligar computador" | Desliga o computador |
| "reiniciar computador" | Reinicia o computador |

## ⚠️ Comandos Perigosos

**CUIDADO** com comandos que podem:
- Desligar ou reiniciar o computador
- Deletar arquivos
- Modificar configurações do sistema
- Executar scripts maliciosos

Sempre teste novos comandos antes de deixar o assistente rodando desacompanhado.

## 🛠️ Personalização Avançada

### Ajustar Sensibilidade de Reconhecimento

No arquivo `utils/command_executor.py`, você pode ajustar o parâmetro `min_similarity` na função `find_command()`:

```python
def find_command(self, spoken_text: str, min_similarity: float = 0.6):
    # Valores menores = mais flexível (pode executar comandos errados)
    # Valores maiores = mais restritivo (pode não reconhecer comandos válidos)
```

### Modificar Wake Word

No arquivo `main.py`, você pode mudar a wake word padrão:

```python
self.voice_listener = VoiceListener(wake_word="sua_palavra")
```

### Ajustar Timeouts

No arquivo `core/voice_listener.py`, você pode modificar os timeouts:

```python
self.voice_listener = VoiceListener(
    wake_word="orion",
    timeout=1,           # Timeout para escuta contínua
    phrase_timeout=0.3   # Timeout entre frases
)
```

## 🐛 Solução de Problemas

### Erro de Microfone
- Verifique se o microfone está conectado e funcionando
- Teste o microfone em outras aplicações
- Execute o assistente como administrador

### Erro de Reconhecimento
- Fale mais devagar e claramente
- Reduza o ruído ambiente
- Ajuste a distância do microfone
- Verifique sua conexão com a internet (usa Google Speech API)

### PyAudio não instala
No Windows:
```bash
pip install pipwin
pipwin install pyaudio
```

### Comandos não reconhecidos
- Verifique se o `commands.json` está bem formatado
- Teste falar o comando exatamente como está no "label"
- Reduza o `min_similarity` para ser mais flexível

### Assistente não responde
- Pressione Ctrl+C e reinicie
- Verifique se não há erros no console
- Teste sua conexão com a internet

## 📊 Logs e Debug

O assistente exibe informações detalhadas no console:
- Status de inicialização
- Comandos carregados
- Wake word detectada
- Comandos reconhecidos
- Resultados de execução

Use essas informações para diagnosticar problemas.

## 🔄 Atualizações Futuras

Possíveis melhorias planejadas:
- [ ] Interface gráfica para gerenciar comandos
- [ ] Suporte a comandos com parâmetros
- [ ] Reconhecimento offline
- [ ] Feedback por voz
- [ ] Comandos condicionais
- [ ] Integração com APIs externas
- [ ] Modo de treinamento personalizado

## 📄 Licença

Este projeto é open source. Sinta-se livre para modificar e distribuir.

## 🤝 Contribuição

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

## 📞 Suporte

Se encontrar problemas ou tiver sugestões, abra uma issue no repositório do projeto.

---

**AssistenteOrion** - Seu assistente virtual inteligente por voz! 🚀
