# Changelog

Todas as mudanças relevantes deste fork em relação ao repositório original
([KevinAllysson/virtual-assistant-orion](https://github.com/KevinAllysson/virtual-assistant-orion)).

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

---

## [Unreleased] — fork Jarvis

### Added

#### Interface desktop (modo pet)
- `backend/desktop_window.py` — janela flutuante com **pywebview** (sem abrir navegador)
- `backend/static_server.py` — serve o build React em `localhost:4173`
- `backend/app_launcher.py` — backend em thread secundária; UI na thread principal
- Modo pet no frontend (`?mode=pet`): rosto 3D, status e bolha de fala (HUD simplificado)
- Estilos `.pet-mode` em `src/index.css`
- Flag `--browser` para forçar abertura no navegador (dev)

#### Empacotamento Windows
- `build.ps1` — script que instala deps, builda frontend e gera o `.exe`
- `jarvis.spec` — configuração PyInstaller (backend + `dist/` + pywebview)
- `backend/paths.py` — resolução de caminhos em dev vs executável
- `backend/requirements-build.txt` — PyInstaller para build
- Saída em `release/Jarvis/Jarvis.exe` (pasta inteira necessária para distribuir)
- Logs em `jarvis.log` ao lado do `.exe` (sem console visível)

#### Voz e wake word
- Wake word dinâmica: `oi {nome}` configurável na primeira execução
- `backend/utils/user_settings.py` — persistência em `user_settings.json`
- `listen_for_assistant_name()` — captura dedicada do nome (sem exigir wake word)
- Escuta automática em **standby** (sem botão para ativar)
- Detecção de **fim de fala** (`PAUSE_THRESHOLD`, `NON_SPEAKING_DURATION`)
- TTS de saudação ao detectar wake word (`SPEAK_WAKE_GREETING`)
- Setup com retentativas se o nome não for reconhecido

#### Comandos Spotify
- `backend/utils/spotify_actions.py` — ações via URI, teclas de mídia e volume
- Novos comandos em `commands.json`:
  - abrir spotify
  - play/pause, pular, faixa anterior
  - pesquisar no spotify `{query}`
  - tocar playlist `{nome}` / playlist por ID
  - aumentar/baixar volume em `{valor}`

#### WebSocket / frontend
- Evento `config` com `assistant_name`, `wake_word`, `configured`
- Estados `standby` e `processing` no HUD
- Nome e wake word dinâmicos em `useOrionSocket.js` e `App.jsx`

### Changed

- Projeto renomeado de **Orion** para **Jarvis** na UI e configuração
- `backend/main.py` — entry point com modos `--legacy`, `--with-ui`, `--browser`
- `backend/server.py` — loop de voz integrado; handlers de sinal só na thread principal
- `backend/core/voice_listener.py` — refatorado para wake word + fim de fala
- `backend/utils/command_executor.py` — placeholders `{valor}`, playlists, ações simbólicas
- `backend/config.py` — flags de TTS, modo pet, timeouts de setup
- `README.md` — documentação completa do fork (instalação, uso, build, troubleshooting)
- `index.html` — título atualizado para Jarvis

### Fixed

- Crash ao iniciar `.exe` (`signal only works in main thread`) no modo pet
- Nome do assistente salvo como `"jarvis"` quando o microfone não ouvia — agora só persiste nome válido
- Setup não repetia se a captura de voz falhasse na primeira execução

### Configuração padrão

| Opção | Valor | Efeito |
|---|---|---|
| `DESKTOP_PET_MODE` | `True` | Janela flutuante em vez de navegador |
| `SPEAK_ON_SUCCESS` | `False` | Sem TTS após comando OK |
| `SPEAK_ON_ERROR` | `False` | Sem TTS após erro |
| `SPEAK_WAKE_GREETING` | `True` | Responde ao `oi {nome}` |
| `USE_WAKE_WORD` | `True` | Escuta contínua em standby |

### Arquivos ignorados pelo Git (novos)

- `release/` — build PyInstaller
- `build/jarvis-work/`, `build/orion-work/`
- `user_settings.json`, `jarvis.log`

---

## [Base upstream] — commit `288ce00`

Estado inicial herdado do repositório original:

- Backend Python com WebSocket (`ws://localhost:8765`)
- Frontend React + Three.js (rosto 3D MediaPipe)
- Comandos básicos Windows (Chrome, Notepad, volume, desligar, etc.)
- Escuta manual via botão no HUD
- Wake word fixa `"Orion"` / modo sem wake word

---

## Como ler este changelog

- **Unreleased** = tudo que está na branch `feat/jarvis-desktop-assistant` e ainda não foi mergeada em `main`
- Após merge, renomeie `[Unreleased]` para a versão/tag correspondente
