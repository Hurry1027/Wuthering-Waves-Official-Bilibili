@echo off
title=����B��-�ٷ�ת������

python --version >nul 2>&1
if %errorlevel% equ 0 (
    REM Python �Ѱ�װ
) else (
    REM Python δ��װ
    echo δ��װ Python �밲װPython
    start https://www.python.org/downloads/
    exit /b
)

python switching.py
pause