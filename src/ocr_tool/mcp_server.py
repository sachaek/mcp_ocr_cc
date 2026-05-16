"""MCP server — exposes ocr-tool as native Claude Code tools.

Install: pip install ocr-tool[mcp]
Register: claude mcp add --transport stdio --scope user ocr-tool -- python -m ocr_tool.mcp_server
"""
from __future__ import annotations

import json
import logging
import os
import sys
import tempfile

from .pipeline import run_single

# All logging must go to stderr — stdout is JSON-RPC transport
log = logging.getLogger(__name__)


def _image_to_text(
    path: str,
    langs: str = "ru+en",
    preprocess: str | None = None,
    layout: bool = False,
    output_format: str = "plain",
) -> str:
    """Run OCR on an image and return formatted text."""
    preprocess_steps = None
    if preprocess:
        preprocess_steps = [s.strip() for s in preprocess.split(",") if s.strip()]
    return run_single(
        path,
        langs=langs.split("+") if langs else ["ru", "en"],
        preprocess_steps=preprocess_steps,
        do_layout=layout,
        output_format=output_format,
    )


try:
    from mcp.server.fastmcp import FastMCP

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
        if not os.path.isfile(path):
            return json.dumps({"error": f"File not found: {path}"})
        try:
            result = _image_to_text(path, langs, preprocess, layout, output_format)
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
        try:
            from .capture import capture_screen, list_monitors

            monitors = list_monitors()
            if monitor < 0 or monitor >= len(monitors):
                available = {m["num"] for m in monitors}
                return json.dumps({"error": f"Monitor {monitor} not found. Available: {available}"})

            img = capture_screen(monitor)

            fd, tmp_path = tempfile.mkstemp(suffix=".png")
            try:
                import cv2
                cv2.imwrite(tmp_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
                result = _image_to_text(tmp_path, langs, preprocess, layout, output_format)
                return result
            finally:
                os.close(fd)
                os.unlink(tmp_path)
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
        server.run(transport="stdio")

except ImportError:
    # Fallback when mcp package is not installed
    def main() -> None:  # type: ignore[misc]
        print("Error: mcp package not installed.", file=sys.stderr)
        print("Install: pip install ocr-tool[mcp]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
