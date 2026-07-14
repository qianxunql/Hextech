from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO


@dataclass(frozen=True)
class OcrResult:
    text: str
    engine: str
    warning: str = ""


def capture_primary_monitor_png() -> bytes:
    try:
        import mss
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("缺少截图依赖 mss，请先运行 uv sync。") from exc

    with mss.mss() as screen:
        monitor = screen.monitors[1]
        shot = screen.grab(monitor)
        from PIL import Image

        image = Image.frombytes("RGB", shot.size, shot.rgb)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()


def _prepare_for_ocr(image_bytes: bytes):
    from PIL import Image, ImageEnhance, ImageFilter

    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    image = image.resize((image.width * 2, image.height * 2))
    image = image.convert("L")
    image = ImageEnhance.Contrast(image).enhance(1.8)
    image = image.filter(ImageFilter.SHARPEN)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@lru_cache(maxsize=1)
def _rapid_ocr():
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("缺少内置 OCR 依赖 rapidocr-onnxruntime，请先运行 uv sync。") from exc

    return RapidOCR()


def ocr_image_bytes(image_bytes: bytes) -> OcrResult:
    image = _prepare_for_ocr(image_bytes)
    result, _ = _rapid_ocr()(image)
    lines = []
    for item in result or []:
        if len(item) >= 2 and item[1]:
            lines.append(str(item[1]).strip())

    text = "\n".join(line for line in lines if line)
    warning = ""
    if not text:
        warning = "没有从截图中识别到文字。请确认游戏处于海克斯选择界面，或先用手动输入。"
    return OcrResult(text=text, engine="rapidocr-onnxruntime", warning=warning)
