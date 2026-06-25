"""
Servidor HTTP simples para a interface React empacotada.
"""

from __future__ import annotations

import threading
import time
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Tuple

FRONTEND_HOST = "localhost"
FRONTEND_PORT = 4173
FRONTEND_URL = f"http://{FRONTEND_HOST}:{FRONTEND_PORT}"


def start_static_server(directory: str, port: int = FRONTEND_PORT) -> Tuple[ThreadingHTTPServer, threading.Thread]:
    handler = partial(SimpleHTTPRequestHandler, directory=directory)
    httpd = ThreadingHTTPServer((FRONTEND_HOST, port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True, name="orion-frontend")
    thread.start()
    return httpd, thread


def open_browser(url: str = FRONTEND_URL, delay: float = 1.5) -> None:
    def _open() -> None:
        time.sleep(delay)
        webbrowser.open(url)

    threading.Thread(target=_open, daemon=True, name="orion-browser").start()
