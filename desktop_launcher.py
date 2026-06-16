#!/usr/bin/env python3
"""تشغيل التطبيق محلياً كبرنامج سطح مكتب (بدون سيرفر خارجي)."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

PORT = 8501


def _prepare_environment() -> Path:
    from pipeline.paths import ensure_user_layout, is_frozen, resource_root

    root = ensure_user_layout()
    os.environ["SCRAPING_PRODUCT_ROOT"] = str(root)
    os.environ.setdefault("PYTHONPATH", str(resource_root() if is_frozen() else root))
    os.environ.setdefault("INSTASHOP_HEADLESS", "true")
    if is_frozen():
        os.environ.setdefault("STREAMLIT_GLOBAL_DEVELOPMENT_MODE", "false")
    return root


def _bootstrap_playwright() -> None:
    from pipeline.scrape.playwright_bootstrap import ensure_playwright_chromium

    ensure_playwright_chromium()


def _ui_path() -> Path:
    from pipeline.paths import is_frozen, resource_root

    if is_frozen():
        return resource_root() / "app" / "ui.py"
    return Path(__file__).resolve().parent / "app" / "ui.py"


def _streamlit_command(ui: Path, workdir: Path) -> list[str]:
    args = [
        "run",
        str(ui),
        f"--server.port={PORT}",
        "--server.address=localhost",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--global.developmentMode=false",
        "--server.fileWatcherType=none",
    ]
    from pipeline.paths import is_frozen

    if is_frozen():
        # داخل PyInstaller: sys.executable هو نفس ملف .app — نمرّر وضع Streamlit عبر argv
        return [sys.executable, "__streamlit__", *args]
    return [sys.executable, "-m", "streamlit", *args]


def _run_streamlit_child() -> int:
    from streamlit.web import cli as stcli

    sys.argv = ["streamlit", *sys.argv[2:]]
    stcli.main()
    return 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "__streamlit__":
        return _run_streamlit_child()

    workdir = _prepare_environment()
    print("⏳ تجهيز المتصفح لـ Instashop...")
    try:
        _bootstrap_playwright()
    except Exception as exc:
        print(f"تحذير: {exc}", file=sys.stderr)

    ui = _ui_path()
    if not ui.is_file():
        print(f"لم يُعثر على الواجهة: {ui}", file=sys.stderr)
        return 1

    print(f"🚀 تشغيل التطبيق على http://localhost:{PORT}")
    proc = subprocess.Popen(
        _streamlit_command(ui, workdir),
        cwd=str(workdir),
        env=os.environ.copy(),
    )

    def _shutdown(*_args):
        if proc.poll() is None:
            proc.send_signal(signal.SIGTERM)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    for _ in range(40):
        if proc.poll() is not None:
            return proc.returncode or 1
        try:
            import urllib.request

            urllib.request.urlopen(f"http://localhost:{PORT}/_stcore/health", timeout=1)
            break
        except Exception:
            time.sleep(0.25)
    else:
        print("تعذّر الاتصال بخادم Streamlit المحلي.", file=sys.stderr)
        proc.terminate()
        return 1

    webbrowser.open(f"http://localhost:{PORT}")
    return proc.wait()


if __name__ == "__main__":
    raise SystemExit(main())
