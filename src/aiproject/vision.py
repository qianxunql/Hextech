from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO


HEXTECH_CHOICE_CROP = (0.22, 0.18, 0.79, 0.69)


@dataclass(frozen=True)
class OcrResult:
    text: str
    engine: str
    warning: str = ""
    crop_box: CropBox | None = None


@dataclass(frozen=True)
class CropBox:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    def as_tuple(self) -> tuple[int, int, int, int]:
        return (self.left, self.top, self.right, self.bottom)


def _ratio_crop_box(width: int, height: int, ratios: tuple[float, float, float, float]) -> CropBox:
    left_ratio, top_ratio, right_ratio, bottom_ratio = ratios
    left = max(0, min(width - 1, round(width * left_ratio)))
    top = max(0, min(height - 1, round(height * top_ratio)))
    right = max(left + 1, min(width, round(width * right_ratio)))
    bottom = max(top + 1, min(height, round(height * bottom_ratio)))
    return CropBox(left=left, top=top, right=right, bottom=bottom)


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


def crop_hextech_choice_area(image_bytes: bytes) -> tuple[bytes, CropBox]:
    from PIL import Image

    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    crop_box = _ratio_crop_box(image.width, image.height, HEXTECH_CHOICE_CROP)
    cropped = image.crop(crop_box.as_tuple())
    buffer = BytesIO()
    cropped.save(buffer, format="PNG")
    return buffer.getvalue(), crop_box


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


def ocr_image_bytes(image_bytes: bytes, crop_hextech_area: bool = True) -> OcrResult:
    crop_box = None
    if crop_hextech_area:
        image_bytes, crop_box = crop_hextech_choice_area(image_bytes)

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
    return OcrResult(text=text, engine="rapidocr-onnxruntime", warning=warning, crop_box=crop_box)
