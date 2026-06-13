"""تثبيت Chromium لـ Playwright على السيرفر (Streamlit Cloud)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_BROWSER_TARGETS = ("chromium-headless-shell", "chromium")
_BROWSER_GLOBS = (
    "chromium_headless_shell-*/chrome-linux/headless_shell",
    "chromium_headless_shell-*/chrome-linux64/headless_shell",
    "chromium-*/chrome-linux64/chrome",
    "chromium-*/chrome-linux/chrome",
    "chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium",
    "chromium-*/chrome-win/chrome.exe",
)


def _browsers_cache_dir() -> Path:
    cache = Path.home() / ".cache" / "ms-playwright"
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(cache)
    return cache


def _chromium_installed() -> bool:
    cache = _browsers_cache_dir()
    return any(cache.glob(pattern) for pattern in _BROWSER_GLOBS)


def _run_install(target: str) -> str:
    proc = subprocess.run(
        [sys.executable, "-m", "playwright", "install", target],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if proc.returncode != 0:
        return (proc.stderr or proc.stdout or f"failed: {target}").strip()
    return ""


def ensure_playwright_chromium() -> None:
    """ثبّت Chromium / headless shell إن لم يكونا موجودين."""
    if _chromium_installed():
        return

    errors: list[str] = []
    for target in _BROWSER_TARGETS:
        err = _run_install(target)
        if err:
            errors.append(err)
        if _chromium_installed():
            return

    detail = " | ".join(errors) if errors else "unknown error"
    cache = _browsers_cache_dir()
    raise RuntimeError(
        "فشل تنزيل متصفح Instashop (Chromium headless shell). "
        f"تفاصيل: {detail}. المسار: {cache}"
    )
