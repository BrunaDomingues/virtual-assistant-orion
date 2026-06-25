# Assistente Jarvis

Fork personalizado do [virtual-assistant-orion](https://github.com/KevinAllysson/virtual-assistant-orion): assistente virtual por voz para Windows com interface 3D flutuante (modo pet), wake word configurável, comandos Spotify e empacotamento em `.exe`.

---

## O que mudou neste fork

| Recurso | Descrição |
|---|---|
| **Janela flutuante** | Abre só o “bichinho” na área de trabalho — sem navegador e sem terminal |
| **Wake word dinâmica** | Na 1ª execução pergunta o nome; depois usa `oi {nome}` |
| **Escuta automática** | Fica em standby ouvindo a wake word — sem botão |
| **Comandos Spotify** | Abrir, play/pause, pular, buscar, playlist por nome/ID |
| **Executável Windows** | `.\build.ps1` gera `release\Jarvis\Jarvis.exe` |
| **Preferências locais** | `user_settings.json` ao lado do `.exe` (não vai pro Git) |

---

## Visão geral da arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│  Interface (React + Three.js)                               │
│  Modo pet: rosto 3D + status + bolha de fala                │
│  Servida em localhost:4173 (pywebview ou navegador)         │
└───────────────────┬─────────────────────────────────────────┘
                    │  WebSocket  ws://localhost:8765
┌───────────────────▼─────────────────────────────────────────┐
│  Backend (Python)                                           │
│  VoiceListener    → microfone + Google Speech API           │
│  CommandExecutor  → fuzzy match + subprocess / Spotify      │
│  OrionSpeaker     → edge-tts + pygame                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Pré-requisitos

| Dependência | Versão mínima | Para quê |
|---|---|---|
| Python | 3.12+ | Backend / reconhecimento de voz |
| Node.js | 18+ | Frontend React (dev e build) |
| Microfone | — | Captura de áudio |
| Internet | — | Google Speech API + edge-tts |
| WebView2 | — | Janela desktop no `.exe` (já vem no Win 10/11) |

> Python 3.13 funciona. PyAudio **não é necessário** — o projeto usa `sounddevice`.

---

## Estrutura do projeto

```
virtual-assistant-orion/
├── backend/
│   ├── main.py                 # Ponto de entrada
│   ├── server.py               # WebSocket + loop de voz
│   ├── desktop_window.py       # Janela flutuante (pywebview)
│   ├── static_server.py        # HTTP para o build React
│   ├── paths.py                # Caminhos dev / .exe
│   ├── config.py               # Wake word, TTS, modo pet
│   ├── commands/commands.json  # Comandos de voz
│   └── utils/
│       ├── command_executor.py
│       ├── spotify_actions.py
│       └── user_settings.py    # Nome do assistente
├── src/                        # Frontend React + Three.js
├── build.ps1                   # Gera Jarvis.exe (Windows)
├── jarvis.spec                 # Config PyInstaller
└── release/Jarvis/             # Saída do build (gitignored)
```

---

## Instalação (desenvolvimento)

```powershell
git clone https://github.com/BrunaDomingues/virtual-assistant-orion.git
cd virtual-assistant-orion

cd backend
py -m pip install -r requirements.txt

cd ..
npm install
npm run build
```

---

## Como usar

### Opção A — Executável (recomendado)

```powershell
.\build.ps1
```

Depois abra **`release\Jarvis\Jarvis.exe`** (use a pasta inteira, não só o `.exe`).

- Só a janelinha flutuante aparece (sem prompt preto)
- Logs em `release\Jarvis\jarvis.log`
- Na **primeira execução**, ele pergunta: *"Como você quer me chamar?"*
- Depois diga **`oi {seu nome}`** para ativar e fale o comando

Para **trocar o nome**, apague `release\Jarvis\user_settings.json` e abra de novo.

### Opção B — Desenvolvimento

```powershell
cd backend
py main.py --with-ui
```

Abre a janela pet localmente (precisa de `npm run build` antes).

### Flags do backend

| Comando | Efeito |
|---|---|
| `py main.py` | Backend + UI pet (se `dist/` existir ou estiver empacotado) |
| `py main.py --with-ui` | Força interface pet em dev |
| `py main.py --browser` | Abre no navegador em vez da janela flutuante |
| `py main.py --legacy` | Só terminal, sem interface |

---

## Fluxo de voz

1. Microfone em **standby** — aguardando wake word
2. Você fala: **`oi jarvis`** (ou o nome que configurou)
3. TTS: *"Oi! {Nome} ouvindo."*
4. Fale o comando e **pause** (~1 s de silêncio)
5. Comando executado → volta ao standby

Feedback por voz após comandos está **desligado** por padrão (`SPEAK_ON_SUCCESS = False` em `config.py`).

---

## Comandos disponíveis

### Sistema

| Fale | Ação |
|---|---|
| "abrir chrome" | Abre o Google Chrome |
| "abrir bloco de notas" | Abre o Notepad |
| "abrir calculadora" | Abre a Calculadora |
| "abrir os arquivos do computador" | Abre o Explorer |
| "bloquear tela" | Bloqueia o Windows |
| "aumentar volume" / "baixar volume" | Volume do sistema |
| "desligar computador" / "reiniciar computador" | Energia |

### Spotify

| Fale | Ação |
|---|---|
| "abrir spotify" | Abre o app |
| "play no spotify" / "pausar música" | Play/pause |
| "pular música" / "música anterior" | Faixas |
| "pesquisar no spotify {artista}" | Busca e toca |
| "tocar playlist {nome}" | Busca playlist |
| "aumentar volume em {valor}" | Volume Spotify (0–100) |

### Adicionar comandos

Edite `backend/commands/commands.json`. Reinicie o backend para recarregar.

Para ações customizadas (ex.: Spotify), use um `code` simbólico e implemente em `backend/utils/spotify_actions.py` ou `command_executor.py`.

---

## Configuração

Arquivo `backend/config.py`:

```python
DESKTOP_PET_MODE = True      # Janela flutuante (False = navegador)
SPEAK_WAKE_GREETING = True   # Responde ao "oi {nome}"
SPEAK_ON_SUCCESS = False     # TTS após comando OK
ASK_ASSISTANT_NAME_ON_FIRST_RUN = True
```

Preferências do usuário ficam em **`user_settings.json`** (ao lado do `.exe` ou em `backend/` em dev).

---

## Solução de problemas

### `.exe` abre e fecha na hora

- Veja `release\Jarvis\jarvis.log`
- Rode a pasta inteira `release\Jarvis\`, não só o `.exe`
- Instale [WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/) se a janela não aparecer

### Nome não salvou / sempre pergunta de novo

- Fale só o nome após a pergunta (ex.: "Nova")
- Verifique permissão de microfone para o app
- Confira se `user_settings.json` foi criado ao lado do `.exe`

### Wake word não funciona

- Use exatamente `oi {nome}` em minúsculas na fala
- Apague `user_settings.json` para reconfigurar

### Backend offline na interface

- Porta 8765 livre: `netstat -an | findstr 8765`
- Reinicie o `.exe` ou `py main.py --with-ui`

### Build falha (“arquivo em uso”)

- Feche o `Jarvis.exe` antes de rodar `.\build.ps1`

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Reconhecimento de voz | `speech_recognition` + Google Speech API |
| Captura de áudio | `sounddevice` |
| TTS | `edge-tts` + `pygame` |
| WebSocket | `websockets` (asyncio) |
| Janela desktop | `pywebview` (Edge WebView2) |
| Interface 3D | React 18 + Three.js + R3F |
| Empacotamento | PyInstaller |

---

## Fork e upstream

Este repositório é um **fork** de [KevinAllysson/virtual-assistant-orion](https://github.com/KevinAllysson/virtual-assistant-orion).

Para sincronizar com o original:

```powershell
git remote add upstream https://github.com/KevinAllysson/virtual-assistant-orion.git
git fetch upstream
git merge upstream/main
```

---

## Licença

Open source. Sinta-se livre para modificar e distribuir.
