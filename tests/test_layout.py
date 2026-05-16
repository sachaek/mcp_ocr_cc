"""Tests for layout analysis module."""
from __future__ import annotations

from ocr_tool import layout


class TestSortReadingOrder:
    def test_empty(self):
        assert layout.sort_reading_order([]) == []

    def test_single_item(self, sample_ocr_items):
        result = layout.sort_reading_order([sample_ocr_items[0]])
        assert len(result) == 1
        assert result[0]["text"] == "Report Title"

    def test_top_to_bottom(self, sample_ocr_items):
        """Items should be sorted top-to-bottom first."""
        result = layout.sort_reading_order(sample_ocr_items)
        texts = [r["text"] for r in result]
        assert texts[0] == "Report Title"

    def test_left_to_right_within_row(self, sample_ocr_items):
        """Items in the same row should be left-to-right."""
        result = layout.sort_reading_order(sample_ocr_items)
        texts = [r["text"] for r in result]
        # Items at y=60: "Left column text" (x=50), "Right column text" (x=350)
        left_idx = texts.index("Left column text")
        right_idx = texts.index("Right column text")
        assert left_idx < right_idx


class TestDetectColumns:
    def test_empty(self):
        assert layout.detect_columns([]) == []

    def test_single_column(self, sample_ocr_items):
        """Single-column (narrow items) should return one column."""
        items = [sample_ocr_items[0]]  # just the heading
        cols = layout.detect_columns(items, min_gap_px=500)
        assert len(cols) == 1

    def test_two_columns(self, sample_ocr_items):
        """Items with a large X gap should split into two columns."""
        cols = layout.detect_columns(sample_ocr_items, min_gap_px=50)
        assert len(cols) == 2


class TestClassifyBlocks:
    def test_empty(self):
        assert layout.classify_blocks([]) == []

    def test_heading_detection(self, sample_ocr_items):
        """Large text should be classified as heading."""
        blocks = layout.classify_blocks(sample_ocr_items, heading_size_ratio=1.0)
        # "Report Title" has bbox height 30, others have 20
        # With ratio=1.0, median=20, so 30 >= 28 → heading
        headings = [b for b in blocks if b.type == "heading"]
        assert len(headings) >= 1

    def test_all_types_present(self, sample_ocr_items):
        blocks = layout.classify_blocks(sample_ocr_items)
        assert len(blocks) > 0
        for b in blocks:
            assert b.type in ("heading", "paragraph", "list-item")
            assert b.text
            assert b.bbox


class TestDetectTables:
    def test_empty(self):
        assert layout.detect_tables([]) == []

    def test_no_table_from_single_row(self, sample_ocr_items):
        """Few items shouldn't trigger table detection."""
        tables = layout.detect_tables(sample_ocr_items[:2], min_rows=3)
        assert len(tables) == 0


class TestAnalyzeImage:
    def test_empty(self):
        result = layout.analyze_image([])
        assert result["columns"] == 0
        assert result["blocks"] == []
        assert result["tables"] == []

    def test_full_analysis(self, sample_ocr_items):
        result = layout.analyze_image(sample_ocr_items)
        assert "columns" in result
        assert "blocks" in result
        assert "tables" in result
        assert len(result["blocks"]) > 0
