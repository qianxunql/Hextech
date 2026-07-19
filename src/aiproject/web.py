from __future__ import annotations

from functools import lru_cache
import json
import mimetypes
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from urllib.parse import unquote, urlparse

from aiproject.config import external_config_dir
from aiproject.lcu import get_current_champion
from aiproject.main import run, stream as stream_run
from aiproject.matcher import build_hextech_choice_question, match_hextech_names
from aiproject.scraper import load_champion_pages_from_index_html, load_hextech_pages_from_index_html
from aiproject.vision import OcrResult, capture_primary_monitor_png, ocr_image_bytes


HOST = "127.0.0.1"
PORT = 8765


def static_file_path(*parts: str) -> Path:
    candidates = [
        Path(__file__).resolve().parent / "static" / Path(*parts),
        app_dir() / "aiproject" / "static" / Path(*parts),
        app_dir() / "src" / "aiproject" / "static" / Path(*parts),
    ]
    if getattr(sys, "frozen", False):
        bundle_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        candidates.insert(0, bundle_root / "aiproject" / "static" / Path(*parts))

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


@lru_cache(maxsize=1)
def index_html() -> str:
    return static_file_path("index.html").read_text(encoding="utf-8")


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        bundle_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        if (bundle_dir / "data").exists():
            return bundle_dir
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def model_overrides() -> dict[str, str]:
    return {"model_provider": "deepseek"}


def champion_catalog() -> list[dict[str, str]]:
    try:
        pages = load_champion_pages_from_index_html("data/html/champions_index.html")
    except RuntimeError:
        return []

    champions: list[dict[str, str]] = []
    image_root = Path("英雄名录 _ ARAM Hextech Wiki_files")
    for page in pages:
        fields: dict[str, str] = {}
        for line in page.text.splitlines():
            if "：" in line:
                key, value = line.split("：", 1)
                fields[key.strip()] = value.strip()

        image_path = image_root / f"{page.name}.webp"
        champions.append(
            {
                "id": page.name,
                "name": fields.get("英雄名称", page.name),
                "title": fields.get("中文称号", ""),
                "rating": fields.get("目录评级", "-"),
                "image": f"/assets/champions/{page.name}.webp" if image_path.exists() else "",
            }
        )

    return sorted(champions, key=lambda item: item["name"])


def hextech_catalog() -> list[dict[str, str]]:
    try:
        pages = load_hextech_pages_from_index_html("海克斯强化列表 _ ARAM Hextech Wiki.html")
    except RuntimeError:
        return []

    image_root = Path("海克斯强化列表 _ ARAM Hextech Wiki_files")
    tier_order = {"棱彩阶": 0, "黄金阶": 1, "白银阶": 2}
    hextechs: list[dict[str, str]] = []
    for page in pages:
        image_path = image_root / f"{page.hextech_id}.webp"
        hextechs.append(
            {
                "id": page.hextech_id,
                "name": page.name,
                "tier": page.tier,
                "ratingRank": str(tier_order.get(page.tier, 99)),
                "description": page.description,
                "image": f"/assets/hextech/{page.hextech_id}.webp" if image_path.exists() else "",
            }
        )

    return sorted(hextechs, key=lambda item: (int(item["ratingRank"]), item["name"]))


def env_file_path(path: str = ".env") -> Path:
    return external_config_dir() / path


def read_env_value(key: str, path: str = ".env") -> str:
    env_path = env_file_path(path)
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
    env_path = env_file_path(path)
    env_path.parent.mkdir(parents=True, exist_ok=True)
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
    server_version = "PoroWeb/0.1"

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            self._send_text(index_html(), "text/html; charset=utf-8")
            return
        if path == "/api/champions":
            self._send_json({"champions": champion_catalog()})
            return
        if path == "/api/hextech":
            self._send_json({"hextech": hextech_catalog()})
            return
        if path == "/health":
            self._send_json({"ok": True})
            return
        if path == "/api/settings":
            self._send_json({"hasDeepseekApiKey": bool(read_env_value("DEEPSEEK_API_KEY"))})
            return
        if path == "/api/vision/status":
            try:
                import rapidocr_onnxruntime  # noqa: F401

                self._send_json({"hasBuiltInOcr": True, "ocrEngine": "rapidocr-onnxruntime"})
            except ImportError:
                self._send_json({"hasBuiltInOcr": False, "ocrEngine": "rapidocr-onnxruntime"})
            return
        if path == "/api/lcu/current-champion":
            self._handle_current_champion()
            return
        if path.startswith("/static/"):
            self._send_static_file(path)
            return
        if path.startswith("/assets/champions/"):
            self._send_champion_image(path)
            return
        if path.startswith("/assets/hextech/"):
            self._send_hextech_image(path)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/settings":
            self._handle_settings_post()
            return

        if path == "/api/ask-stream":
            self._handle_ask_stream()
            return

        if path == "/api/recognize-screenshot":
            self._handle_recognize_screenshot()
            return

        if path != "/api/ask":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        try:
            question = self._read_question()
            answer = run(question, overrides=model_overrides())
            self._send_json({"answer": answer})
        except Exception as exc:  # noqa: BLE001 - returned to local UI
            self._send_json({"error": str(exc), "answer": f"出错了：{exc}"}, status=500)

    def _read_question(self) -> str:
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)
        payload = json.loads(raw_body.decode("utf-8"))
        question = str(payload.get("question", "")).strip()
        if not question:
            raise ValueError("question is required")
        return question

    def _read_json_payload(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw_body = self.rfile.read(length)
        return json.loads(raw_body.decode("utf-8"))

    def _handle_ask_stream(self) -> None:
        try:
            question = self._read_question()
        except Exception as exc:  # noqa: BLE001 - returned to local UI
            self._send_text(str(exc), "text/plain; charset=utf-8", status=400)
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        try:
            for chunk in stream_run(question, overrides=model_overrides()):
                body = chunk.encode("utf-8")
                if not body:
                    continue
                self.wfile.write(body)
                self.wfile.flush()
        except Exception as exc:  # noqa: BLE001 - stream error is shown inline
            self.wfile.write(f"出错了：{exc}".encode("utf-8"))
            self.wfile.flush()

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

    def _handle_recognize_screenshot(self) -> None:
        try:
            payload = self._read_json_payload()
            champion = str(payload.get("champion", "")).strip()
            manual_text = str(payload.get("ocrText", "")).strip()
            detected_champion = None

            if not champion:
                detected_champion = get_current_champion()
                if detected_champion is not None:
                    champion = detected_champion.name

            if manual_text:
                ocr_result = OcrResult(text=manual_text, engine="manual")
            else:
                image_bytes = capture_primary_monitor_png()
                ocr_result = ocr_image_bytes(image_bytes)

            matches = match_hextech_names(ocr_result.text, hextech_catalog(), limit=4)
            question = build_hextech_choice_question(champion, matches)
            if not matches and ocr_result.text:
                question = f"{question}\nOCR 原始文本：{ocr_result.text}"
            self._send_json(
                {
                    "ok": True,
                    "engine": ocr_result.engine,
                    "warning": ocr_result.warning,
                    "rawText": ocr_result.text,
                    "cropBox": {
                        "left": ocr_result.crop_box.left,
                        "top": ocr_result.crop_box.top,
                        "right": ocr_result.crop_box.right,
                        "bottom": ocr_result.crop_box.bottom,
                        "width": ocr_result.crop_box.width,
                        "height": ocr_result.crop_box.height,
                    }
                    if ocr_result.crop_box
                    else None,
                    "champion": {
                        "id": detected_champion.champion_id,
                        "alias": detected_champion.alias,
                        "name": detected_champion.name,
                        "source": detected_champion.source,
                        "phase": detected_champion.phase,
                    }
                    if detected_champion
                    else None,
                    "matches": [
                        {
                            "id": item.id,
                            "name": item.name,
                            "tier": item.tier,
                            "score": round(item.score, 1),
                            "sourceText": item.source_text,
                        }
                        for item in matches
                    ],
                    "question": question,
                }
            )
        except Exception as exc:  # noqa: BLE001 - returned to local UI
            self._send_json({"ok": False, "error": str(exc)}, status=500)

    def _handle_current_champion(self) -> None:
        try:
            champion = get_current_champion()
            if champion is None:
                self._send_json({"ok": True, "champion": None})
                return
            self._send_json(
                {
                    "ok": True,
                    "champion": {
                        "id": champion.champion_id,
                        "alias": champion.alias,
                        "name": champion.name,
                        "source": champion.source,
                        "phase": champion.phase,
                    },
                }
            )
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

    def _send_static_file(self, path: str) -> None:
        filename = Path(unquote(path)).name
        if filename not in {"index.html", "styles.css", "app.js", "overlay.html", "overlay.css", "overlay.js"}:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        file_path = static_file_path(filename)
        if not file_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        body = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(filename)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_champion_image(self, path: str) -> None:
        filename = Path(unquote(path)).name
        if not filename.endswith(".webp") or "/" in filename or "\\" in filename:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        image_path = Path("英雄名录 _ ARAM Hextech Wiki_files") / filename
        if not image_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        body = image_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(filename)[0] or "image/webp")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_hextech_image(self, path: str) -> None:
        filename = Path(unquote(path)).name
        if not filename.endswith(".webp") or "/" in filename or "\\" in filename:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        image_path = Path("海克斯强化列表 _ ARAM Hextech Wiki_files") / filename
        if not image_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        body = image_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(filename)[0] or "image/webp")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(host: str = HOST, port: int = PORT) -> None:
    os.chdir(app_dir())
    os.environ.setdefault("AI_MODEL_PROVIDER", "deepseek")
    os.environ.setdefault("DEEPSEEK_MODEL", "deepseek-chat")
    server = ThreadingHTTPServer((host, port), HextechRequestHandler)
    print(f"Poro web UI: http://{host}:{port}")
    server.serve_forever()


def main() -> None:
    serve()


if __name__ == "__main__":
    main()
