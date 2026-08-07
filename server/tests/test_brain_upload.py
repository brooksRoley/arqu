"""Tests for brain/router.py magic-byte image validation."""

from __future__ import annotations

import pytest

from server.app.brain.router import _is_valid_image_magic


# Minimal valid headers for each supported format
_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
_JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 100
_GIF87 = b"GIF87a" + b"\x00" * 100
_GIF89 = b"GIF89a" + b"\x00" * 100
_WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 100
_BMP = b"BM" + b"\x00" * 100
_FAKE_TEXT = b"This is not an image file at all" + b"\x00" * 100
_ZIP_AS_JPG = b"PK\x03\x04" + b"\x00" * 100  # ZIP magic — common extension-spoof
_RIFF_WAVE = b"RIFF\x00\x00\x00\x00WAVE" + b"\x00" * 100  # audio, not image


class TestIsValidImageMagic:
    def test_png(self):
        assert _is_valid_image_magic(_PNG) is True

    def test_jpeg(self):
        assert _is_valid_image_magic(_JPEG) is True

    def test_gif87(self):
        assert _is_valid_image_magic(_GIF87) is True

    def test_gif89(self):
        assert _is_valid_image_magic(_GIF89) is True

    def test_webp(self):
        assert _is_valid_image_magic(_WEBP) is True

    def test_bmp(self):
        assert _is_valid_image_magic(_BMP) is True

    def test_random_text_rejected(self):
        assert _is_valid_image_magic(_FAKE_TEXT) is False

    def test_zip_disguised_as_jpg_rejected(self):
        assert _is_valid_image_magic(_ZIP_AS_JPG) is False

    def test_empty_bytes_rejected(self):
        assert _is_valid_image_magic(b"") is False

    def test_too_short_rejected(self):
        assert _is_valid_image_magic(b"\x89P") is False

    def test_riff_audio_rejected(self):
        assert _is_valid_image_magic(_RIFF_WAVE) is False
