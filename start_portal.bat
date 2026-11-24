@echo off
title Scout Intelligence Portal
cd /d "%~dp0"
echo.
echo   Starting Scout Intelligence Portal...
echo   Auto-detecting available port and opening browser...
echo.
python api.py
pause
