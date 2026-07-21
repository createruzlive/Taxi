@echo off
REM ============================================================
REM  avtostart_ornat.bat
REM  Hodim kompyuterida BIR MARTA bosiladi.
REM  Chaqiruv dasturini Windows bilan birga avtomatik
REM  ishga tushiradigan qiladi ("Hodim" rejimida, fonda).
REM ============================================================

cd /d "%~dp0"

set "EXE=%CD%\Chaqiruv.exe"
if not exist "%EXE%" set "EXE=%CD%\dist\Chaqiruv.exe"
if not exist "%EXE%" goto YOQ

for %%I in ("%EXE%") do set "EXEDIR=%%~dpI"
set "LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Chaqiruv.lnk"

echo.
echo  Dastur:  %EXE%
echo  Yorliq:  %LNK%
echo.
echo  Avtostart o'rnatilmoqda...

powershell -NoProfile -ExecutionPolicy Bypass -Command "$w = New-Object -ComObject WScript.Shell; $s = $w.CreateShortcut('%LNK%'); $s.TargetPath = '%EXE%'; $s.Arguments = 'hodim'; $s.WorkingDirectory = '%EXEDIR%'; $s.WindowStyle = 1; $s.Description = 'Chaqiruv hodim'; $s.Save()"
if errorlevel 1 goto XATO

echo.
echo  Hodim dasturi hoziroq fonda ishga tushirilmoqda...
start "" "%EXE%" hodim

echo.
echo ============================================================
echo  TAYYOR!  Kompyuter yoqilganda Chaqiruv o'zi "Hodim"
echo  rejimida FONDA ishga tushadi. Oyna ko'rinmaydi.
echo  Direktor xabar yuborganda ekranda pop-up chiqadi.
echo.
echo  O'chirish: Win+R, keyin  shell:startup  yozing,
echo  ochilgan papkadan "Chaqiruv" yorligini o'chiring.
echo ============================================================
pause
exit /b 0

:YOQ
echo ============================================================
echo  XATO: Chaqiruv.exe topilmadi.
echo  Bu faylni Chaqiruv.exe bilan bitta papkaga qo'ying.
echo ============================================================
pause
exit /b 1

:XATO
echo XATO: Yorliq yaratilmadi.
pause
exit /b 1
