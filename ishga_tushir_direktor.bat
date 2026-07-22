@echo off
REM ============================================================
REM  ishga_tushir_direktor.bat
REM  chaqiruv.py ni "Direktor" rejimida ishga tushiradi.
REM  Ochilganda parol so'raydi, keyin xabar yuborish oynasi chiqadi.
REM  (exe emas - Python skript, shuning uchun Windows Smart App
REM   Control bloklamaydi.)
REM
REM  Talab: kompyuterda Python 3 o'rnatilgan bo'lishi kerak
REM         (https://python.org, "Add Python to PATH" belgilanadi).
REM  Bu faylni chaqiruv.py bilan BIR PAPKADA saqlang.
REM ============================================================

cd /d "%~dp0"

if not exist "chaqiruv.py" goto YOQFILE

REM pythonw = ortiqcha qora konsol oynasi chiqmasin.
set "PY="
where pythonw >nul 2>nul && set "PY=pythonw"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY goto YOQPYTHON

start "" %PY% "chaqiruv.py" direktor
exit /b 0

:YOQFILE
echo ============================================================
echo  XATO: Shu papkada "chaqiruv.py" fayli yo'q.
echo  Bu bat faylni chaqiruv.py bilan bitta papkaga qo'ying.
echo ============================================================
pause
exit /b 1

:YOQPYTHON
echo ============================================================
echo  XATO: Python topilmadi.
echo  https://python.org dan Python 3 ni o'rnating va
echo  o'rnatishda "Add Python to PATH" belgisini qo'ying.
echo ============================================================
pause
exit /b 1
