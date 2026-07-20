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
    from PySide6.QtCore import QObject, QPoint, Qt, QUrl, Slot
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import QMainWindow
    from PySide6.QtWebEngineWidgets import QWebEngineView

    COLLAPSED_SIZE = 64
    EXPANDED_WIDTH = 360
    EXPANDED_HEIGHT = 460

    class OverlayBridge(QObject):
        def __init__(self, window: QMainWindow) -> None:
            super().__init__(window)
            self.window = window
            self.expand_direction = "right"
            self.drag_mouse_start: QPoint | None = None
            self.drag_window_start: QPoint | None = None

        def _available_rect(self):
            screen = self.window.screen()
            if screen:
                return screen.availableGeometry()
            return None

        def _clamp_to_screen(self, point: QPoint, width: int, height: int) -> QPoint:
            rect = self._available_rect()
            if not rect:
                return point
            x = min(max(point.x(), rect.left()), rect.right() - width + 1)
            y = min(max(point.y(), rect.top()), rect.bottom() - height + 1)
            return QPoint(x, y)

        @Slot()
        def minimize(self) -> None:
            self.window.showMinimized()

        @Slot()
        def expand(self) -> None:
            self.expandTo("right")

        @Slot(str)
        def expandTo(self, direction: str) -> None:
            direction = "left" if direction == "left" else "right"
            if self.window.width() == EXPANDED_WIDTH and self.expand_direction == direction:
                return

            pos = self.window.pos()
            if direction == "left":
                pos = QPoint(pos.x() - (EXPANDED_WIDTH - self.window.width()), pos.y())
            self.expand_direction = direction
            pos = self._clamp_to_screen(pos, EXPANDED_WIDTH, EXPANDED_HEIGHT)
            self.window.setGeometry(pos.x(), pos.y(), EXPANDED_WIDTH, EXPANDED_HEIGHT)

        @Slot()
        def collapse(self) -> None:
            pos = self.window.pos()
            if self.expand_direction == "left":
                pos = QPoint(pos.x() + (self.window.width() - COLLAPSED_SIZE), pos.y())
            pos = self._clamp_to_screen(pos, COLLAPSED_SIZE, COLLAPSED_SIZE)
            self.window.setGeometry(pos.x(), pos.y(), COLLAPSED_SIZE, COLLAPSED_SIZE)

        @Slot(int, int)
        def startDrag(self, screen_x: int, screen_y: int) -> None:
            self.drag_mouse_start = QPoint(screen_x, screen_y)
            self.drag_window_start = self.window.pos()

        @Slot(int, int)
        def dragTo(self, screen_x: int, screen_y: int) -> None:
            if self.drag_mouse_start is None or self.drag_window_start is None:
                return
            delta = QPoint(screen_x, screen_y) - self.drag_mouse_start
            pos = self.drag_window_start + delta
            pos = self._clamp_to_screen(pos, self.window.width(), self.window.height())
            self.window.move(pos)

        @Slot()
        def endDrag(self) -> None:
            self.drag_mouse_start = None
            self.drag_window_start = None

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
    window.resize(COLLAPSED_SIZE, COLLAPSED_SIZE)
    window.setMinimumSize(COLLAPSED_SIZE, COLLAPSED_SIZE)

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
    stop_champion_watcher = threading.Event()
    champion_watcher = threading.Thread(
        target=_watch_champion_select,
        args=(stop_champion_watcher,),
        daemon=True,
    )
    champion_watcher.start()
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
        stop_champion_watcher.set()
        server.shutdown()


def _watch_champion_select(stop_event: threading.Event) -> None:
    from aiproject.lcu import watch_champ_select_champion

    watch_champ_select_champion(stop_event)


if __name__ == "__main__":
    main()
