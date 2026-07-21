@echo off
REM ============================================================
REM  avtostart_ornat.bat
REM  Hodim kompyuterida BIR MARTA bosiladi.
REM  Chaqiruv dasturini Windows bilan birga avtomatik
REM  ishga tushiradigan qiladi ("Hodim" rejimida).
REM ============================================================

cd /d "%~dp0"

REM --- Chaqiruv.exe ni topamiz (shu papka yoki dist\ ichida) ---
set "EXE=%CD%\Chaqiruv.exe"
if not exist "%EXE%" set "EXE=%CD%\dist\Chaqiruv.exe"

if not exist "%EXE%" (
    echo ============================================================
    echo  XATO: Chaqiruv.exe topilmadi.
    echo.
    echo  Bu faylni Chaqiruv.exe bilan bir papkaga qo'ying
    echo  (yoki dist\ papkasi yonida ishga tushiring) va qayta urining.
    echo ============================================================
    pause
    exit /b 1
)

REM --- exe qaysi papkada, o'shani ish papkasi qilamiz ---
for %%I in ("%EXE%") do set "EXEDIR=%%~dpI"

REM --- Startup papkasidagi yorliq manzili ---
set "LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Chaqiruv.lnk"

echo.
echo  Dastur:  %EXE%
echo  Yorliq:  %LNK%
echo.
echo  Avtostart o'rnatilmoqda...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$w = New-Object -ComObject WScript.Shell;" ^
  "$s = $w.CreateShortcut('%LNK%');" ^
  "$s.TargetPath = '%EXE%';" ^
  "$s.Arguments = 'hodim';" ^
  "$s.WorkingDirectory = '%EXEDIR%';" ^
  "$s.WindowStyle = 1;" ^
  "$s.Description = 'Chaqiruv - hodim rejimi';" ^
  "$s.Save()"

if errorlevel 1 (
    echo XATO: Yorliq yaratilmadi.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  TAYYOR!  Endi kompyuter yoqilganda Chaqiruv o'zi
echo  "Hodim" rejimida ishga tushadi.
echo.
echo  Hoziroq sinab ko'rish uchun dasturni ochamizmi? (ha uchun
echo  biror tugma bosing, kerak bo'lmasa oynani yoping)
echo ============================================================
pause
start "" "%EXE%" hodim

echo.
echo  Avtostartni O'CHIRISH kerak bo'lsa: Win+R -^> shell:startup
echo  -^> ochilgan papkadan "Chaqiruv" yorlig'ini o'chiring.
echo.
pause
