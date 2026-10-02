@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Eduardo el Calvo - Buscar actualizaciones
rem  Actualiza a Eduardo a mano (aunque las actualizaciones automaticas esten apagadas).
rem  Nunca toca config.toml, ia_local.toml, voz_local.toml ni memoria.json.
(
  if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" actualizador.py --forzar
  ) else (
    where py >nul 2>nul && ( py -3 actualizador.py --forzar ) || ( python actualizador.py --forzar )
  )
  pause
  exit /b
)
