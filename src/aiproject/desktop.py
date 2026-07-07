from __future__ import annotations

import os
import threading
import webbrowser
from http.server import ThreadingHTTPServer

from aiproject.web import HOST, HextechRequestHandler, app_dir


def start_server() -> tuple[ThreadingHTTPServer, str]:
    os.chdir(app_dir())
    os.environ.setdefault("AI_MODEL_PROVIDER", "deepseek")
    os.environ.setdefault("DEEPSEEK_MODEL", "deepseek-chat")

    server = ThreadingHTTPServer((HOST, 0), HextechRequestHandler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://{host}:{port}"


def main() -> None:
    server, url = start_server()
    try:
        import webview

        window = webview.create_window("Poro", url, width=1190, height=900, min_size=(860, 680))
        webview.start()
        if window:
            server.shutdown()
    except Exception:
        webbrowser.open(url)
        threading.Event().wait()


if __name__ == "__main__":
    main()
