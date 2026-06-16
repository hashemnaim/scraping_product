# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — نسخة macOS Apple Silicon (M1/M2/M3) arm64."""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata

block_cipher = None
root = Path(SPEC).resolve().parent

datas = [
    (str(root / "app"), "app"),
    (str(root / ".streamlit"), ".streamlit"),
    (str(root / "catalog"), "catalog"),
    (str(root / "pipeline"), "pipeline"),
]
binaries = []
hiddenimports = [
    "streamlit",
    "streamlit.web.cli",
    "streamlit.runtime.scriptrunner.magic_funcs",
    "altair",
    "pandas",
    "numpy",
    "PIL",
    "openpyxl",
    "lxml",
    "playwright",
    "playwright.sync_api",
    "blinker",
    "pipeline",
    "pipeline.brand_matcher",
    "pipeline.maps_runner",
    "pipeline.places_exporter",
    "pipeline.field_mapping",
    "pipeline.match_types",
    "pipeline.review_report",
    "pipeline.run_history",
    "pipeline.category_rules",
    "pipeline.scrape.maps",
    "pipeline.paths",
]

for package in (
    "streamlit",
    "altair",
    "pandas",
    "numpy",
    "playwright",
    "openpyxl",
    "lxml",
    "PIL",
):
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(package)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hidden
    except Exception:
        pass

for meta in ("streamlit", "altair", "pandas", "playwright"):
    try:
        datas += copy_metadata(meta)
    except Exception:
        pass

a = Analysis(
    [str(root / "desktop_launcher.py")],
    pathex=[str(root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ScrapingProduct",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="arm64",
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ScrapingProduct-M1",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="ScrapingProduct-M1.app",
        icon=None,
        bundle_identifier="com.scrapingproduct.desktop.m1",
        info_plist={
            "CFBundleName": "ScrapingProduct",
            "CFBundleDisplayName": "تصدير المنتجات",
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
            "LSArchitecturePriority": ["arm64"],
        },
    )
