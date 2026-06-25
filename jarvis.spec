# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec para o Assistente Jarvis (backend + interface React).
Gere com: .\build.ps1
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

ROOT = Path(SPECPATH).resolve()
BACKEND = ROOT / "backend"
DIST_FRONTEND = ROOT / "dist"

edge_datas, edge_binaries, edge_hidden = collect_all("edge_tts")
webview_datas, webview_binaries, webview_hidden = collect_all("webview")

a = Analysis(
    [str(BACKEND / "main.py")],
    pathex=[str(BACKEND)],
    binaries=edge_binaries + webview_binaries,
    datas=[
        (str(BACKEND / "commands" / "commands.json"), "commands"),
        (str(DIST_FRONTEND), "frontend"),
    ] + edge_datas + webview_datas,
    hiddenimports=[
        "pygame",
        "pygame.mixer",
        "websockets",
        "websockets.asyncio",
        "websockets.asyncio.server",
        "websockets.legacy",
        "websockets.legacy.server",
        "sounddevice",
        "speech_recognition",
        "edge_tts",
        "aiohttp",
        "certifi",
        "webview",
        "paths",
        "static_server",
        "desktop_window",
        "app_launcher",
        "server",
        "core.voice_listener",
        "core.speaker",
        "core.sd_microphone",
        "utils.command_executor",
        "utils.spotify_actions",
        "utils.user_settings",
    ] + edge_hidden + webview_hidden + collect_submodules("edge_tts"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Jarvis",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Jarvis",
)
