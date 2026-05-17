"""EasyOCR wrapper with reader caching."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    import numpy as np

ProgressCB = Callable[[int, int, str], None] | None

log = logging.getLogger(__name__)

_reader_cache: dict[tuple[str, ...], "easyocr.Reader"] = {}


def get_reader(langs: list[str] | None = None, progress_cb: ProgressCB = None) -> "easyocr.Reader":
    """Return a cached easyocr Reader for the given languages."""
    import easyocr

    key = tuple(langs or ["ru", "en"])
    if key not in _reader_cache:
        if progress_cb:
            progress_cb(0, 1, "Loading OCR model...")
        log.info("Loading easyocr model for %s", "+".join(key))
        _reader_cache[key] = easyocr.Reader(list(key), gpu=False, verbose=False)
        if progress_cb:
            progress_cb(1, 1, "OCR model loaded")
    return _reader_cache[key]


def recognize(
    image: "np.ndarray",
    langs: list[str] | None = None,
    paragraph: bool = False,
    min_size: int = 10,
    width_ths: float = 0.7,
    progress_cb: ProgressCB = None,
) -> list[dict]:
    """Run OCR on an image array.

    Returns a list of dicts:
        {"text": str, "confidence": float, "bbox": [[x1,y1],[x2,y1],[x2,y2],[x1,y2]]}
    """
    reader = get_reader(langs, progress_cb=progress_cb)
    if progress_cb:
        progress_cb(0, 1, "Recognizing text...")
    raw = reader.readtext(image, paragraph=paragraph, min_size=min_size, width_ths=width_ths)
    results: list[dict] = []
    for entry in raw:
        if len(entry) == 3:
            bbox, text, conf = entry
            confidence = round(float(conf), 4)
        else:
            bbox, text = entry
            confidence = None
        results.append({
            "text": text,
            "confidence": confidence,
            "bbox": [[float(x), float(y)] for x, y in bbox],
        })
    if progress_cb:
        progress_cb(1, 1, f"{len(results)} text fragments found")
    return results


def recognize_path(
    path: str,
    langs: list[str] | None = None,
    paragraph: bool = False,
    min_size: int = 10,
    width_ths: float = 0.7,
) -> list[dict]:
    """Run OCR on an image file path."""
    import cv2

    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return recognize(img, langs=langs, paragraph=paragraph, min_size=min_size, width_ths=width_ths)
