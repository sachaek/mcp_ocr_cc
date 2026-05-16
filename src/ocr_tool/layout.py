"""Document layout analysis using OCR bounding boxes.

No ML models — purely geometric analysis of easyocr bbox data.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class TextBlock:
    """A semantic block of text on the page."""
    type: str  # "heading" | "paragraph" | "list-item" | "table-cell"
    text: str
    bbox: list[list[float]]  # [[x1,y1],[x2,y1],[x2,y2],[x1,y2]]
    confidence: float | None = None


@dataclass
class Table:
    """A detected table with rows and columns."""
    cells: list[list[str]] = field(default_factory=list)
    bbox: list[list[float]] | None = None


def _bbox_center_x(bbox: list[list[float]]) -> float:
    return (bbox[0][0] + bbox[2][0]) / 2


def _bbox_center_y(bbox: list[list[float]]) -> float:
    return (bbox[0][1] + bbox[2][1]) / 2


def _bbox_height(bbox: list[list[float]]) -> float:
    return bbox[2][1] - bbox[0][1]


def _bbox_width(bbox: list[list[float]]) -> float:
    return bbox[2][0] - bbox[0][0]


def sort_reading_order(
    items: list[dict],
    row_threshold: float = 0.3,
) -> list[dict]:
    """Sort OCR results in natural reading order (top→bottom, left→right).

    Groups items into rows by Y-coordinate proximity, then sorts
    left→right within each row.

    Args:
        items: OCR results with "bbox" keys.
        row_threshold: Fraction of median bbox height used as Y-tolerance.
    """
    if not items:
        return items

    heights = [_bbox_height(i["bbox"]) for i in items]
    median_h = statistics.median(heights) if heights else 20
    tolerance = median_h * row_threshold

    # Sort by Y first, then cluster into rows
    sorted_y = sorted(items, key=lambda i: _bbox_center_y(i["bbox"]))
    rows: list[list[dict]] = [[sorted_y[0]]]

    for item in sorted_y[1:]:
        prev_y = _bbox_center_y(rows[-1][-1]["bbox"])
        if abs(_bbox_center_y(item["bbox"]) - prev_y) <= tolerance:
            rows[-1].append(item)
        else:
            rows.append([item])

    # Sort each row left→right
    for row in rows:
        row.sort(key=lambda i: _bbox_center_x(i["bbox"]))

    return [item for row in rows for item in row]


def detect_columns(
    items: list[dict],
    min_gap_px: float = 50,
) -> list[list[dict]]:
    """Split OCR items into columns based on X-coordinate clustering.

    Args:
        items: OCR results with "bbox" keys.
        min_gap_px: Minimum horizontal gap between columns.

    Returns:
        List of columns, each column being a list of items in reading order.
    """
    if not items:
        return []

    centers_x = sorted(_bbox_center_x(i["bbox"]) for i in items)
    gaps = [centers_x[i + 1] - centers_x[i] for i in range(len(centers_x) - 1)]
    if not gaps:
        return [items]

    median_gap = statistics.median(gaps) if gaps else 0
    threshold = max(min_gap_px, median_gap * 2)

    # Find split points
    mid_x = {}
    for i, gap in enumerate(gaps):
        if gap > threshold:
            split = (centers_x[i] + centers_x[i + 1]) / 2
            mid_x[split] = True

    if not mid_x:
        return [items]

    boundaries = sorted(mid_x)
    columns: list[list[dict]] = [[] for _ in range(len(boundaries) + 1)]

    for item in items:
        cx = _bbox_center_x(item["bbox"])
        col_idx = next((i for i, b in enumerate(boundaries) if cx < b), len(boundaries))
        columns[col_idx].append(item)

    # Sort each column in reading order
    for col in columns:
        col.sort(key=lambda i: (_bbox_center_y(i["bbox"]), _bbox_center_x(i["bbox"])))

    return [col for col in columns if col]


def classify_blocks(
    items: list[dict],
    heading_size_ratio: float = 1.4,
) -> list[TextBlock]:
    """Classify OCR results into semantic blocks (headings, paragraphs, etc).

    Uses heuristics based on bbox dimensions and position.
    """
    if not items:
        return []

    heights = [_bbox_height(i["bbox"]) for i in items]
    median_h = statistics.median(heights) if heights else 20

    blocks: list[TextBlock] = []
    for item in sort_reading_order(items):
        h = _bbox_height(item["bbox"])
        text = item["text"].strip()

        if not text:
            continue

        if h >= median_h * heading_size_ratio:
            block_type = "heading"
        elif text.startswith("- ") or text.startswith("* ") or text[0].isdigit():
            block_type = "list-item"
        else:
            block_type = "paragraph"

        blocks.append(TextBlock(
            type=block_type,
            text=text,
            bbox=item["bbox"],
            confidence=item.get("confidence"),
        ))

    return blocks


def detect_tables(
    items: list[dict],
    col_tolerance: float = 15.0,
    min_rows: int = 2,
) -> list[Table]:
    """Detect simple tables from aligned text columns.

    Looks for vertically aligned bounding boxes that form a grid.

    Args:
        items: OCR results with "bbox" keys.
        col_tolerance: Max X deviation to consider items aligned in a column.
        min_rows: Minimum number of rows to consider a table.

    Returns:
        List of detected tables.
    """
    if len(items) < min_rows * 2:
        return []

    sorted_items = sort_reading_order(items)

    # Group items into rows
    heights = [_bbox_height(i["bbox"]) for i in sorted_items]
    median_h = statistics.median(heights) if heights else 20
    row_threshold = median_h * 0.3

    rows: list[list[dict]] = [[sorted_items[0]]]
    for item in sorted_items[1:]:
        prev_y = _bbox_center_y(rows[-1][-1]["bbox"])
        if abs(_bbox_center_y(item["bbox"]) - prev_y) <= row_threshold:
            rows[-1].append(item)
        else:
            rows.append([item])

    if len(rows) < min_rows:
        return []

    # Check if items within each row share similar X positions across rows
    row_x_groups: list[list[list[float]]] = []
    for row in rows:
        row.sort(key=lambda i: _bbox_center_x(i["bbox"]))
        row_x_groups.append([_bbox_center_x(i["bbox"]) for i in row])

    # Simple heuristic: if most rows have 2+ items and align vertically
    min_cols = min(len(g) for g in row_x_groups)
    max_cols = max(len(g) for g in row_x_groups)

    if min_cols < 2 or max_cols - min_cols > 2:
        return []  # not a grid

    # Build cells
    table = Table()
    for i, row in enumerate(rows):
        table.cells.append([item["text"] for item in row])

    if table.cells and table.cells[0]:
        x_coords = [item["bbox"][0][0] for row in rows for item in row]
        y_coords = [item["bbox"][0][1] for row in rows for item in row]
        x2_coords = [item["bbox"][2][0] for row in rows for item in row]
        y2_coords = [item["bbox"][2][1] for row in rows for item in row]
        table.bbox = [
            [min(x_coords), min(y_coords)],
            [max(x2_coords), min(y_coords)],
            [max(x2_coords), max(y2_coords)],
            [min(x_coords), max(y2_coords)],
        ]

    return [table]


def analyze_image(items: list[dict]) -> dict:
    """Full layout analysis of OCR results.

    Returns a structured dict with columns, blocks, and tables.
    """
    ordered = sort_reading_order(items)
    columns = detect_columns(items)
    blocks = [
        {
            "type": b.type,
            "text": b.text,
            "confidence": b.confidence,
        }
        for b in classify_blocks(ordered)
    ]
    tables = [
        {"cells": t.cells, "bbox": t.bbox}
        for t in detect_tables(ordered)
    ]

    return {
        "columns": len(columns),
        "blocks": blocks,
        "tables": tables,
    }
