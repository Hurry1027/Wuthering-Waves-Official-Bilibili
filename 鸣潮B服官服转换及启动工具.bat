@echo off
title=鸣潮B服-官服转换工具2

python --version >nul 2>&1
if %errorlevel% equ 0 (
    REM Python 已安装
) else (
    REM Python 未安装
    echo 未安装 Python 请安装Python
    start https://www.python.org/downloads/
    exit /b
)

python switch.py
timeout /t 3 >nul