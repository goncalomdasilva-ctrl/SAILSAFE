@echo off
title SAILSAFE - servidor local
echo.
echo   SAILSAFE - a servir em http://localhost:8000
echo   Fecha esta janela para parar.
echo.
start "" http://localhost:8000
py -m http.server 8000 2>nul || python -m http.server 8000
