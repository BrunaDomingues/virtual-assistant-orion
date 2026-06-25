## Summary

Transforma o assistente Orion em **Jarvis** com janela desktop flutuante, wake word personalizada, comandos Spotify e build Windows.

Documentação completa em [CHANGELOG.md](../CHANGELOG.md) e [docs/UPSTREAM.md](../docs/UPSTREAM.md).

### Principais mudanças

- Janela pet (pywebview) — sem navegador e sem terminal no `.exe`
- Wake word `oi {nome}` com setup na 1ª execução
- Escuta automática em standby + detecção de fim de fala
- Comandos Spotify (play, pause, buscar, playlist, volume)
- `build.ps1` → `release/Jarvis/Jarvis.exe`
- README, CHANGELOG e guia de upstream

## Test plan

- [ ] `py -m pip install -r backend/requirements.txt` e `npm install`
- [ ] `npm run build` + `py main.py --with-ui` — janela pet e wake word
- [ ] Apagar `user_settings.json` e testar pergunta do nome
- [ ] Comandos Spotify e Windows em `commands.json`
- [ ] `.\build.ps1` → `release\Jarvis\Jarvis.exe` (só interface)
- [ ] `git remote -v` mostra `origin` + `upstream`
