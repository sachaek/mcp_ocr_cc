"""Tests for output formatters."""
from __future__ import annotations

import json

from ocr_tool import formatters


SAMPLE_ITEMS = [
    {"text": "Hello", "confidence": 0.95, "bbox": [[0, 0], [10, 0], [10, 5], [0, 5]]},
    {"text": "World", "confidence": 0.90, "bbox": [[0, 10], [15, 10], [15, 15], [0, 15]]},
]

SAMPLE_LAYOUT = {
    "columns": 1,
    "blocks": [
        {"type": "paragraph", "text": "Hello", "confidence": 0.95},
        {"type": "paragraph", "text": "World", "confidence": 0.90},
    ],
    "tables": [],
}


class TestFormatPlain:
    def test_basic(self):
        result = formatters.format_plain(SAMPLE_ITEMS)
        assert result == "Hello\nWorld"

    def test_empty(self):
        assert formatters.format_plain([]) == ""


class TestFormatJson:
    def test_basic(self):
        result = formatters.format_json(SAMPLE_ITEMS)
        data = json.loads(result)
        assert len(data["results"]) == 2
        assert data["results"][0]["text"] == "Hello"

    def test_with_layout(self):
        result = formatters.format_json(SAMPLE_ITEMS, layout=SAMPLE_LAYOUT)
        data = json.loads(result)
        assert "layout" in data
        assert data["layout"]["columns"] == 1
        assert "text" in data  # merged text from layout blocks

    def test_empty(self):
        result = formatters.format_json([])
        data = json.loads(result)
        assert data["results"] == []


class TestFormatCsv:
    def test_basic(self):
        result = formatters.format_csv(SAMPLE_ITEMS)
        assert "text,confidence,bbox" in result
        assert "Hello" in result
        assert "World" in result

    def test_empty(self):
        result = formatters.format_csv([])
        assert "text,confidence,bbox" in result


class TestFormatHtml:
    def test_basic(self):
        result = formatters.format_html(SAMPLE_ITEMS)
        assert "<html>" in result
        assert "<p>Hello</p>" in result

    def test_with_layout_headings(self):
        layout = {
            "blocks": [
                {"type": "heading", "text": "Title"},
                {"type": "paragraph", "text": "Body"},
                {"type": "list-item", "text": "Item 1"},
            ]
        }
        result = formatters.format_html(SAMPLE_ITEMS, layout=layout)
        assert "<h2>Title</h2>" in result
        assert "<p>Body</p>" in result
        assert "<li>Item 1</li>" in result

    def test_empty(self):
        result = formatters.format_html([])
        assert "<html>" in result
