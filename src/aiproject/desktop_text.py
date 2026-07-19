from __future__ import annotations

import os
import sys
import threading
import webbrowser

from aiproject.desktop import run_qt_desktop, start_server


def main() -> None:
    if "--poro-overlay" in sys.argv:
        from aiproject.desktop_overlay import main as overlay_main

        overlay_main()
        return

    os.environ.setdefault("RETRIEVAL_MODE", "text")
    os.environ.setdefault("AI_MODEL_PROVIDER", "deepseek")
    os.environ.setdefault("DEEPSEEK_MODEL", "deepseek-chat")

    server, url = start_server()
    try:
        run_qt_desktop("Poro", url)
    except Exception:
        webbrowser.open(url)
        threading.Event().wait()
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
