@echo off
title Colheiteira_App_Dashboard
REM setup.bat - Script de instalação para Windows
echo.
echo ====================================
echo  Instalacao do Colheiteira - Windows
echo ====================================
echo.

REM Verifica Python
echo [1/5] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale Python 3.10+ de: https://www.python.org/
    pause
    exit /b 1
)
echo [OK] Python encontrado
echo.

REM Verifica Node.js
echo [2/5] Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Node.js nao encontrado
    echo Lighthouse nao funcionara. Instale de: https://nodejs.org/
) else (
    echo [OK] Node.js encontrado
)
echo.

REM Ortografia não depende mais de Java
echo [3/5] Verificando motor de ortografia...
echo [OK] Ortografia usa pyspellchecker em Python puro
echo.

REM Cria ambiente virtual
echo [4/5] Criando ambiente virtual...
if exist venv (
    echo Ambiente virtual ja existe
) else (
    python -m venv venv
    echo [OK] Ambiente virtual criado
)
echo.

REM Ativa ambiente e instala dependências
echo [5/5] Instalando dependencias...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo [OK] Dependencias instaladas
echo.

REM Instala e valida Lighthouse
node --version >nul 2>&1
if not errorlevel 1 (
    echo Ajustando PATH do npm global para esta janela...
    for /f "usebackq delims=" %%I in (`npm prefix -g 2^>nul`) do set "NPM_GLOBAL=%%I"
    if defined NPM_GLOBAL set "PATH=%NPM_GLOBAL%;%APPDATA%\npm;%PATH%"

    echo Instalando/atualizando Lighthouse...
    call npm install -g lighthouse@13
    if not errorlevel 1 (
        echo [OK] npm terminou a instalacao do Lighthouse
    ) else (
        echo [AVISO] Erro ao instalar Lighthouse pelo npm
    )

    where lighthouse >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Lighthouse encontrado no PATH
        lighthouse --version
    ) else (
        where lighthouse.cmd >nul 2>&1
        if not errorlevel 1 (
            echo [OK] lighthouse.cmd encontrado no PATH
            lighthouse.cmd --version
        ) else (
            echo [AVISO] Lighthouse instalado, mas ainda nao apareceu no PATH desta janela.
            echo         O app atualizado tambem tenta via npx automaticamente.
            echo         Diagnostico manual: npm prefix -g ^& where lighthouse
        )
    )
)
echo.

REM Cria diretórios
echo Criando estrutura de diretorios...
if not exist output mkdir output
if not exist plugins\ortografia mkdir plugins\ortografia
if not exist plugins\links mkdir plugins\links
if not exist plugins\imagens mkdir plugins\imagens
if not exist plugins\social_media mkdir plugins\social_media
echo [OK] Diretorios criados
echo.

echo ====================================
echo  Instalacao concluida!
echo ====================================
echo.
echo Proximos passos:
echo.
echo 1. Ative o ambiente virtual:
echo    venv\Scripts\activate.bat
echo.
echo 2. Execute uma analise:
echo    python main.py https://seusite.com
echo.
echo 3. Visualize o dashboard:
echo    python server\app.py
echo    Acesse: http://localhost:5840
echo.
echo ====================================
pause
