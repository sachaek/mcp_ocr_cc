"""Test fixtures."""
from __future__ import annotations

import numpy as np
import pytest


@pytest.fixture
def blank_image():
    """Return a 200x200 white RGB image."""
    return np.ones((200, 200, 3), dtype=np.uint8) * 255


@pytest.fixture
def text_image():
    """Return a 300x100 image with a dark block simulating text area."""
    img = np.ones((100, 300, 3), dtype=np.uint8) * 255
    # Dark line simulating text row
    img[30:50, 20:280] = 0
    img[60:80, 40:260] = 0
    return img


@pytest.fixture
def sample_ocr_items():
    """Mock OCR results simulating a 2-column layout with heading."""
    return [
        {
            "text": "Report Title",
            "confidence": 0.98,
            "bbox": [[100, 10], [300, 10], [300, 40], [100, 40]],
        },
        {
            "text": "Left column text",
            "confidence": 0.95,
            "bbox": [[50, 60], [200, 60], [200, 80], [50, 80]],
        },
        {
            "text": "Right column text",
            "confidence": 0.93,
            "bbox": [[350, 60], [500, 60], [500, 80], [350, 80]],
        },
        {
            "text": "Left detail",
            "confidence": 0.90,
            "bbox": [[50, 100], [200, 100], [200, 120], [50, 120]],
        },
        {
            "text": "Right detail",
            "confidence": 0.88,
            "bbox": [[350, 100], [500, 100], [500, 120], [350, 120]],
        },
    ]
