#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON=".venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON=python3
fi

echo "==> تثبيت أدوات البناء..."
"$PYTHON" -m pip install -q pyinstaller

echo "==> تثبيت متصفح Playwright (للتضمين في أول تشغيل)..."
"$PYTHON" -m playwright install chromium-headless-shell

echo "==> بناء التطبيق..."
"$PYTHON" -m PyInstaller scraping_product.spec --noconfirm --clean

if [[ "$(uname)" == "Darwin" ]]; then
  echo ""
  echo "✅ تم البناء: dist/ScrapingProduct.app"
  echo "   انسخه إلى Applications وشغّله بالنقر المزدوج."
else
  echo ""
  echo "✅ تم البناء: dist/ScrapingProduct/ScrapingProduct.exe"
fi
