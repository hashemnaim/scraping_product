@echo off
setlocal
cd /d "%~dp0.."

if exist .venv\Scripts\python.exe (
  set PYTHON=.venv\Scripts\python.exe
) else (
  set PYTHON=python
)

echo ==^> Installing build tools...
%PYTHON% -m pip install -q pyinstaller

echo ==^> Installing Playwright browser...
%PYTHON% -m playwright install chromium-headless-shell

echo ==^> Building desktop app...
%PYTHON% -m PyInstaller scraping_product.spec --noconfirm --clean

echo.
echo Done: dist\ScrapingProduct\ScrapingProduct.exe
pause
