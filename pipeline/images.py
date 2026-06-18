"""تحميل وضغط وتسمية صور المنتجات."""

from __future__ import annotations

import random
import time
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

from pipeline.constants import HEADERS, SCRAPE_SETTINGS


def image_filename(product_id: int) -> str:
    width = max(3, len(str(product_id)))
    return f"product_{product_id:0{width}d}.webp"


def images_folder_from_excel(excel_filename: str) -> str:
    """اسم مجلد الصور من اسم ملف Excel (بدون الامتداد)."""
    stem = Path((excel_filename or "").strip()).stem
    return stem or "product_images"


def image_relative_path(images_folder: str, product_id: int) -> str:
    return f"{images_folder}/{image_filename(product_id)}"


def _throttle():
    delay = SCRAPE_SETTINGS["delay_between_requests"]
    time.sleep(random.uniform(delay * 0.8, delay * 1.2))


def _prepare_image(img: Image.Image) -> Image.Image:
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        return img.convert("RGBA")
    return img.convert("RGB")


def _resize_to_max(img: Image.Image, max_dimension: int) -> Image.Image:
    width, height = img.size
    longest = max(width, height)
    if longest <= max_dimension:
        return img
    scale = max_dimension / longest
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return img.resize(new_size, Image.Resampling.LANCZOS)


def _encode_webp(img: Image.Image, quality: int) -> bytes:
    buffer = BytesIO()
    img.save(buffer, "WEBP", quality=quality)
    return buffer.getvalue()


def _compress_webp(img: Image.Image) -> bytes:
    max_bytes = SCRAPE_SETTINGS["max_image_bytes"]
    quality_start = SCRAPE_SETTINGS["webp_quality_start"]
    quality_min = SCRAPE_SETTINGS["webp_quality_min"]
    min_dimension = SCRAPE_SETTINGS["min_image_dimension"]

    working = _resize_to_max(img, SCRAPE_SETTINGS["max_image_dimension"])

    for _ in range(4):
        low, high = quality_min, quality_start
        best_data: bytes | None = None

        while low <= high:
            mid = (low + high) // 2
            data = _encode_webp(working, mid)
            if len(data) <= max_bytes:
                best_data = data
                low = mid + 1
            else:
                high = mid - 1

        if best_data is None:
            best_data = _encode_webp(working, quality_min)

        if len(best_data) <= max_bytes or min(working.size) <= min_dimension:
            return best_data

        width, height = working.size
        next_width = max(min_dimension, int(width * 0.9))
        next_height = max(min_dimension, int(height * 0.9))
        if next_width >= width and next_height >= height:
            return best_data
        working = working.resize((next_width, next_height), Image.Resampling.LANCZOS)

    return best_data if best_data is not None else _encode_webp(working, quality_min)


def _save_webp(image_bytes: bytes, path: Path) -> int:
    with Image.open(BytesIO(image_bytes)) as img:
        prepared = _prepare_image(img)
        data = _compress_webp(prepared)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return path.stat().st_size


def download_product_image(
    url: str,
    path: Path,
    session: requests.Session,
    retries: int = 3,
) -> tuple[bool, int]:
    if not url:
        return False, 0
    original_size = 0
    for attempt in range(retries):
        try:
            _throttle()
            response = session.get(url, headers=HEADERS, timeout=20)
            response.raise_for_status()
            original_size = len(response.content)
            saved = _save_webp(response.content, path)
            return True, max(0, original_size - saved)
        except Exception:
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
    return False, 0


def remove_images_in_range(images_dir: Path, id_start: int, id_end: int) -> None:
    if id_end < id_start:
        return
    for product_id in range(id_start, id_end + 1):
        path = images_dir / image_filename(product_id)
        if path.exists():
            path.unlink()


def move_orphan_images_to_backup(images_dir: Path, keep_ids: set[int], backup_dir: Path) -> int:
    if not images_dir.exists():
        return 0
    backup_dir.mkdir(parents=True, exist_ok=True)
    removed = 0
    for file in images_dir.glob("product_*.webp"):
        try:
            pid = int(file.stem.split("_")[1])
        except (IndexError, ValueError):
            continue
        if pid not in keep_ids:
            target = backup_dir / file.name
            file.rename(target)
            removed += 1
    return removed
