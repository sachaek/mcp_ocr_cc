"""Orchestration pipeline: capture → preprocess → OCR → layout → format."""
from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Callable

import cv2

from . import capture, formatters, layout, ocr, preprocess

if TYPE_CHECKING:
    import numpy as np

ProgressCB = Callable[[int, int, str], None] | None

log = logging.getLogger(__name__)


MAX_PIXELS = 1_920 * 1_080  # downscale if image exceeds this


def _downscale_if_needed(img: "np.ndarray") -> "np.ndarray":
    """Downscale large images to keep OCR fast."""
    h, w = img.shape[:2]
    if w * h > MAX_PIXELS:
        scale = (MAX_PIXELS / (w * h)) ** 0.5
        new_w, new_h = int(w * scale), int(h * scale)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return img


def load_image(path: str) -> "np.ndarray":
    """Load an image file as RGB numpy array."""
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return _downscale_if_needed(img)


def run_from_array(
    img: "np.ndarray",
    *,
    langs: list[str] | None = None,
    preprocess_steps: list[str] | None = None,
    do_layout: bool = False,
    output_format: str = "plain",
    save_preprocessed: str | None = None,
    progress_cb: ProgressCB = None,
) -> str:
    """Run pipeline on an in-memory image array — no temp files needed."""
    total = 4 + bool(do_layout)
    step = 0

    def _report(msg: str):
        nonlocal step
        if progress_cb:
            progress_cb(step, total, msg)
        step += 1

    img = _downscale_if_needed(img)
    _report("Image ready")

    if preprocess_steps:
        img = preprocess.apply_chain(img, preprocess_steps)
        if save_preprocessed:
            cv2.imwrite(save_preprocessed, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    _report("Preprocessing done")

    results = ocr.recognize(img, langs=langs, progress_cb=progress_cb)
    _report("Text recognized")

    layout_data = None
    if do_layout:
        layout_data = layout.analyze_image(results)
    _report("Layout analyzed")

    fmt_func_name = formatters.FORMATTERS.get(output_format, (None,))[0]
    if fmt_func_name is None:
        fmt_func_name = "format_plain"
    fmt_func = getattr(formatters, fmt_func_name)
    if output_format in ("json", "html"):
        result = fmt_func(results, layout=layout_data)
    else:
        result = fmt_func(results)
    _report("Done")
    return result


def run_single(
    path: str | None = None,
    *,
    langs: list[str] | None = None,
    preprocess_steps: list[str] | None = None,
    do_layout: bool = False,
    output_format: str = "plain",
    save_preprocessed: str | None = None,
    progress_cb: ProgressCB = None,
) -> str:
    """Run the full pipeline on a single image.

    Args:
        path: Image file path, or None for screen capture.
        langs: Language codes for OCR.
        preprocess_steps: List of preprocessing step names.
        do_layout: Run layout analysis.
        output_format: "plain" | "json" | "csv" | "html"
        save_preprocessed: Path to save preprocessed image (for debugging).
        progress_cb: Optional callback(current_step, total_steps, message).

    Returns:
        Formatted output string.
    """
    total = 5 + bool(do_layout)
    step = 0

    def _report(msg: str):
        nonlocal step
        if progress_cb:
            progress_cb(step, total, msg)
        step += 1

    # Capture or load
    if path is None:
        img = capture.capture_screen()
        _report("Screen captured")
    else:
        img = load_image(path)
        _report("Image loaded")

    # Preprocess
    if preprocess_steps:
        img = preprocess.apply_chain(img, preprocess_steps)
        if save_preprocessed:
            cv2.imwrite(save_preprocessed, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        _report("Preprocessing done")
    else:
        _report("Preprocessing skipped")

    # OCR
    results = ocr.recognize(img, langs=langs, progress_cb=progress_cb)
    _report("Text recognized")

    # Layout analysis
    layout_data = None
    if do_layout:
        layout_data = layout.analyze_image(results)
        _report("Layout analyzed")
    else:
        _report("Layout skipped")

    # Format
    fmt_func_name = formatters.FORMATTERS.get(output_format, (None,))[0]
    if fmt_func_name is None:
        fmt_func_name = "format_plain"
    fmt_func = getattr(formatters, fmt_func_name)

    if output_format in ("json", "html"):
        result = fmt_func(results, layout=layout_data)
    else:
        result = fmt_func(results)
    _report("Done")
    return result


def run_batch(
    directory: str,
    *,
    langs: list[str] | None = None,
    preprocess_steps: list[str] | None = None,
    do_layout: bool = False,
    output_format: str = "plain",
    recursive: bool = False,
    extensions: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"),
) -> dict[str, str]:
    """Run pipeline on all images in a directory.

    Returns dict mapping filename → formatted output.
    """
    supported = extensions
    results: dict[str, str] = {}

    if recursive:
        iterator = []
        for root, _dirs, files in os.walk(directory):
            for f in sorted(files):
                iterator.append(os.path.join(root, f))
    else:
        iterator = sorted(
            os.path.join(directory, f)
            for f in os.listdir(directory)
            if f.lower().endswith(supported)
        )

    for filepath in iterator:
        if not filepath.lower().endswith(supported):
            continue
        log.info("Processing: %s", filepath)
        out = run_single(
            filepath,
            langs=langs,
            preprocess_steps=preprocess_steps,
            do_layout=do_layout,
            output_format=output_format,
        )
        results[filepath] = out

    return results
