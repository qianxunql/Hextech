from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from urllib.parse import urlparse

from aiproject.main import run


HOST = "127.0.0.1"
PORT = 8765


HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Hextech</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #ffffff;
      --panel: #f3f3f3;
      --text: #151515;
      --muted: #8e8e8e;
      --line: #eeeeee;
      --button: #ffffff;
      --button-disabled: #dddddd;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: "Segoe UI", "Microsoft YaHei UI", Arial, sans-serif;
      letter-spacing: 0;
    }

    .app {
      min-height: 100vh;
      display: grid;
      grid-template-rows: 56px 1fr auto;
    }

    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 26px 0 10px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 18px;
      font-weight: 500;
    }

    .brand-icon {
      width: 42px;
      height: 42px;
      border-radius: 10px;
      position: relative;
      overflow: hidden;
      flex: 0 0 auto;
      background:
        radial-gradient(circle at 24px 8px, rgba(255, 255, 255, 0.9) 0 6px, transparent 7px),
        linear-gradient(135deg, #22135f 0%, #5033c8 42%, #00b9ff 72%, #0b123f 100%);
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.25);
    }

    .brand-icon::before,
    .brand-icon::after {
      content: "";
      position: absolute;
      top: 14px;
      width: 15px;
      height: 12px;
      border-radius: 55% 55% 45% 45%;
      background: #f6e8ff;
      transform: rotate(-24deg);
      box-shadow: inset 0 -2px 0 rgba(112, 45, 126, 0.35);
    }

    .brand-icon::before { left: 1px; }
    .brand-icon::after {
      right: 1px;
      transform: rotate(24deg);
    }

    .poro {
      position: absolute;
      left: 4px;
      right: 4px;
      bottom: 1px;
      height: 26px;
      border-radius: 48% 48% 42% 42%;
      background: #ffffff;
      box-shadow: 0 -4px 10px rgba(255, 255, 255, 0.45);
    }

    .poro::before,
    .poro::after {
      content: "";
      position: absolute;
      top: 8px;
      width: 5px;
      height: 7px;
      border-radius: 50%;
      background: #111111;
    }

    .poro::before { left: 10px; }
    .poro::after { right: 10px; }

    .poro-gem {
      position: absolute;
      top: 2px;
      left: 15px;
      width: 12px;
      height: 12px;
      border-radius: 3px;
      background: linear-gradient(135deg, #d9b5ff, #7d35d7);
      transform: rotate(45deg);
      box-shadow: 0 0 8px rgba(201, 137, 255, 0.95);
      z-index: 2;
    }

    .poro-tongue {
      position: absolute;
      left: 17px;
      bottom: -2px;
      width: 10px;
      height: 12px;
      border-radius: 7px 7px 8px 8px;
      background: #e95a83;
      z-index: 3;
    }

    .window-actions {
      display: flex;
      gap: 34px;
      color: #111;
      font-size: 25px;
      line-height: 1;
      user-select: none;
    }

    .settings-trigger {
      position: fixed;
      left: 28px;
      bottom: 28px;
      z-index: 10;
      width: 34px;
      height: 34px;
      border: 0;
      border-radius: 50%;
      background: transparent;
      color: #777777;
      font-size: 27px;
      line-height: 34px;
      padding: 0;
      cursor: pointer;
    }

    .settings-trigger:hover {
      background: #f4f4f4;
      color: #333333;
    }

    .settings-backdrop {
      position: fixed;
      inset: 0;
      display: none;
      align-items: flex-end;
      justify-content: flex-start;
      padding: 0 0 76px 28px;
      background: rgba(255, 255, 255, 0.2);
      z-index: 20;
    }

    .settings-backdrop.open {
      display: flex;
    }

    .settings-panel {
      width: 320px;
      background: #ffffff;
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: 0 18px 60px rgba(0, 0, 0, 0.14);
      padding: 18px;
    }

    .settings-title {
      margin: 0 0 14px;
      font-size: 16px;
      font-weight: 600;
    }

    .setting-field {
      display: grid;
      gap: 8px;
      margin-top: 12px;
    }

    .setting-label {
      color: #4b4b4b;
      font-size: 13px;
      font-weight: 600;
    }

    .api-key-input {
      width: 100%;
      height: 44px;
      padding: 0 12px;
      border: 1px solid var(--line);
      border-radius: 12px;
      background: #ffffff;
      color: var(--text);
      font: 14px "Segoe UI", "Microsoft YaHei UI", Arial, sans-serif;
    }

    .api-key-input:focus {
      border-color: #111111;
      outline: none;
    }

    .save-settings {
      width: 100%;
      height: 42px;
      margin-top: 14px;
      border-radius: 12px;
      background: #111111;
      color: #ffffff;
      font-size: 14px;
      cursor: pointer;
    }

    .settings-note {
      margin: 10px 0 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.4;
    }

    main {
      display: flex;
      align-items: stretch;
      justify-content: center;
      padding: 36px 48px 8px;
      min-height: 0;
    }

    .conversation {
      width: min(1088px, 100%);
      display: flex;
      flex-direction: column;
      justify-content: center;
      min-height: 0;
    }

    .empty {
      margin: auto;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 20px;
      color: #0d0d0d;
    }

    .poro-line {
      width: 88px;
      height: 72px;
      position: relative;
    }

    .poro-line::before,
    .poro-line::after {
      content: "";
      position: absolute;
      top: 18px;
      width: 22px;
      height: 16px;
      border: 4px solid #0d0d0d;
      border-radius: 60% 45% 60% 45%;
      background: var(--bg);
      transform: rotate(-28deg);
    }

    .poro-line::before { left: 1px; }
    .poro-line::after {
      right: 1px;
      transform: rotate(28deg) scaleX(-1);
    }

    .poro-head {
      position: absolute;
      left: 18px;
      top: 14px;
      width: 52px;
      height: 44px;
      border: 5px solid #0d0d0d;
      border-radius: 45% 45% 52% 52%;
      background: var(--bg);
    }

    .poro-head::before,
    .poro-head::after {
      content: "";
      position: absolute;
      top: 16px;
      width: 6px;
      height: 8px;
      border-radius: 50%;
      background: #0d0d0d;
    }

    .poro-head::before { left: 12px; }
    .poro-head::after { right: 12px; }

    .poro-line-gem {
      position: absolute;
      left: 36px;
      top: 1px;
      width: 16px;
      height: 16px;
      border: 4px solid #0d0d0d;
      transform: rotate(45deg);
      background: var(--bg);
      z-index: 2;
    }

    .poro-line-tongue {
      position: absolute;
      left: 37px;
      top: 48px;
      width: 14px;
      height: 18px;
      border: 4px solid #0d0d0d;
      border-top: 0;
      border-radius: 0 0 10px 10px;
      background: var(--bg);
    }

    .messages {
      display: none;
      flex-direction: column;
      gap: 18px;
      overflow: auto;
      padding: 16px 10px 24px;
      min-height: 0;
      height: 100%;
    }

    .message {
      width: min(880px, 100%);
      line-height: 1.8;
      font-size: 16px;
      white-space: pre-wrap;
    }

    .message.user {
      align-self: flex-end;
      width: auto;
      max-width: min(760px, 90%);
      background: var(--panel);
      border-radius: 22px;
      padding: 12px 18px;
    }

    .message.assistant {
      align-self: flex-start;
      padding: 4px 2px;
    }

    .composer-wrap {
      padding: 8px 48px 48px;
      display: flex;
      justify-content: center;
    }

    .composer {
      width: min(1092px, 100%);
      min-height: 146px;
      background: var(--panel);
      border-radius: 34px;
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 14px;
      padding: 24px 16px 12px 30px;
    }

    textarea {
      resize: none;
      border: 0;
      outline: 0;
      background: transparent;
      color: var(--text);
      font: 25px "Segoe UI", "Microsoft YaHei UI", Arial, sans-serif;
      line-height: 1.4;
      min-width: 0;
      height: 76px;
      padding: 0;
    }

    textarea::placeholder { color: #9b9b9b; opacity: 1; }

    .controls {
      align-self: end;
      display: flex;
      align-items: center;
      gap: 10px;
      padding-bottom: 0;
    }

    button,
    select {
      border: 0;
      outline: 0;
      height: 56px;
      background: var(--button);
      color: #202020;
      font: 24px "Segoe UI", "Microsoft YaHei UI", Arial, sans-serif;
    }

    .upload-button {
      width: 56px;
      border-radius: 50%;
      color: #777777;
      cursor: pointer;
    }

    select {
      appearance: none;
      border-radius: 28px;
      padding: 0 48px 0 22px;
      background-image:
        linear-gradient(45deg, transparent 50%, #666 50%),
        linear-gradient(135deg, #666 50%, transparent 50%);
      background-position:
        calc(100% - 24px) 26px,
        calc(100% - 17px) 26px;
      background-size: 7px 7px;
      background-repeat: no-repeat;
      font-size: 24px;
    }

    .send {
      width: 56px;
      border-radius: 50%;
      background: var(--button-disabled);
      color: #ffffff;
      cursor: pointer;
    }

    .send.ready {
      background: #111111;
    }

    .send:disabled {
      cursor: wait;
      opacity: 0.55;
    }

    @media (max-width: 760px) {
      .settings-trigger { left: 18px; bottom: 18px; }
      main { padding: 18px 18px 4px; }
      .composer-wrap { padding: 8px 16px 22px; }
      .composer {
        grid-template-columns: 1fr;
        min-height: 180px;
        padding: 22px;
      }
      textarea { font-size: 20px; }
      .controls { justify-content: flex-end; }
      select { max-width: 160px; font-size: 19px; }
    }
  </style>
</head>
<body>
  <div class="app">
    <header>
      <div class="brand">
        <span class="brand-icon" aria-hidden="true">
          <span class="poro-gem"></span>
          <span class="poro"><span class="poro-tongue"></span></span>
        </span>
        <span>Hextech</span>
      </div>
      <div class="window-actions"><span>−</span><span>□</span><span>×</span></div>
    </header>

    <button class="settings-trigger" id="settingsButton" type="button" title="设置" aria-label="设置">⚙</button>

    <div class="settings-backdrop" id="settingsBackdrop">
      <section class="settings-panel" role="dialog" aria-modal="true" aria-labelledby="settingsTitle">
        <h2 class="settings-title" id="settingsTitle">设置</h2>
        <label class="setting-field">
          <span class="setting-label">DeepSeek API Key</span>
          <input class="api-key-input" id="apiKeyInput" type="password" placeholder="sk-..." autocomplete="off" />
        </label>
        <button class="save-settings" id="saveSettings" type="button">保存 API Key</button>
        <p class="settings-note" id="settingsNote">API Key 会保存到项目根目录的 .env 文件。</p>
      </section>
    </div>

    <main>
      <section class="conversation">
        <div class="empty" id="empty">
          <div class="poro-line" aria-hidden="true">
            <div class="poro-line-gem"></div>
            <div class="poro-head"></div>
            <div class="poro-line-tongue"></div>
          </div>
        </div>
        <div class="messages" id="messages"></div>
      </section>
    </main>

    <section class="composer-wrap">
      <form class="composer" id="form">
        <textarea id="question" placeholder="Send a message" autocomplete="off"></textarea>
        <div class="controls">
          <button class="upload-button" type="button" title="上传">⇧</button>
          <select id="modelSelect" aria-label="模型">
            <option value="cloud">deepseek-chat</option>
            <option value="local">qwen3:4b</option>
          </select>
          <button class="send" id="send" type="submit" title="发送">↑</button>
        </div>
      </form>
    </section>
  </div>

  <script>
    const form = document.querySelector("#form");
    const input = document.querySelector("#question");
    const send = document.querySelector("#send");
    const empty = document.querySelector("#empty");
    const messages = document.querySelector("#messages");
    const settingsButton = document.querySelector("#settingsButton");
    const settingsBackdrop = document.querySelector("#settingsBackdrop");
    const modelSelect = document.querySelector("#modelSelect");
    const apiKeyInput = document.querySelector("#apiKeyInput");
    const saveSettings = document.querySelector("#saveSettings");
    const settingsNote = document.querySelector("#settingsNote");

    const MODEL_CONFIGS = {
      cloud: { provider: "deepseek", model: "deepseek-chat", label: "deepseek-chat" },
      local: { provider: "ollama", model: "qwen3:4b", label: "qwen3:4b" },
    };

    function currentMode() {
      return modelSelect.value || localStorage.getItem("hextech:modelMode") || "cloud";
    }

    function applyModelMode(mode) {
      const nextMode = MODEL_CONFIGS[mode] ? mode : "cloud";
      localStorage.setItem("hextech:modelMode", nextMode);
      modelSelect.value = nextMode;
    }

    async function loadSettings() {
      try {
        const response = await fetch("/api/settings");
        const data = await response.json();
        apiKeyInput.value = "";
        apiKeyInput.placeholder = data.hasDeepseekApiKey ? "已保存，输入新 Key 可覆盖" : "sk-...";
      } catch {
        settingsNote.textContent = "读取设置失败。";
      }
    }

    async function saveApiKey() {
      saveSettings.disabled = true;
      settingsNote.textContent = "正在保存...";
      try {
        const response = await fetch("/api/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ deepseekApiKey: apiKeyInput.value.trim() }),
        });
        const data = await response.json();
        settingsNote.textContent = data.ok ? "已保存到 .env。" : "保存失败。";
      } catch (error) {
        settingsNote.textContent = `保存失败：${error}`;
      } finally {
        saveSettings.disabled = false;
      }
    }

    function setReady() {
      send.classList.toggle("ready", input.value.trim().length > 0);
    }

    function showMessages() {
      empty.style.display = "none";
      messages.style.display = "flex";
    }

    function addMessage(role, text) {
      showMessages();
      const node = document.createElement("div");
      node.className = `message ${role}`;
      node.textContent = text;
      messages.appendChild(node);
      messages.scrollTop = messages.scrollHeight;
      return node;
    }

    input.addEventListener("input", setReady);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
      }
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const question = input.value.trim();
      if (!question || send.disabled) return;

      input.value = "";
      setReady();
      addMessage("user", question);
      const pending = addMessage("assistant", "正在检索知识库并思考...");
      send.disabled = true;

      try {
        const response = await fetch("/api/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question, modelMode: currentMode() }),
        });
        const data = await response.json();
        pending.textContent = data.answer || "没有得到回答。";
      } catch (error) {
        pending.textContent = `出错了：${error}`;
      } finally {
        send.disabled = false;
        input.focus();
      }
    });

    settingsButton.addEventListener("click", () => {
      settingsBackdrop.classList.add("open");
      loadSettings();
    });

    settingsBackdrop.addEventListener("click", (event) => {
      if (event.target === settingsBackdrop) {
        settingsBackdrop.classList.remove("open");
      }
    });

    modelSelect.addEventListener("change", () => {
      applyModelMode(modelSelect.value);
    });

    saveSettings.addEventListener("click", saveApiKey);

    applyModelMode(currentMode());
    input.focus();
    setReady();
  </script>
</body>
</html>
"""


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        bundle_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        if (bundle_dir / "data").exists():
            return bundle_dir
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def model_overrides(model_mode: str) -> dict[str, str]:
    if model_mode == "local":
        return {"model_provider": "ollama", "ollama_model": "qwen3:4b"}
    return {"model_provider": "deepseek", "deepseek_model": "deepseek-chat"}


def read_env_value(key: str, path: str = ".env") -> str:
    env_path = Path(path)
    if not env_path.exists():
        return ""
    for raw_line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        env_key, value = line.split("=", 1)
        if env_key.strip() == key:
            return value.strip().strip('"').strip("'")
    return ""


def write_env_value(key: str, value: str, path: str = ".env") -> None:
    env_path = Path(path)
    lines = env_path.read_text(encoding="utf-8", errors="replace").splitlines() if env_path.exists() else []
    updated = False
    next_lines: list[str] = []
    for raw_line in lines:
        if raw_line.strip().startswith("#") or "=" not in raw_line:
            next_lines.append(raw_line)
            continue
        env_key, _ = raw_line.split("=", 1)
        if env_key.strip() == key:
            next_lines.append(f"{key}={value}")
            updated = True
        else:
            next_lines.append(raw_line)
    if not updated:
        next_lines.append(f"{key}={value}")
    env_path.write_text("\n".join(next_lines) + "\n", encoding="utf-8")
    os.environ[key] = value


class HextechRequestHandler(BaseHTTPRequestHandler):
    server_version = "HextechWeb/0.1"

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            self._send_text(HTML, "text/html; charset=utf-8")
            return
        if path == "/health":
            self._send_json({"ok": True})
            return
        if path == "/api/settings":
            self._send_json({"hasDeepseekApiKey": bool(read_env_value("DEEPSEEK_API_KEY"))})
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/settings":
            self._handle_settings_post()
            return

        if path != "/api/ask":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
            question = str(payload.get("question", "")).strip()
            if not question:
                raise ValueError("question is required")
            model_mode = str(payload.get("modelMode", "cloud")).strip().lower()
            answer = run(question, overrides=model_overrides(model_mode))
            self._send_json({"answer": answer})
        except Exception as exc:  # noqa: BLE001 - returned to local UI
            self._send_json({"error": str(exc), "answer": f"出错了：{exc}"}, status=500)

    def _handle_settings_post(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
            api_key = str(payload.get("deepseekApiKey", "")).strip()
            write_env_value("DEEPSEEK_API_KEY", api_key)
            self._send_json({"ok": True})
        except Exception as exc:  # noqa: BLE001 - returned to local UI
            self._send_json({"ok": False, "error": str(exc)}, status=500)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_text(self, content: str, content_type: str, status: int = 200) -> None:
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(host: str = HOST, port: int = PORT) -> None:
    os.chdir(app_dir())
    os.environ.setdefault("AI_MODEL_PROVIDER", "deepseek")
    os.environ.setdefault("DEEPSEEK_MODEL", "deepseek-chat")
    server = ThreadingHTTPServer((host, port), HextechRequestHandler)
    print(f"Hextech web UI: http://{host}:{port}")
    server.serve_forever()


def main() -> None:
    serve()


if __name__ == "__main__":
    main()
