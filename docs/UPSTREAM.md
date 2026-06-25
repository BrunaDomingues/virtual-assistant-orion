# Guia de upstream — fork Jarvis

Este repositório é um **fork** de:

| Remote | URL | Uso |
|---|---|---|
| `origin` | `https://github.com/BrunaDomingues/virtual-assistant-orion.git` | **Seu fork** — push, PRs, releases |
| `upstream` | `https://github.com/KevinAllysson/virtual-assistant-orion.git` | **Original** — só fetch/merge, nunca push |

---

## Remotes configurados

Verifique com:

```powershell
git remote -v
```

Saída esperada:

```
origin    https://github.com/BrunaDomingues/virtual-assistant-orion.git (fetch)
origin    https://github.com/BrunaDomingues/virtual-assistant-orion.git (push)
upstream  https://github.com/KevinAllysson/virtual-assistant-orion.git (fetch)
upstream  https://github.com/KevinAllysson/virtual-assistant-orion.git (push)
```

### Se `upstream` ainda não existir

```powershell
git remote add upstream https://github.com/KevinAllysson/virtual-assistant-orion.git
git fetch upstream
```

---

## Fluxo de trabalho recomendado

```
upstream/main  ──fetch──►  local/main  ──merge/rebase──►  feat/sua-branch  ──push──►  origin/feat/sua-branch
                                                                                              │
                                                                                              ▼
                                                                                        PR → origin/main
```

1. Trabalhe sempre em **branch de feature** (ex.: `feat/jarvis-desktop-assistant`)
2. Faça **push** para `origin` (seu fork)
3. Abra **PR** de `feat/...` → `main` no **seu fork**
4. Periodicamente, **sincronize** com `upstream` para pegar correções do original

---

## Sincronizar com o repositório original

### 1. Buscar atualizações do upstream

```powershell
git fetch upstream
```

### 2. Ver o que mudou no original (e você ainda não tem)

```powershell
git log --oneline main..upstream/main
```

Se não imprimir nada, seu `main` já está em dia com o upstream.

### 3. Atualizar seu `main` local

```powershell
git checkout main
git merge upstream/main
git push origin main
```

> Use `merge` (não `rebase`) no `main` se preferir histórico simples no fork.

### 4. Trazer upstream para sua branch de feature

```powershell
git checkout feat/jarvis-desktop-assistant
git merge main
# ou, se preferir histórico linear:
# git rebase main
git push origin feat/jarvis-desktop-assistant
```

---

## Comparar fork vs original

```powershell
# Arquivos diferentes entre upstream e sua branch
git diff --stat upstream/main...feat/jarvis-desktop-assistant

# Commits só no seu fork
git log --oneline upstream/main..feat/jarvis-desktop-assistant

# Commits só no original (você ainda não integrou)
git log --oneline feat/jarvis-desktop-assistant..upstream/main
```

---

## Abrir PR no seu fork

Branch já no GitHub:

**https://github.com/BrunaDomingues/virtual-assistant-orion/compare/main...feat/jarvis-desktop-assistant**

Ou via CLI (após `gh auth login`):

```powershell
gh pr create `
  --repo BrunaDomingues/virtual-assistant-orion `
  --base main `
  --head feat/jarvis-desktop-assistant `
  --title "Jarvis: assistente desktop com voz, Spotify e build Windows" `
  --body-file .github/pr-body.md
```

---

## Enviar contribuição de volta ao original (opcional)

Se quiser propor suas mudanças ao repo do KevinAllysson:

1. Garanta que `main` do upstream está mergeado na sua branch
2. Push para `origin`
3. No GitHub: **Compare & pull request** de `BrunaDomingues/virtual-assistant-orion` → `KevinAllysson/virtual-assistant-orion`

O mantenedor original decide se aceita o merge.

---

## Documentação das alterações

| Arquivo | Conteúdo |
|---|---|
| [README.md](../README.md) | Instalação, uso, comandos, build, troubleshooting |
| [CHANGELOG.md](../CHANGELOG.md) | Lista detalhada do que mudou vs upstream |
| Este arquivo | Remotes, sync e fluxo de PR |

---

## Estado atual (referência)

- **Branch de feature:** `feat/jarvis-desktop-assistant`
- **Commit principal:** transformação Orion → Jarvis (desktop, Spotify, build)
- **Upstream `main`:** alinhado com o `main` do fork na base (`288ce00`) — sem commits novos no original desde o fork
