# Assistente Orion

Assistente virtual por voz com interface visual 3D. A escuta é ativada manualmente por botão no frontend, reconhece comandos em português e executa ações no Windows com feedback visual e resposta por voz (TTS) em tempo real.

---

## Visão geral da arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend  (React + Three.js)   –  npm run dev → :5173      │
│                                                             │
│   Rosto 3D (nuvem de pontos + wireframe MediaPipe)          │
│   HUD: estado, comandos, parâmetros neurais                 │
└───────────────────┬─────────────────────────────────────────┘
                    │  WebSocket  ws://localhost:8765
┌───────────────────▼─────────────────────────────────────────┐
│  Backend   (Python)             –  python main.py → :8765   │
│                                                             │
│   VoiceListener   → microfone + Google Speech API            │
│   CommandExecutor → fuzzy match + subprocess                 │
│   OrionSpeaker    → edge-tts + pygame (resposta por voz)    │
└─────────────────────────────────────────────────────────────┘
```

O backend emite eventos JSON (`state`, `recognized`, `command`, `error`) para o frontend via WebSocket. O frontend também envia `start_listening` e `stop_listening` para controlar a escuta contínua sem wake word.

---

## Pré-requisitos

| Dependência | Versão mínima | Para quê |
|---|---|---|
| Python | 3.12+ | Backend / reconhecimento de voz |
| Node.js | 18+ | Frontend React |
| Microfone | — | Captura de áudio |
| Internet | — | Google Speech API (reconhecimento) |

> Python 3.14 é suportado. PyAudio **não é necessário** — o projeto usa `sounddevice`.

---

## Estrutura do projeto

```
virtual-assistant-orion/
├── backend/                    # Servidor Python
│   ├── main.py                 # Ponto de entrada
│   ├── server.py               # Servidor WebSocket (ws://localhost:8765)
│   ├── requirements.txt        # Dependências Python
│   ├── core/
│   │   ├── voice_listener.py   # Captura + reconhecimento de comando
│   │   └── speaker.py          # TTS assíncrono (edge-tts + pygame)
│   ├── utils/
│   │   └── command_executor.py # Fuzzy match + execução de comandos
│   └── commands/
│       └── commands.json       # Comandos de voz configuráveis
│
├── src/                        # Aplicação React
│   ├── App.jsx                 # Orquestração: HUD + estado
│   ├── index.css               # Estilo global (Share Tech Mono, animações)
│   ├── hooks/
│   │   └── useOrionSocket.js   # Hook WebSocket com reconexão automática
│   ├── components/
│   │   ├── AgentFace.jsx       # Canvas R3F: rosto, anéis, partículas, Bloom
│   │   └── FaceMesh.jsx        # Nuvem de pontos + wireframe + olhos animados
│   └── data/
│       └── faceLandmarks.js    # Loader do modelo OBJ (MediaPipe 468 vértices)
│
├── index.html                  # HTML raiz (fonte Share Tech Mono)
├── vite.config.js              # Configuração Vite 5
└── package.json
```

---

## Instalação

### 1. Clonar o repositório

```powershell
git clone https://github.com/KevinAllysson/virtual-assistant-orion.git
cd virtual-assistant-orion
```

### 2. Instalar dependências do backend

```powershell
cd backend
pip install -r requirements.txt
```

> Se aparecer erro de compilação do `PyAudio`: ele não é mais usado. Certifique-se de estar usando o `requirements.txt` atualizado que usa `sounddevice`.

### 3. Instalar dependências do frontend

```powershell
cd ..          # volta para a raiz do projeto
npm install
```

---

## Como iniciar

Abra **dois terminais** separados.

### Terminal 1 — Backend (servidor de voz)

```powershell
cd backend
python main.py
```

Você verá:

```
============================================================
       ASSISTENTE ORION - SERVIDOR WebSocket
       ws://localhost:8765
============================================================
Inicializando executor de comandos...
Carregados 9 comandos do arquivo commands/commands.json
...
Calibrando microfone para ruído ambiente...
[WS] Servidor iniciado em ws://localhost:8765
```

### Terminal 2 — Frontend (interface visual)

```powershell
npm run dev
```

Acesse **http://localhost:5173** no navegador.

Assim que o backend estiver rodando, o painel direito do HUD mostrará `BACKEND: ONLINE` e o botão `INICIAR ESCUTA` ficará disponível para ativar a captura de voz.

---

## Como usar

1. Com ambos os servidores rodando, clique em **INICIAR ESCUTA** no HUD.
2. O rosto 3D muda para o estado **LISTENING**.
3. Diga um comando — por exemplo: **"abrir chrome"**.
4. A interface passa por **PROCESSING** e depois **SPEAKING** enquanto a resposta em voz é reproduzida.
5. Ao terminar, o assistente volta para **LISTENING** (se escuta contínua ativa) ou **STANDBY**.
6. Clique em **PARAR ESCUTA** para encerrar a captura contínua.

---

## Comandos disponíveis

| Fale | Ação |
|---|---|
| "abrir chrome" | Abre o Google Chrome |
| "abrir bloco de notas" | Abre o Notepad |
| "bloquear tela" | Bloqueia a sessão do Windows |
| "abrir calculadora" | Abre a Calculadora |
| "abrir os arquivos do computador" | Abre o Windows Explorer |
| "aumentar volume" | Aumenta o volume do sistema |
| "baixar volume" | Diminui o volume do sistema |
| "desligar computador" | Desliga o PC |
| "reiniciar computador" | Reinicia o PC |

### Adicionar novos comandos

Edite `backend/commands/commands.json`:

```json
[
  {
    "label": "abrir spotify",
    "code": "start spotify"
  }
]
```

- `label` — exatamente o que você vai falar (português)
- `code` — comando executado via `subprocess` no Windows

O backend recarrega o arquivo automaticamente a cada inicialização. Não é necessário reiniciar para trocar comandos — basta reiniciar o `python main.py`.

---

## Modo legado (terminal sem frontend)

Se quiser rodar apenas o backend no terminal, sem o servidor WebSocket:

```powershell
cd backend
python main.py --legacy
```

No modo legado, o assistente também usa TTS para dar feedback após cada comando executado.

---

## Solução de problemas

### Backend não inicia / erro de microfone

```
ERRO na inicialização: ...
```

- Verifique se o microfone está conectado e não está em uso por outro app.
- Teste com `py -3.14 -c "import sounddevice as sd; print(sd.query_devices())"`.

### Erro de compilação ao instalar dependências

```
error: Microsoft Visual C++ 14.0 or greater is required
```

O `PyAudio` não é mais usado. Se aparecer esse erro, confirme que o `requirements.txt` contém `sounddevice` e **não** `pyaudio`.

### Frontend mostra `BACKEND: OFFLINE`

- Confirme que `python main.py` está rodando no terminal 1.
- Verifique se a porta 8765 está livre: `netstat -an | findstr 8765`.
- O frontend tentará reconectar automaticamente a cada 2 segundos.

### Rosto 3D não aparece (tela preta)

- O modelo OBJ é baixado do GitHub ao abrir o app — verifique sua conexão com a internet.
- Durante o download o placeholder (icosaedro wireframe) é exibido.

### Comandos não são reconhecidos

- Fale de forma clara e próxima ao microfone.
- Verifique sua conexão com a internet (o reconhecimento usa a Google Speech API).
- Reduza a sensibilidade mínima em `backend/utils/command_executor.py`:
  ```python
  def find_command(self, spoken_text: str, min_similarity: float = 0.5):
  ```

### Botão de escuta não ativa captura

- Confirme que `python main.py` está rodando no backend.
- Verifique se o frontend mostra `BACKEND: ONLINE`.
- Se necessário, reinicie backend e frontend.

### Sem áudio de resposta (TTS)

- Verifique se as dependências foram instaladas com `pip install -r requirements.txt`.
- Confirme que `edge-tts` e `pygame` estão presentes no ambiente Python ativo.
- Verifique se há dispositivo de saída de áudio disponível no sistema.

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Reconhecimento de voz | `speech_recognition` + Google Speech API |
| Captura de áudio | `sounddevice` (sem PyAudio) |
| Resposta por voz (TTS) | `edge-tts` + `pygame` |
| Servidor WebSocket | `websockets` (Python asyncio) |
| Interface 3D | React 18 + Three.js ~0.168 + React Three Fiber |
| Efeitos visuais | `@react-three/postprocessing` (Bloom) |
| Modelo facial | MediaPipe Canonical Face Model (468 vértices) |
| Build tool | Vite 5 |

---

## Licença

Open source. Sinta-se livre para modificar e distribuir.
