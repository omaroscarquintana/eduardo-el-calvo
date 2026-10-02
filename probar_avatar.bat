@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Eduardo el Calvo - Prueba del avatar
if not exist ".venv\Scripts\python.exe" (
  echo Primero ejecuta "instalar.bat".
  pause
  exit /b 1
)
".venv\Scripts\python.exe" bot.py --avatar-prueba --sin-esperas
pause
