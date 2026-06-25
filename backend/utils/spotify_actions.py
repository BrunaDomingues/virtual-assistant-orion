"""
Controles do Spotify no Windows via URI scheme e teclas de mídia globais.
"""

from __future__ import annotations

import ctypes
import subprocess
import urllib.parse

VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_VOLUME_UP = 0xAF
VK_VOLUME_DOWN = 0xAE

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002


def _press_media_key(vk_code: int) -> None:
    user32 = ctypes.windll.user32
    user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
    user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)


def open_spotify() -> bool:
    subprocess.Popen('start "" "spotify:"', shell=True)
    return True


def _open_uri(uri: str) -> bool:
    subprocess.Popen(f'start "" "{uri}"', shell=True)
    return True


def search_spotify(query: str) -> bool:
    query = query.strip()
    if not query:
        return False
    encoded = urllib.parse.quote(query)
    return _open_uri(f"spotify:search:{encoded}")


def search_playlist(name: str) -> bool:
    """Busca uma playlist pelo nome (abre resultados no Spotify)."""
    name = name.strip()
    if not name:
        return False
    return search_spotify(f"playlist {name}")


def play_playlist(playlist_id: str) -> bool:
    """
    Reproduz uma playlist pelo ID do Spotify.
    Ex.: 37i9dQZF1DXcBWIGoYBM5M ou spotify:playlist:37i9dQZF1DXcBWIGoYBM5M
    """
    playlist_id = playlist_id.strip()
    if not playlist_id:
        return False

    if playlist_id.startswith("spotify:playlist:"):
        uri = playlist_id
    elif "open.spotify.com/playlist/" in playlist_id:
        pid = playlist_id.rsplit("/", 1)[-1].split("?")[0]
        uri = f"spotify:playlist:{pid}"
    else:
        uri = f"spotify:playlist:{playlist_id}"

    return _open_uri(uri)


def next_track() -> bool:
    _press_media_key(VK_MEDIA_NEXT_TRACK)
    return True


def previous_track() -> bool:
    _press_media_key(VK_MEDIA_PREV_TRACK)
    return True


def play_pause() -> bool:
    _press_media_key(VK_MEDIA_PLAY_PAUSE)
    return True


def play_current() -> bool:
    """Retoma a reprodução (tecla play/pause do Windows)."""
    _press_media_key(VK_MEDIA_PLAY_PAUSE)
    return True


def volume_up(steps: int = 3) -> bool:
    steps = max(1, min(int(steps), 30))
    for _ in range(steps):
        _press_media_key(VK_VOLUME_UP)
    return True


def volume_down(steps: int = 3) -> bool:
    steps = max(1, min(int(steps), 30))
    for _ in range(steps):
        _press_media_key(VK_VOLUME_DOWN)
    return True


def extract_search_query(spoken_text: str, prefixes: list[str]) -> str | None:
    """
    Extrai o termo de busca de frases como:
      - "pesquisar no spotify coldplay"
      - "buscar bohemian rhapsody no spotify"
      - "tocar no spotify rock nacional"
    """
    text = spoken_text.lower().strip()
    if not text:
        return None

    suffix = " no spotify"

    for prefix in sorted(prefixes, key=len, reverse=True):
        p = prefix.lower().strip()
        if not p:
            continue

        if text.startswith(p):
            query = text[len(p):].strip(" ,")
            if query and query != "no spotify":
                return query

        stem = p.replace(suffix, "").strip()
        if stem and text.startswith(stem) and text.endswith(suffix):
            query = text[len(stem): -len(suffix)].strip(" ,")
            if query:
                return query

    return None


SPOTIFY_ACTIONS = {
    "spotify_open": open_spotify,
    "spotify_search": search_spotify,
    "spotify_playlist": play_playlist,
    "spotify_playlist_search": search_playlist,
    "spotify_play_current": play_current,
    "spotify_volume_up": volume_up,
    "spotify_volume_down": volume_down,
    "spotify_next": next_track,
    "spotify_previous": previous_track,
    "spotify_play_pause": play_pause,
}
