"""اختبارات تسمية الصور والضغط."""

import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image

from pipeline.constants import SCRAPE_SETTINGS
from pipeline.images import _save_webp, image_filename, image_relative_path, images_folder_from_excel


def test_filename_padding_three_digits():
    assert image_filename(1) == "product_001.webp"
    assert image_filename(86) == "product_086.webp"


def test_filename_expands_beyond_999():
    assert image_filename(1000) == "product_1000.webp"


def test_relative_path():
    assert image_relative_path("fruits_images", 7) == "fruits_images/product_007.webp"


def test_images_folder_from_excel():
    assert images_folder_from_excel("fruits.xlsx") == "fruits"
    assert images_folder_from_excel("products.xlsx") == "products"
    assert images_folder_from_excel("") == "product_images"


def _make_image_bytes(width: int, height: int) -> bytes:
    image = Image.new("RGB", (width, height), color=(220, 40, 80))
    for x in range(0, width, 12):
        for y in range(0, height, 12):
            image.putpixel((x, y), (x % 255, y % 255, (x + y) % 255))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_save_webp_limits_large_image_to_max_bytes():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "large.webp"
        saved_size = _save_webp(_make_image_bytes(1800, 1800), path)

        assert path.exists()
        assert saved_size <= SCRAPE_SETTINGS["max_image_bytes"]


def test_save_webp_keeps_small_image_within_limit():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "small.webp"
        saved_size = _save_webp(_make_image_bytes(120, 120), path)

        assert path.exists()
        assert saved_size <= SCRAPE_SETTINGS["max_image_bytes"]
