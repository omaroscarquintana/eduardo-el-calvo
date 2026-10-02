@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Instalar Eduardo el Calvo
echo ==========================================
echo   Instalando Eduardo el Calvo...
echo ==========================================
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY ( where python >nul 2>nul && set "PY=python" )
if not defined PY (
  echo.
  echo  [ERROR] No encuentro Python. Instalalo desde https://www.python.org/downloads/
  echo  y marca la casilla "Add python.exe to PATH" durante la instalacion.
  pause
  exit /b 1
)
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"
if errorlevel 1 (
  echo  [ERROR] Tu Python es muy viejo o no funciona. Instala Python 3.12 o mas nuevo.
  pause
  exit /b 1
)
echo Creando el entorno del bot (carpeta .venv)...
%PY% -m venv .venv
if errorlevel 1 ( echo [ERROR] No se pudo crear el entorno. & pause & exit /b 1 )
echo Instalando librerias (puede tardar un par de minutos)...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install --upgrade -r requirements.txt
if errorlevel 1 ( echo [ERROR] Fallo la instalacion de librerias. Revisa tu internet. & pause & exit /b 1 )
rem  Crea config.toml (tu configuracion) si todavia no existe. Las actualizaciones nunca lo tocan.
".venv\Scripts\python.exe" -c "from pathlib import Path; from eduardo.configuracion import asegurar_config_usuario as a; a(Path('.').resolve())"
echo.
echo ==========================================
echo   LISTO! Ahora:
echo   1) Abre config.toml y escribe tu usuario de TikTok
echo   2) Prueba con "probar_voz.bat", "simular.bat" y "probar_avatar.bat"
echo   3) Durante tu LIVE abre "iniciar.bat"
echo ==========================================
pause
