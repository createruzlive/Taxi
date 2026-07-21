@echo off
REM ============================================================
REM  Chaqiruv.exe yasash skripti (Windows uchun)
REM ============================================================
REM  Bu faylni Windows kompyuterda ikki marta bosing yoki
REM  buyruq satridan ishga tushiring:  build_exe.bat
REM
REM  Natija:  dist\Chaqiruv.exe  (bitta mustaqil fayl)
REM  Uni Python o'rnatilmagan kompyuterда ham ishlatsa bo'ladi.
REM ============================================================

echo.
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
echo  TAYYOR!  Fayl:  dist\Chaqiruv.exe
echo  Uni Direktor va Anvar kompyuterlariga nusxalang.
echo ============================================================
pause
