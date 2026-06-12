"""تحميل وضغط وتسمية صور المنتجات."""

from __future__ import annotations

import os
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


def image_relative_path(images_folder: str, product_id: int) -> str:
    return f"{images_folder}/{image_filename(product_id)}"


def _throttle():
    delay = SCRAPE_SETTINGS["delay_between_requests"]
    time.sleep(random.uniform(delay * 0.8, delay * 1.2))


def _save_webp(image_bytes: bytes, path: Path) -> int:
    with Image.open(BytesIO(image_bytes)) as img:
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path, "WEBP", quality=SCRAPE_SETTINGS["webp_quality"])
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
