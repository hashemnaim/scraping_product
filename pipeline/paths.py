"""مسارات المشروع — وضع التطوير ووضع التطبيق المجمّع (PyInstaller)."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

APP_NAME = "ScrapingProduct"


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def resource_root() -> Path:
    """ملفات مضمّنة للقراءة فقط داخل الحزمة."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent.parent


def app_root() -> Path:
    """مجلد العمل القابل للكتابة (إخراج، بيانات، كتالوج)."""
    override = os.environ.get("SCRAPING_PRODUCT_ROOT")
    if override:
        return Path(override)
    if is_frozen():
        if sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / APP_NAME
        if sys.platform == "win32":
            return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / APP_NAME
        return Path.home() / f".{APP_NAME.lower()}"
    return Path(__file__).resolve().parent.parent


def project_root() -> Path:
    return app_root()


def catalog_dir() -> Path:
    return project_root() / "catalog"


def ensure_user_layout() -> Path:
    """أنشئ مجلدات المستخدم وانسخ الكتالوج الافتراضي عند أول تشغيل."""
    root = app_root()
    for name in ("output", "data", "catalog"):
        (root / name).mkdir(parents=True, exist_ok=True)

    if not is_frozen():
        return root

    bundled = resource_root() / "catalog"
    target = root / "catalog"
    if not bundled.is_dir():
        return root

    for item in bundled.iterdir():
        dest = target / item.name
        if dest.exists():
            continue
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    return root
