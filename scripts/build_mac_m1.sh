#!/usr/bin/env bash
# بناء نسخة macOS Apple Silicon (M1 / M2 / M3) — arm64 فقط
set -euo pipefail
cd "$(dirname "$0")/.."

ARCH="$(uname -m)"
if [[ "$ARCH" != "arm64" ]]; then
  echo "❌ هذا السكربت مخصص للبناء على Mac Apple Silicon (arm64)."
  echo "   الجهاز الحالي: $ARCH"
  exit 1
fi

PYTHON=".venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON=python3
fi

APP_NAME="ScrapingProduct-M1.app"
ZIP_NAME="ScrapingProduct-M1-macOS-arm64.zip"

echo "==> Mac Apple Silicon (M1/M2/M3) — arm64"
echo "==> تثبيت أدوات البناء..."
"$PYTHON" -m pip install -q pyinstaller

echo "==> تثبيت متصفح Playwright..."
"$PYTHON" -m playwright install chromium-headless-shell

echo "==> بناء التطبيق..."
"$PYTHON" -m PyInstaller scraping_product_m1.spec --noconfirm --clean

if [[ ! -d "dist/$APP_NAME" ]]; then
  echo "❌ لم يُعثر على dist/$APP_NAME"
  exit 1
fi

# تحقق من المعمارية
BINARY="dist/$APP_NAME/Contents/MacOS/ScrapingProduct"
FILE_INFO="$(file "$BINARY")"
if [[ "$FILE_INFO" != *"arm64"* ]]; then
  echo "❌ الملف المبني ليس arm64: $FILE_INFO"
  exit 1
fi

echo "==> ضغط للتوزيع..."
rm -f "dist/$ZIP_NAME"
ditto -c -k --sequesterRsrc --keepParent "dist/$APP_NAME" "dist/$ZIP_NAME"

SIZE_APP="$(du -sh "dist/$APP_NAME" | awk '{print $1}')"
SIZE_ZIP="$(du -sh "dist/$ZIP_NAME" | awk '{print $1}')"

echo ""
echo "✅ تم البناء بنجاح — Mac M1/M2/M3 (arm64)"
echo ""
echo "   التطبيق:  dist/$APP_NAME  ($SIZE_APP)"
echo "   للمشاركة: dist/$ZIP_NAME  ($SIZE_ZIP)"
echo ""
echo "   التثبيت:"
echo "   1. فك الضغط عن $ZIP_NAME"
echo "   2. اسحب ScrapingProduct-M1.app إلى Applications"
echo "   3. كليك يمين → Open (أول مرة فقط)"
echo ""
