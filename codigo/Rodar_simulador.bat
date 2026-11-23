@echo off
chcp 65001 >nul
title Simulador 3D do Sistema Solar (A3)
cd /d "%~dp0"
set "PY=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if not exist "%PY%" set "PY=py -3.13"
echo Abrindo o simulador...
%PY% sistema_solar.py
if errorlevel 1 (
  echo.
  echo  O simulador fechou com erro. Confira se o Python 3.12+ e a Ursina 8.3.0 estao instalados.
  pause
)
