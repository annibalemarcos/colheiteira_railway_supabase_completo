@echo off
title Colheiteira_App_Dashboard
mode con: cols=68 lines=14
cd /d "%~dp0"
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat
python scripts\clear_output.py
pause
