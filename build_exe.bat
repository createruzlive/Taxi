@echo off
REM ============================================================
REM  Chaqiruv.exe yasash skripti (Windows uchun)
REM ============================================================
REM  Bu faylni chaqiruv.py bilan BIR PAPKADA saqlang va
REM  ikki marta bosing (yoki cmd dan ishga tushiring).
REM
REM  Natija:  dist\Chaqiruv.exe  (bitta mustaqil fayl)
REM ============================================================

REM --- Skriptning o'z papkasiga o'tamiz (juda muhim!) ---
cd /d "%~dp0"

echo.
echo  Ishchi papka:  %CD%
echo.

REM --- chaqiruv.py shu papkada bormi tekshiramiz ---
if not exist "chaqiruv.py" (
    echo ============================================================
    echo  XATO: Shu papkada "chaqiruv.py" fayli topilmadi.
    echo.
    echo  Sabab: build_exe.bat "chaqiruv.py" bilan bir papkada
    echo         bo'lishi kerak.
    echo.
    echo  Yechim:
    echo   1) Loyihani to'liq yuklab oling (Code -^> Download ZIP)
    echo      va ZIP ichidan HAMMA fayllarni bitta papkaga chiqaring.
    echo   2) chaqiruv.py va build_exe.bat bir papkada turishi kerak.
    echo   3) Shu papkadagi build_exe.bat ni qayta ishga tushiring.
    echo ============================================================
    pause
    exit /b 1
)

echo [1/3] Python tekshirilmoqda...
python --version
if errorlevel 1 (
    echo XATO: Python topilmadi. https://python.org dan o'rnating
    echo        va "Add Python to PATH" belgisini qo'ying.
    pause
    exit /b 1
)

echo.
echo [2/3] PyInstaller o'rnatilmoqda (bir marta)...
python -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo XATO: PyInstaller o'rnatilmadi. Internetni tekshiring.
    pause
    exit /b 1
)

echo.
echo [3/3] Chaqiruv.exe yasalmoqda...
python -m PyInstaller --onefile --windowed --name Chaqiruv --clean chaqiruv.py
if errorlevel 1 (
    echo XATO: Yasab bo'lmadi.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  TAYYOR!  Fayl:  %CD%\dist\Chaqiruv.exe
echo  Uni Direktor va Hodim kompyuterlariga nusxalang.
echo ============================================================
pause
