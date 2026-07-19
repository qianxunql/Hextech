from __future__ import annotations

import os
import sys
import threading
import webbrowser

from aiproject.desktop import install_web_bridge, start_server


def _move_overlay_to_corner(window) -> None:
    from PySide6.QtWidgets import QApplication

    screen = QApplication.primaryScreen()
    if not screen:
        return
    rect = screen.availableGeometry()
    window.move(rect.right() - window.width() - 24, rect.top() + 120)


def create_overlay_window(url: str):
    from PySide6.QtCore import QObject, Qt, QUrl, Slot
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import QMainWindow
    from PySide6.QtWebEngineWidgets import QWebEngineView

    class OverlayBridge(QObject):
        def __init__(self, window: QMainWindow) -> None:
            super().__init__(window)
            self.window = window

        @Slot()
        def minimize(self) -> None:
            self.window.showMinimized()

        @Slot()
        def expand(self) -> None:
            self.window.resize(360, 460)

        @Slot()
        def collapse(self) -> None:
            self.window.resize(64, 64)

        @Slot()
        def close(self) -> None:
            self.window.close()

    window = QMainWindow()
    window.setWindowTitle("Poro Overlay")
    window.setWindowFlags(
        Qt.WindowType.FramelessWindowHint
        | Qt.WindowType.WindowStaysOnTopHint
        | Qt.WindowType.Tool
    )
    window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    window.resize(64, 64)
    window.setMinimumSize(64, 64)

    view = QWebEngineView(window)
    view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    view.page().setBackgroundColor(QColor(0, 0, 0, 0))
    window.setCentralWidget(view)
    install_web_bridge(view, OverlayBridge(window))
    view.load(QUrl(f"{url}/static/overlay.html"))
    _move_overlay_to_corner(window)
    return window


def main() -> None:
    os.environ.setdefault("RETRIEVAL_MODE", "text")
    os.environ.setdefault("AI_MODEL_PROVIDER", "deepseek")
    os.environ.setdefault("DEEPSEEK_MODEL", "deepseek-chat")

    server, url = start_server()
    try:
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance() or QApplication(sys.argv)
        window = create_overlay_window(url)
        window.show()
        app.exec()
    except Exception:
        webbrowser.open(f"{url}/static/overlay.html")
        threading.Event().wait()
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
