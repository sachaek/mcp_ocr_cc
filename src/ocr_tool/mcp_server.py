"""MCP server — exposes ocr-tool as native Claude Code tools.

Install: pip install ocr-tool[mcp]
"""
from __future__ import annotations

import json
import logging
import os
import sys

from .pipeline import run_from_array, run_single

log = logging.getLogger(__name__)


def _parse_options(langs: str, preprocess: str | None, layout: bool):
    """Parse common OCR options into structured form."""
    preprocess_steps = None
    if preprocess:
        preprocess_steps = [s.strip() for s in preprocess.split(",") if s.strip()]
    return {
        "langs": langs.split("+") if langs else ["ru", "en"],
        "preprocess_steps": preprocess_steps,
        "do_layout": layout,
    }


def _mk_progress(ctx):
    """Build a progress callback from a FastMCP Context."""
    import time as _time

    _start = _time.time()
    _last_step = ""

    def cb(current: int, total: int, msg: str):
        nonlocal _last_step
        if msg == _last_step:
            return  # deduplicate
        _last_step = msg
        elapsed = _time.time() - _start
        ctx.info(f"[{current}/{total}] {msg} ({elapsed:.1f}s)")
        ctx.report_progress(current, total)
    return cb


def _image_to_text(
    path: str,
    langs: str = "ru+en",
    preprocess: str | None = None,
    layout: bool = False,
    output_format: str = "plain",
    progress_cb=None,
) -> str:
    """Run OCR on an image file and return formatted text."""
    opts = _parse_options(langs, preprocess, layout)
    return run_single(path, output_format=output_format, progress_cb=progress_cb, **opts)


try:
    from mcp.server.fastmcp import FastMCP, Context

    server = FastMCP("ocr-tool")

    @server.tool(
        description="Extract text from an image using OCR. Returns the recognized text."
    )
    def ocr_image(
        path: str,
        langs: str = "ru+en",
        preprocess: str | None = None,
        layout: bool = False,
        output_format: str = "plain",
        ctx: Context | None = None,
    ) -> str:
        """Run OCR on an image file.

        Args:
            path: Absolute path to the image file (PNG, JPG, BMP, TIFF, WEBP).
            langs: Language codes separated by '+' (default: 'ru+en').
            preprocess: Comma-separated preprocessing steps. Available: bilateral, binarize, clahe, denoise, deskew, gray, otsu, sharpen, upscale.
            layout: Whether to analyze document layout (columns, headings, tables).
            output_format: Output format — 'plain', 'json', 'csv', or 'html'.
        """
        log.info("ocr_image: path=%s langs=%s", path, langs)
        cb = _mk_progress(ctx) if ctx else None
        if not os.path.isfile(path):
            return json.dumps({"error": f"File not found: {path}"})
        try:
            result = _image_to_text(path, langs, preprocess, layout, output_format, progress_cb=cb)
            return result
        except Exception as e:
            log.exception("ocr_image failed")
            return json.dumps({"error": str(e)})

    @server.tool(
        description="Capture a screenshot and extract text using OCR. Returns the recognized text."
    )
    def ocr_screen(
        monitor: int = 1,
        langs: str = "ru+en",
        preprocess: str | None = None,
        layout: bool = False,
        output_format: str = "plain",
        ctx: Context | None = None,
    ) -> str:
        """Capture a monitor screen and run OCR on it.

        Args:
            monitor: Monitor number (1-based). Use 1 for primary monitor.
            langs: Language codes separated by '+' (default: 'ru+en').
            preprocess: Comma-separated preprocessing steps.
            layout: Whether to analyze document layout.
            output_format: Output format — 'plain', 'json', 'csv', or 'html'.
        """
        log.info("ocr_screen: monitor=%d langs=%s", monitor, langs)
        cb = _mk_progress(ctx) if ctx else None
        try:
            from .capture import capture_screen, list_monitors

            monitors = list_monitors()
            if monitor < 0 or monitor >= len(monitors):
                available = {m["num"] for m in monitors}
                return json.dumps({"error": f"Monitor {monitor} not found. Available: {available}"})

            if cb:
                cb(0, 5, "Capturing screen...")
            img = capture_screen(monitor)
            if cb:
                cb(1, 5, "Screen captured")
            opts = _parse_options(langs, preprocess, layout)
            return run_from_array(img, output_format=output_format, progress_cb=cb, **opts)
        except ImportError:
            return json.dumps({"error": "Screen capture requires mss. Install: pip install ocr-tool[screen]"})
        except Exception as e:
            log.exception("ocr_screen failed")
            return json.dumps({"error": str(e)})

    def main() -> None:
        """Run MCP server with stdio transport."""
        logging.basicConfig(
            level=logging.WARNING,
            format="[ocr-tool-mcp] %(levelname)s: %(message)s",
            stream=sys.stderr,
        )
        log.info("Preloading OCR model (ru+en)...")
        from .ocr import get_reader  # noqa: PLC0415
        get_reader(["ru", "en"])  # <-- load model NOW, not on first tool call
        log.info("OCR model preloaded — ready for fast OCR")
        server.run(transport="stdio")

except ImportError:
    # Fallback when mcp package is not installed
    def main() -> None:  # type: ignore[misc]
        print("Error: mcp package not installed.", file=sys.stderr)
        print("Install: pip install ocr-tool[mcp]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
