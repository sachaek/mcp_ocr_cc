"""Output formatters for OCR results."""
from __future__ import annotations

import csv
import io
import json
from typing import Any


def format_plain(items: list[dict]) -> str:
    """Plain text: one line per text fragment."""
    return "\n".join(item["text"] for item in items if item.get("text"))


def format_json(items: list[dict], layout: dict | None = None) -> str:
    """JSON output with full data including layout analysis."""
    output: dict[str, Any] = {"results": items}
    if layout:
        output["layout"] = layout
        scanned = layout.get("blocks", [])
        output["text"] = "\n".join(
            b["text"] for b in scanned if b.get("text")
        )
    return json.dumps(output, ensure_ascii=False, indent=2)


def format_csv(items: list[dict]) -> str:
    """CSV output: text, confidence, bbox."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["text", "confidence", "bbox"])
    for item in items:
        writer.writerow([
            item.get("text", ""),
            item.get("confidence", ""),
            json.dumps(item.get("bbox", []), ensure_ascii=False),
        ])
    return out.getvalue()


def format_html(items: list[dict], layout: dict | None = None) -> str:
    """HTML output preserving document structure."""
    parts = ["<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>"]

    if layout and layout.get("blocks"):
        for block in layout["blocks"]:
            text = block.get("text", "")
            if block.get("type") == "heading":
                parts.append(f"<h2>{_html_escape(text)}</h2>")
            elif block.get("type") == "list-item":
                parts.append(f"<li>{_html_escape(text)}</li>")
            else:
                parts.append(f"<p>{_html_escape(text)}</p>")
    else:
        for item in items:
            parts.append(f"<p>{_html_escape(item.get('text', ''))}</p>")

    parts.append("</body></html>")
    return "\n".join(parts)


def _html_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


FORMATTERS: dict[str, tuple[str, bool]] = {
    "plain": ("format_plain", False),
    "json": ("format_json", True),
    "csv": ("format_csv", False),
    "html": ("format_html", True),
}
