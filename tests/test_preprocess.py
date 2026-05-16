"""Tests for preprocessing module."""
from __future__ import annotations

import numpy as np
import pytest

from ocr_tool import preprocess


class TestBinarize:
    def test_binarize_returns_rgb(self, blank_image):
        result = preprocess.binarize(blank_image)
        assert result.shape == blank_image.shape
        assert result.dtype == np.uint8

    def test_binarize_otsu_returns_rgb(self, blank_image):
        result = preprocess.binarize_otsu(blank_image)
        assert result.shape == blank_image.shape
        assert result.dtype == np.uint8


class TestDenoise:
    def test_denoise_returns_same_shape(self, blank_image):
        result = preprocess.denoise(blank_image)
        assert result.shape == blank_image.shape

    def test_bilateral_returns_same_shape(self, blank_image):
        result = preprocess.denoise_bilateral(blank_image)
        assert result.shape == blank_image.shape


class TestCLAHE:
    def test_clahe_returns_rgb(self, blank_image):
        result = preprocess.clahe(blank_image)
        assert result.shape == blank_image.shape
        assert result.dtype == np.uint8


class TestDeskew:
    def test_deskew_returns_same_shape(self, blank_image):
        result = preprocess.deskew(blank_image)
        assert result.shape == blank_image.shape

    def test_deskew_rotated_text(self):
        """Deskew should rotate text to horizontal."""
        h, w = 200, 200
        img = np.ones((h, w, 3), dtype=np.uint8) * 255
        # Draw horizontal line
        img[100:110, 20:180] = 0
        result = preprocess.deskew(img)
        assert result.shape == (h, w, 3)


class TestUpscale:
    def test_upscale_default(self, blank_image):
        result = preprocess.upscale(blank_image)
        assert result.shape == (400, 400, 3)

    def test_upscale_3x(self, blank_image):
        result = preprocess.upscale(blank_image, scale=3.0)
        assert result.shape == (600, 600, 3)

    def test_upscale_1x_no_change(self, blank_image):
        result = preprocess.upscale(blank_image, scale=1.0)
        assert result.shape == blank_image.shape


class TestSharpen:
    def test_sharpen_returns_same_shape(self, blank_image):
        result = preprocess.sharpen(blank_image)
        assert result.shape == blank_image.shape


class TestApplyChain:
    def test_chain_empty(self, blank_image):
        result = preprocess.apply_chain(blank_image, [])
        assert result.shape == blank_image.shape
        assert np.array_equal(result, blank_image)

    def test_chain_single(self, blank_image):
        result = preprocess.apply_chain(blank_image, ["clahe"])
        assert result.shape == blank_image.shape

    def test_chain_multiple(self, blank_image):
        result = preprocess.apply_chain(blank_image, ["clahe", "denoise", "sharpen"])
        assert result.shape == blank_image.shape

    def test_chain_unknown_step(self, blank_image):
        with pytest.raises(ValueError, match="Unknown preprocessing step"):
            preprocess.apply_chain(blank_image, ["nonexistent"])

    def test_to_grayscale(self, blank_image):
        result = preprocess.to_grayscale(blank_image)
        assert result.shape == blank_image.shape

    @pytest.mark.parametrize("step_name", sorted(preprocess.STEPS))
    def test_all_steps_run(self, step_name, text_image):
        """Every registered step should run without error."""
        result = preprocess.apply_chain(text_image, [step_name])
        assert result.dtype == np.uint8
        # upscale changes dimensions — skip shape check for it
        if step_name != "upscale":
            assert result.shape == text_image.shape
