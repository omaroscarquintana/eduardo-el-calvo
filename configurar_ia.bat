@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Eduardo el Calvo - Configurar la IA gratis
if not exist ".venv\Scripts\python.exe" (
  echo Primero ejecuta "instalar.bat".
  pause
  exit /b 1
)
".venv\Scripts\python.exe" bot.py --configurar-ia
pause
