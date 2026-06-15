"""تثبيت Chromium لـ Playwright على السيرفر (Streamlit Cloud)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import playwright


def _browsers_cache_dir() -> Path:
    cache = Path.home() / ".cache" / "ms-playwright"
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(cache))
    return cache


def _browser_revision(name: str) -> str:
    browsers_json = (
        Path(playwright.__file__).parent / "driver" / "package" / "browsers.json"
    )
    data = json.loads(browsers_json.read_text())
    for entry in data["browsers"]:
        if entry["name"] == name:
            return str(entry["revision"])
    raise RuntimeError(f"Browser {name!r} not found in Playwright browsers.json")


def _cache_folder_name(headless: bool) -> str:
    if headless:
        revision = _browser_revision("chromium-headless-shell")
        return f"chromium_headless_shell-{revision}"
    revision = _browser_revision("chromium")
    return f"chromium-{revision}"


def _executable_candidates(headless: bool) -> list[Path]:
    cache = _browsers_cache_dir()
    folder = cache / _cache_folder_name(headless)
    if not folder.is_dir():
        return []
    if headless:
        patterns = (
            "chrome-headless-shell-*/chrome-headless-shell",
            "chrome-headless-shell-*/headless_shell",
            "chrome-linux*/headless_shell",
        )
    else:
        patterns = (
            "chrome-*/chrome",
            "chrome-mac*/Chromium.app/Contents/MacOS/Chromium",
            "chrome-mac-*/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
            "chrome-win*/chrome.exe",
        )
    found: list[Path] = []
    for pattern in patterns:
        found.extend(folder.glob(pattern))
    return found


def _browser_ready(headless: bool) -> bool:
    return any(path.is_file() for path in _executable_candidates(headless))


def _purge_stale_browsers(headless: bool) -> None:
    """احذف نسخ Chromium القديمة (مثلاً بعد تغيير إصدار Playwright)."""
    cache = _browsers_cache_dir()
    if not cache.is_dir():
        return
    keep = {_cache_folder_name(headless)}
    for child in list(cache.iterdir()):
        if not child.is_dir() or child.name in keep:
            continue
        if child.name.startswith(("chromium-", "chromium_headless_shell-")):
            shutil.rmtree(child, ignore_errors=True)


def _run_install(target: str) -> str:
    cache = _browsers_cache_dir()
    env = {**os.environ, "PLAYWRIGHT_BROWSERS_PATH": str(cache)}
    proc = subprocess.run(
        [sys.executable, "-m", "playwright", "install", target],
        capture_output=True,
        text=True,
        timeout=600,
        env=env,
    )
    if proc.returncode != 0:
        return (proc.stderr or proc.stdout or f"failed: {target}").strip()
    return ""


def ensure_playwright_chromium(headless: bool | None = None) -> None:
    """ثبّت متصفح Playwright المطلوب لإنستاشوب."""
    if headless is None:
        from pipeline.constants import SCRAPE_SETTINGS

        headless = bool(SCRAPE_SETTINGS["instashop_headless"])

    if _browser_ready(headless):
        return

    _purge_stale_browsers(headless)

    targets = ("chromium-headless-shell",) if headless else ("chromium",)
    errors: list[str] = []
    for target in targets:
        err = _run_install(target)
        if err:
            errors.append(err)
        if _browser_ready(headless):
            return

    detail = " | ".join(errors) if errors else "unknown error"
    expected = _cache_folder_name(headless)
    cache = _browsers_cache_dir()
    raise RuntimeError(
        "فشل تنزيل متصفح Instashop. "
        f"المطلوب: {expected}. تفاصيل: {detail}. الكاش: {cache}"
    )
