@echo off
cd /d "%~dp0"

echo =====================================================
echo ⚙️  Pro Thumbnail Tool — Auto Installer & Builder
echo =====================================================

:: Ensure pip is available
python -m ensurepip --upgrade >nul 2>&1
python -m pip install --upgrade pip setuptools wheel >nul

echo.
echo 📦 Installing dependencies...
echo.

:: Install all libraries listed in requirements.txt
if exist requirements.txt (
    python -m pip install -r requirements.txt
) else (
    echo requirements.txt not found!
)

echo.
echo 🛠️ Installing Nuitka and build requirements...
echo.

python -m pip install --upgrade nuitka zstandard ordered-set >nul

echo.
echo 🚀 Running NuitkaBuilder.bat...
echo.

call "%~dp0NuitkaBuilder.bat"

echo.
echo ✅ All done!
echo Your compiled file will appear as: ProThumbnailTool.exe
echo =====================================================
pause
