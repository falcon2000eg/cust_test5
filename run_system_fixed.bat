@echo off
title Customer Issues Management System v2.0.0

echo ================================
echo Customer Issues Management System
echo Version 2.0.0 - Enhanced Edition
echo ================================
echo.
echo Starting system...

cd /d "%~dp0"

python customer_issues_main.py
if %errorlevel% neq 0 (
    echo.
    echo Error: Failed to start the system
    echo Please ensure Python 3.7+ is installed
    echo.
    pause
    exit /b 1
)

echo.
echo System completed.
pause