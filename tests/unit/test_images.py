"""اختبارات تسمية الصور."""

from pipeline.images import image_filename, image_relative_path, images_folder_from_excel


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
