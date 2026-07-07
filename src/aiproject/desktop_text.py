from __future__ import annotations

import os

from aiproject.desktop import start_server


def main() -> None:
    os.environ.setdefault("RETRIEVAL_MODE", "text")
    os.environ.setdefault("AI_MODEL_PROVIDER", "deepseek")
    os.environ.setdefault("DEEPSEEK_MODEL", "deepseek-chat")

    server, url = start_server()
    try:
        import webview

        window = webview.create_window("Hextech 内置索引版", url, width=1190, height=900, min_size=(860, 680))
        webview.start()
        if window:
            server.shutdown()
    except Exception:
        import threading
        import webbrowser

        webbrowser.open(url)
        threading.Event().wait()


if __name__ == "__main__":
    main()
