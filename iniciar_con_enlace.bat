@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Eduardo el Calvo - LIVE (con enlace para LIVE Studio)
rem  Todo va entre parentesis a proposito: asi Windows lee el archivo completo antes de
rem  empezar y no se confunde si la actualizacion automatica cambia este mismo .bat.
(
  if not exist ".venv\Scripts\python.exe" (
    echo Primero ejecuta "instalar.bat".
    pause
    exit /b 1
  )
  ".venv\Scripts\python.exe" actualizador.py
  echo.
  ".venv\Scripts\python.exe" bot.py --enlace
  pause
  exit /b
)
