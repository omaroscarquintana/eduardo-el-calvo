@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Eduardo el Calvo - Ventana del avatar
rem  Plan B para TikTok LIVE Studio: abre el avatar en una ventana sola, con fondo VERDE,
rem  para agregarla en LIVE Studio con "Captura de ventana" + filtro "Chroma Key".
rem  Si cambiaste el puerto en config.toml, cámbialo aquí también.
set "PUERTO=8765"
set "FONDO=verde"
if /i "%~1"=="magenta" set "FONDO=magenta"
set "URL=http://127.0.0.1:%PUERTO%/avatar?fondo=%FONDO%"
set "NAV="
for %%P in ("%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" "%LocalAppData%\Microsoft\Edge\Application\msedge.exe" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" "%LocalAppData%\Google\Chrome\Application\chrome.exe") do (
  if not defined NAV if exist "%%~P" set "NAV=%%~P"
)
if not defined NAV (
  echo No encontré Microsoft Edge ni Google Chrome. Abro el avatar en tu navegador normal.
  start "" "%URL%"
  pause
  exit /b 1
)
echo Abriendo la ventana del avatar con fondo %FONDO% (para el Chroma Key de LIVE Studio)...
echo  - Eduardo tiene que estar abierto (iniciar.bat).
echo  - En LIVE Studio: Agregar fuente, Captura de ventana, elige "Eduardo el Calvo - Avatar".
echo  - Luego clic derecho en la fuente, Filtro avanzado, Agregar, Chroma Key (verde).
echo  - No minimices esta ventana (puede quedar detrás de otras, eso sí funciona).
start "" "%NAV%" --app="%URL%" --window-size=540,960 --user-data-dir="%TEMP%\eduardo_ventana" --autoplay-policy=no-user-gesture-required --no-first-run --no-default-browser-check
timeout /t 6 >nul
