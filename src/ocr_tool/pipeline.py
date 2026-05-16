"""Orchestration pipeline: capture → preprocess → OCR → layout → format."""
from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING

import cv2

from . import capture, formatters, layout, ocr, preprocess

if TYPE_CHECKING:
    import numpy as np

log = logging.getLogger(__name__)


def load_image(path: str) -> "np.ndarray":
    """Load an image file as RGB numpy array."""
    img = cv2.imread(path)
    if img is None:
        print(f"Error: could not read image file: {path}", file=sys.stderr)
        sys.exit(1)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def run_from_array(
    img: "np.ndarray",
    *,
    langs: list[str] | None = None,
    preprocess_steps: list[str] | None = None,
    do_layout: bool = False,
    output_format: str = "plain",
    save_preprocessed: str | None = None,
) -> str:
    """Run pipeline on an in-memory image array — no temp files needed."""
    if preprocess_steps:
        img = preprocess.apply_chain(img, preprocess_steps)
        if save_preprocessed:
            cv2.imwrite(save_preprocessed, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

    results = ocr.recognize(img, langs=langs)

    layout_data = layout.analyze_image(results) if do_layout else None

    fmt_func_name = formatters.FORMATTERS.get(output_format, (None,))[0]
    if fmt_func_name is None:
        fmt_func_name = "format_plain"
    fmt_func = getattr(formatters, fmt_func_name)
    if output_format in ("json", "html"):
        return fmt_func(results, layout=layout_data)
    return fmt_func(results)


def run_single(
    path: str | None = None,
    *,
    langs: list[str] | None = None,
    preprocess_steps: list[str] | None = None,
    do_layout: bool = False,
    output_format: str = "plain",
    save_preprocessed: str | None = None,
) -> str:
    """Run the full pipeline on a single image.

    Args:
        path: Image file path, or None for screen capture.
        langs: Language codes for OCR.
        preprocess_steps: List of preprocessing step names.
        do_layout: Run layout analysis.
        output_format: "plain" | "json" | "csv" | "html"
        save_preprocessed: Path to save preprocessed image (for debugging).

    Returns:
        Formatted output string.
    """
    # Capture or load
    if path is None:
        log.info("Capturing screen...")
        img = capture.capture_screen()
    else:
        img = load_image(path)

    # Preprocess
    if preprocess_steps:
        log.info("Applying preprocessing: %s", ", ".join(preprocess_steps))
        img = preprocess.apply_chain(img, preprocess_steps)
        if save_preprocessed:
            cv2.imwrite(save_preprocessed, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            log.info("Saved preprocessed image to %s", save_preprocessed)

    # OCR
    results = ocr.recognize(img, langs=langs)

    # Layout analysis
    layout_data = None
    if do_layout:
        layout_data = layout.analyze_image(results)

    # Format
    fmt_func_name = formatters.FORMATTERS.get(output_format, (None,))[0]
    if fmt_func_name is None:
        fmt_func_name = "format_plain"

    if output_format in ("json", "html"):
        fmt_func = getattr(formatters, fmt_func_name)
        return fmt_func(results, layout=layout_data)

    fmt_func = getattr(formatters, fmt_func_name)
    return fmt_func(results)


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
