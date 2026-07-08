from __future__ import annotations

import os

from aiproject.desktop import create_desktop_window, start_server


def main() -> None:
    os.environ.setdefault("RETRIEVAL_MODE", "text")
    os.environ.setdefault("AI_MODEL_PROVIDER", "deepseek")
    os.environ.setdefault("DEEPSEEK_MODEL", "deepseek-chat")

    server, url = start_server()
    try:
        import webview

        window = create_desktop_window("Poro", url)
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
