@echo off
title Colheiteira_App_Dashboard
mode con: cols=68 lines=14
REM run_dashboard.bat - inicia o dashboard Flask na porta 5840

cd /d "%~dp0"

echo.
echo ============================================================
echo        Colheiteira - Dashboard Flask :5840
echo ============================================================
echo.

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Ajusta PATH do npm global para achar lighthouse.cmd no Windows
for /f "usebackq delims=" %%I in (`npm prefix -g 2^>nul`) do set "NPM_GLOBAL=%%I"
if defined NPM_GLOBAL set "PATH=%NPM_GLOBAL%;%APPDATA%\npm;%PATH%"

if not exist output mkdir output
if not exist output\history mkdir output\history

echo Abrindo dashboard em http://localhost:5840
echo.
start "" http://localhost:5840
python server\app.py
pause
