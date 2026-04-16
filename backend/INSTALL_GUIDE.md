# 🔧 Guia de Instalação - AssistenteOrion

## Problema com PyAudio no Windows

O erro que você está vendo é comum no Windows. O PyAudio precisa de componentes compilados em C++.

## ✅ Soluções (escolha uma)

### **Solução 1: Usar arquivo .whl pré-compilado (RECOMENDADO)**

Esta é a forma mais simples e rápida:

1. **Baixe o arquivo .whl apropriado para sua versão do Python:**
   
   Acesse: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
   
   Ou use este link direto para Python 3.13:
   - Para 64-bit: `PyAudio‑0.2.11‑cp313‑cp313‑win_amd64.whl`
   - Para 32-bit: `PyAudio‑0.2.11‑cp313‑cp313‑win32.whl`

2. **Instale o arquivo baixado:**
   ```bash
   pip install caminho\para\o\arquivo\PyAudio-0.2.11-cp313-cp313-win_amd64.whl
   ```

3. **Depois instale a outra dependência:**
   ```bash
   pip install speechrecognition==3.10.0
   ```

### **Solução 2: Usar pipwin**

```bash
pip install pipwin
pipwin install pyaudio
pip install speechrecognition==3.10.0
```

### **Solução 3: Instalar Visual C++ Build Tools**

Se preferir compilar do zero:

1. Baixe o instalador: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Execute e selecione "Desktop development with C++"
3. Instale (pode demorar bastante - ~6GB)
4. Depois execute:
   ```bash
   pip install -r requirements.txt
   ```

### **Solução 4: Usar versão alternativa sem PyAudio**

Podemos usar `sounddevice` + `soundfile` ao invés de `pyaudio`:

```bash
pip install speechrecognition==3.10.0
pip install sounddevice
pip install soundfile
```

## 🎯 Verificar sua versão do Python

Para saber qual arquivo .whl baixar, execute:

```bash
python --version
python -c "import struct; print('64-bit' if struct.calcsize('P') * 8 == 64 else '32-bit')"
```

## 📝 Após resolver o PyAudio

Execute o assistente:
```bash
python main.py
```

## ❓ Ainda com problemas?

Se nenhuma solução funcionar, me avise qual você tentou e qual foi o erro!
