@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Voces disponibles
if not exist ".venv\Scripts\python.exe" (
  echo Primero ejecuta "instalar.bat".
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m edge_tts --list-voices | findstr /b /c:"es-"
pause
