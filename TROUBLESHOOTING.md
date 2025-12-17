# 🔧 Troubleshooting - AssistenteOrion

## Problema: Wake Word não está sendo reconhecida

### Solução 1: Verifique o que está sendo reconhecido

Execute o assistente e observe os logs. Você verá algo como:

```
[DEBUG] ✅ Texto reconhecido: 'orio' (normalizado: 'orio')
```

Se você vê o texto sendo reconhecido, mas a wake word não ativa, adicione essa variação!

### Solução 2: Adicione novas variações fonéticas

Edite o arquivo `core/voice_listener.py` e adicione a variação na lista `wake_word_variations`:

```python
self.wake_word_variations = [
    "orion",
    "orio",
    "sua_variacao_aqui",  # Adicione aqui!
]
```

### Solução 3: Variações comuns já adicionadas

O assistente já aceita automaticamente:
- orion, órion, orio, ório
- orião, hórion, oriom
- o rion, o rio, oryon

Se alguma outra variação aparecer frequentemente, adicione-a!

## Problema: Comandos não estão sendo executados

### Verifique a similaridade

O assistente usa matching por similaridade. Se o comando não for reconhecido:

1. Veja o log: `[DEBUG] ✅ Comando capturado: 'xxxxx'`
2. Compare com os comandos em `commands/commands.json`
3. Ajuste o label para ficar mais próximo do que você fala

Exemplo:
- ❌ Label: "abrir navegador chrome"
- ❌ Você fala: "abrir chrome"
- ✅ Solução: Mudar label para "abrir chrome"

## Problema: Muito sensível ou pouco sensível

### Ajuste o threshold de similaridade

No arquivo `utils/command_executor.py`, linha ~66:

```python
def find_command(self, spoken_text: str, min_similarity: float = 0.6):
```

- **Mais flexível**: diminua para `0.4` ou `0.5`
- **Mais restritivo**: aumente para `0.7` ou `0.8`

## Problema: Microfone não está captando

### Teste o microfone

1. Verifique se está conectado
2. Teste em outras aplicações
3. Verifique o volume do microfone no Windows
4. Execute como administrador

### Ajuste o timeout

Se demora muito para captar, aumente o timeout no `core/voice_listener.py`:

```python
audio = self.recognizer.listen(
    source, 
    timeout=2,  # Aumente este valor
    phrase_time_limit=5
)
```

## Problema: Muito ruído ambiente

### Aumente o tempo de calibração

No arquivo `core/voice_listener.py`, método `_calibrate_microphone`:

```python
self.recognizer.adjust_for_ambient_noise(source, duration=3)  # Era 2, aumente para 3 ou 4
```

### Ajuste a energia mínima

No arquivo `core/voice_listener.py`, após calibração:

```python
self.recognizer.energy_threshold = 300  # Valor padrão é ~300
# Aumente para ambientes barulhentos (400-600)
# Diminua para ambientes silenciosos (100-200)
```

## Dicas Gerais

1. **Fale claramente** e com volume normal
2. **Evite sotaques fortes** na wake word
3. **Conexão com internet** é necessária (usa Google Speech API)
4. **Ambiente quieto** melhora significativamente o reconhecimento
5. **Distância do microfone**: 15-30cm é ideal

## Como adicionar seus próprios logs

Adicione prints em qualquer lugar do código para debug:

```python
print(f"[MEU DEBUG] Variável x = {x}")
```

Isso ajuda a entender o fluxo do programa!
