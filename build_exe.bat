@echo off
REM ============================================================
REM  Chaqiruv.exe yasash skripti (Windows uchun)
REM  Bu faylni chaqiruv.py bilan BIR PAPKADA saqlang va
REM  ikki marta bosing.  Natija:  dist\Chaqiruv.exe
REM ============================================================

cd /d "%~dp0"

echo.
echo  Ishchi papka:  %CD%
echo.

if not exist "chaqiruv.py" goto YOQ

echo [1/3] Python tekshirilmoqda...
python --version
if errorlevel 1 goto YOQPYTHON

echo.
echo [2/3] PyInstaller o'rnatilmoqda (bir marta)...
python -m pip install --upgrade pyinstaller
if errorlevel 1 goto PIPXATO

echo.
echo [3/3] Chaqiruv.exe yasalmoqda...
python -m PyInstaller --onefile --windowed --name Chaqiruv --clean chaqiruv.py
if errorlevel 1 goto BUILDXATO

echo.
echo ============================================================
echo  TAYYOR!  Fayl:  %CD%\dist\Chaqiruv.exe
echo  Uni Direktor va Hodim kompyuterlariga nusxalang.
echo ============================================================
pause
exit /b 0

:YOQ
echo ============================================================
echo  XATO: Shu papkada "chaqiruv.py" fayli yo'q.
echo  build_exe.bat va chaqiruv.py bitta papkada bo'lishi kerak.
echo  Loyihani to'liq yuklab, hamma faylni bitta papkaga qo'ying.
echo ============================================================
pause
exit /b 1

:YOQPYTHON
echo XATO: Python topilmadi. https://python.org dan o'rnating
echo        va "Add Python to PATH" belgisini qo'ying.
pause
exit /b 1

:PIPXATO
echo XATO: PyInstaller o'rnatilmadi. Internetni tekshiring.
pause
exit /b 1

:BUILDXATO
echo XATO: Yasab bo'lmadi. Yuqoridagi xabarlarni o'qing.
pause
exit /b 1
