"""تثبيت Chromium لـ Playwright على السيرفر (Streamlit Cloud)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _browsers_cache_dir() -> Path:
    cache = Path.home() / ".cache" / "ms-playwright"
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(cache)
    return cache


def _chromium_installed() -> bool:
    cache = _browsers_cache_dir()
    patterns = (
        "chromium-*/chrome-linux64/chrome",
        "chromium-*/chrome-linux/chrome",
        "chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium",
        "chromium-*/chrome-win/chrome.exe",
    )
    return any(cache.glob(pattern) for pattern in patterns)


def ensure_playwright_chromium() -> None:
    """ثبّت Chromium إن لم يكن موجوداً (مطلوب على Streamlit Cloud)."""
    if _chromium_installed():
        return

    proc = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "unknown error").strip()
        raise RuntimeError(
            "فشل تنزيل Chromium لـ Instashop. "
            f"تفاصيل: {detail}"
        )

    if not _chromium_installed():
        cache = _browsers_cache_dir()
        raise RuntimeError(
            "Chromium غير موجود بعد playwright install. "
            f"المسار المتوقع تحت {cache}. "
            "جرّب Reboot للتطبيق من Streamlit Cloud."
        )
