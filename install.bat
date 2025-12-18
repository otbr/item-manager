@echo off
title Python Dependencies Installer
echo ======================================
echo   Project Dependencies Installer
echo ======================================
echo.

:: Check if Python exists
py --version >nul 2>&1
if errorlevel 1 (
    echo Python not found.
    echo Please install Python 3.10 or newer before continuing.
    pause
    exit /b
)

:: Show Python version
echo Detected Python version:
py --version
echo.

:: Ask user
set /p choice=Do you want to install the dependencies? (Y/N): 

if /I "%choice%" NEQ "Y" (
    echo Installation canceled by user.
    pause
    exit /b
)

echo.
echo Installing dependencies...
py -m pip install ^
PyQt6==6.7.1 ^
Pillow==10.4.0 ^
torch^>=2.0.0 ^
torchvision^>=0.15.0 ^
opencv-python^>=4.8.0 ^
numpy^>=1.24.0,^<2.0.0 ^
realesrgan^>=0.3.0 ^
basicsr^>=1.4.2 ^
onnxruntime ^
rembg

:: Check install result
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies.
    pause
    exit /b
)

echo.
echo ======================================
echo   Installation completed successfully!
echo ======================================

echo This installer will remove itself.
timeout /t 8 >nul

cmd /c del "%~f0"
exit
