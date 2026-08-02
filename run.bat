@echo off
mode con: cols=68 lines=14
title Colheiteira_app_dashboard
REM run.bat - executa uma análise e opcionalmente abre o dashboard

cd /d "%~dp0"

echo.
echo ============================================================
echo        Colheiteira - Analise Web
echo ============================================================
echo.

if "%~1"=="" (
    echo [ERRO] URL nao fornecida
    echo.
    echo Uso: run.bat ^<URL^>
    echo Exemplo: run.bat https://example.com
    echo.
    pause
    exit /b 1
)

set "URL=%~1"

echo %URL% | findstr /i "http://" >nul
if errorlevel 1 (
    echo %URL% | findstr /i "https://" >nul
    if errorlevel 1 set "URL=https://%URL%"
)

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Ajusta PATH do npm global para achar lighthouse.cmd no Windows
for /f "usebackq delims=" %%I in (`npm prefix -g 2^>nul`) do set "NPM_GLOBAL=%%I"
if defined NPM_GLOBAL set "PATH=%NPM_GLOBAL%;%APPDATA%\npm;%PATH%"

echo [OK] Analisando: %URL%
echo.
python main.py "%URL%"

if errorlevel 1 (
    echo.
    echo [ERRO] A analise falhou. Veja os logs acima.
    pause
    exit /b 1
)

echo.
echo [OK] Analise concluida.
echo Dashboard: http://localhost:5840
echo.
set /p RESPOSTA="Deseja iniciar o dashboard agora? (s/n): "
if /i "%RESPOSTA%"=="s" (
    start "" http://localhost:5840
    python server\app.py
)
