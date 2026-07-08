from __future__ import annotations

import os
import threading
import webbrowser
from http.server import ThreadingHTTPServer

from aiproject.web import HOST, HextechRequestHandler, app_dir


class WindowApi:
    def __init__(self) -> None:
        self.window = None

    def bind(self, window) -> None:
        self.window = window

    def minimize(self) -> None:
        if self.window:
            self.window.minimize()

    def toggle_maximize(self) -> None:
        if not self.window:
            return
        if getattr(self.window, "state", None) == "maximized":
            self.window.restore()
        else:
            self.window.maximize()

    def close(self) -> None:
        if self.window:
            self.window.destroy()


def start_server() -> tuple[ThreadingHTTPServer, str]:
    os.chdir(app_dir())
    os.environ.setdefault("AI_MODEL_PROVIDER", "deepseek")
    os.environ.setdefault("DEEPSEEK_MODEL", "deepseek-chat")

    server = ThreadingHTTPServer((HOST, 0), HextechRequestHandler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://{host}:{port}"


def create_desktop_window(title: str, url: str):
    import webview

    api = WindowApi()
    window = webview.create_window(
        title,
        url,
        js_api=api,
        width=1190,
        height=900,
        min_size=(860, 680),
        frameless=True,
        easy_drag=True,
    )
    api.bind(window)
    return window


def main() -> None:
    server, url = start_server()
    try:
        import webview

        window = create_desktop_window("Poro", url)
        webview.start()
        if window:
            server.shutdown()
    except Exception:
        webbrowser.open(url)
        threading.Event().wait()


if __name__ == "__main__":
    main()
