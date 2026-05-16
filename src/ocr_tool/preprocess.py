"""Image preprocessing to improve OCR quality.

All operations use OpenCV/Pillow only — no ML models.
Every function accepts and returns a numpy array (RGB).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import cv2
import numpy as np

if TYPE_CHECKING:
    import numpy.typing as npt

    RGBArray = npt.NDArray[np.uint8]


def to_grayscale(img: RGBArray) -> RGBArray:
    """Convert RGB to grayscale (3-channel)."""
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)


def binarize(img: RGBArray) -> RGBArray:
    """Adaptive thresholding — works well for documents with uneven lighting."""
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 31, 2)
    return cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)


def binarize_otsu(img: RGBArray) -> RGBArray:
    """Otsu global thresholding."""
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)


def denoise(img: RGBArray, strength: int = 10) -> RGBArray:
    """Non-local means denoising. Strength 10 = light, 30 = aggressive."""
    return cv2.fastNlMeansDenoisingColored(img, None, strength, strength, 7, 21)


def denoise_bilateral(img: RGBArray, d: int = 9) -> RGBArray:
    """Bilateral filter — preserves edges while smoothing."""
    return cv2.bilateralFilter(img, d, 75, 75)  # type: ignore[no-any-return]


def clahe(img: RGBArray, clip_limit: float = 2.0) -> RGBArray:
    """Contrast Limited Adaptive Histogram Equalization — boosts local contrast."""
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe_obj = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
    l = clahe_obj.apply(l)
    lab = cv2.merge([l, a, b])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)


def deskew(img: RGBArray, max_angle: float = 15.0) -> RGBArray:
    """Auto-rotate image so text lines are horizontal."""
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.bitwise_not(gray)
    coords = np.column_stack(np.where(gray > 0))
    if len(coords) == 0:
        return img

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    if abs(angle) > max_angle:
        return img

    h, w = img.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img, matrix, (w, h),
                              flags=cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_REPLICATE)
    return rotated


def upscale(img: RGBArray, scale: float = 2.0) -> RGBArray:
    """Upscale image using Lanczos interpolation (no ML)."""
    h, w = img.shape[:2]
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)


def sharpen(img: RGBArray) -> RGBArray:
    """Unsharp masking — enhances edges for crisper OCR."""
    blurred = cv2.GaussianBlur(img, (0, 0), 3)
    return cv2.addWeighted(img, 1.5, blurred, -0.5, 0)


# Registry of all preprocessing steps for CLI dispatch
STEPS: dict[str, tuple[str, dict]] = {
    "gray": ("to_grayscale", {}),
    "binarize": ("binarize", {}),
    "otsu": ("binarize_otsu", {}),
    "denoise": ("denoise", {"strength": 10}),
    "bilateral": ("denoise_bilateral", {}),
    "clahe": ("clahe", {}),
    "deskew": ("deskew", {}),
    "upscale": ("upscale", {"scale": 2.0}),
    "sharpen": ("sharpen", {}),
}


def apply_chain(img: RGBArray, steps: list[str]) -> RGBArray:
    """Apply a comma-separated chain of preprocessing steps."""
    for name in steps:
        name = name.strip()
        if name not in STEPS:
            available = ", ".join(sorted(STEPS))
            raise ValueError(f"Unknown preprocessing step: {name!r}. Available: {available}")
        func_name, kwargs = STEPS[name]
        func = globals()[func_name]
        img = func(img, **kwargs)
    return img
