from __future__ import annotations

import os
import subprocess
import sys
import threading
import webbrowser
from http.server import ThreadingHTTPServer
from typing import Callable

from aiproject.web import HOST, HextechRequestHandler, app_dir


WEBCHANNEL_BOOTSTRAP = r"""
(function () {
  if (window.__poroQtBridgeReady) return;
  window.__poroQtBridgeReady = true;

  function attachBridge() {
    if (!window.qt || !window.QWebChannel) return;
    new QWebChannel(window.qt.webChannelTransport, function (channel) {
      window.poroNative = { api: channel.objects.poroBridge };
    });
  }

  if (window.QWebChannel) {
    attachBridge();
    return;
  }

  var script = document.createElement("script");
  script.src = "qrc:///qtwebchannel/qwebchannel.js";
  script.onload = attachBridge;
  document.head.appendChild(script);
})();
"""


def start_server() -> tuple[ThreadingHTTPServer, str]:
    os.chdir(app_dir())
    os.environ.setdefault("AI_MODEL_PROVIDER", "deepseek")
    os.environ.setdefault("DEEPSEEK_MODEL", "deepseek-chat")

    server = ThreadingHTTPServer((HOST, 0), HextechRequestHandler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://{host}:{port}"


def overlay_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, "--poro-overlay"]
    return [sys.executable, "-m", "aiproject.desktop_overlay"]


class OverlayProcessController:
    def __init__(self, interval_seconds: float = 2.0) -> None:
        self.interval_seconds = interval_seconds
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.process: subprocess.Popen | None = None
        self.thread = threading.Thread(target=self._watch, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        self._stop_overlay()
        if self.thread.is_alive():
            self.thread.join(timeout=3)

    def _start_overlay(self) -> None:
        with self.lock:
            if self.process and self.process.poll() is None:
                return
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            self.process = subprocess.Popen(overlay_command(), creationflags=creationflags)

    def _stop_overlay(self) -> None:
        with self.lock:
            process = self.process
            self.process = None
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()

    def _watch(self) -> None:
        from aiproject.lcu import get_gameflow_phase

        while not self.stop_event.is_set():
            try:
                phase = get_gameflow_phase()
                should_show = phase in {"ChampSelect", "InProgress"}
                with self.lock:
                    is_running = self.process is not None and self.process.poll() is None
                if should_show and not is_running:
                    self._start_overlay()
                elif not should_show and is_running:
                    self._stop_overlay()
            except Exception:
                pass
            self.stop_event.wait(self.interval_seconds)

        self._stop_overlay()


def start_overlay_phase_watcher(interval_seconds: float = 2.0) -> OverlayProcessController:
    controller = OverlayProcessController(interval_seconds)
    controller.start()
    return controller


def _set_app_icon(app, window) -> None:
    from PySide6.QtGui import QIcon

    icon_path = os.path.join(app_dir(), "assets", "poro.ico")
    if os.path.exists(icon_path):
        icon = QIcon(icon_path)
        app.setWindowIcon(icon)
        window.setWindowIcon(icon)


def install_web_bridge(view, bridge) -> None:
    from PySide6.QtWebChannel import QWebChannel

    channel = QWebChannel(view.page())
    channel.registerObject("poroBridge", bridge)
    view.page().setWebChannel(channel)
    view.loadFinished.connect(lambda _ok: view.page().runJavaScript(WEBCHANNEL_BOOTSTRAP))


def create_desktop_window(title: str, url: str, on_close: Callable[[], None] | None = None):
    from PySide6.QtCore import QObject, QUrl, Slot
    from PySide6.QtWidgets import QMainWindow
    from PySide6.QtWebEngineWidgets import QWebEngineView

    class DesktopBridge(QObject):
        def __init__(self, window: QMainWindow) -> None:
            super().__init__(window)
            self.window = window

        @Slot()
        def minimize(self) -> None:
            self.window.showMinimized()

        @Slot()
        def toggle_maximize(self) -> None:
            if self.window.isMaximized():
                self.window.showNormal()
            else:
                self.window.showMaximized()

        @Slot()
        def close(self) -> None:
            self.window.close()

    class DesktopWindow(QMainWindow):
        def closeEvent(self, event) -> None:
            if on_close:
                on_close()
            super().closeEvent(event)

    window = DesktopWindow()
    window.setWindowTitle(title)
    window.resize(1190, 900)
    window.setMinimumSize(860, 680)

    view = QWebEngineView(window)
    window.setCentralWidget(view)
    install_web_bridge(view, DesktopBridge(window))
    view.load(QUrl(url))
    return window


def run_qt_desktop(title: str, url: str, enable_overlay: bool = True) -> int:
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    overlay_controller = None

    def stop_overlay() -> None:
        if overlay_controller:
            overlay_controller.stop()

    window = create_desktop_window(title, url, on_close=stop_overlay)
    _set_app_icon(app, window)
    window.show()

    if enable_overlay:
        overlay_controller = start_overlay_phase_watcher()

    exit_code = app.exec()
    stop_overlay()
    return exit_code


def main() -> None:
    if "--poro-overlay" in sys.argv:
        from aiproject.desktop_overlay import main as overlay_main

        overlay_main()
        return

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
