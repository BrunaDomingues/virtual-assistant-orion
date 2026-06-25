import threading
import time


def should_show_ui(is_frozen, argv) -> bool:
    return is_frozen() or "--with-ui" in argv or "--browser" in argv


def use_browser_ui(argv) -> bool:
    return "--browser" in argv


def run_with_desktop_pet(start_ui_fn, run_server_fn) -> None:
    """Backend em thread; janela pet bloqueia a thread principal."""
    server_error = []

    def _run_server() -> None:
        try:
            run_server_fn()
        except Exception as exc:
            server_error.append(exc)

    thread = threading.Thread(target=_run_server, daemon=True, name="jarvis-backend")
    thread.start()
    time.sleep(1.2)

    if server_error:
        err = server_error[0]
        print(f"\nERRO no backend: {err}")
        raise err

    start_ui_fn()
