@echo off
setlocal

title Python Dependencies Installer

:: ===============================
:: CHECK PYTHON
:: ===============================
py --version >nul 2>&1
if %errorlevel%==0 (
    echo Python already installed.
    py --version
    goto INSTALL_DEPS
)

echo Python not found.
echo Downloading Python installer...

:: ===============================
:: DOWNLOAD PYTHON INSTALLER
:: ===============================
set PYTHON_VERSION=3.10.11
set PYTHON_INSTALLER=python-%PYTHON_VERSION%-amd64.exe
set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/%PYTHON_INSTALLER%

powershell -Command ^
"Invoke-WebRequest '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%'"

if not exist %PYTHON_INSTALLER% (
    echo Failed to download Python installer.
    pause
    exit /b
)

echo Installing Python %PYTHON_VERSION%...

:: ===============================
:: INSTALL PYTHON SILENTLY
:: ===============================
%PYTHON_INSTALLER% ^
    /quiet ^
    InstallAllUsers=1 ^
    PrependPath=1 ^
    Include_test=0

:: ===============================
:: WAIT FOR INSTALL
:: ===============================
timeout /t 10 >nul

:: ===============================
:: VERIFY INSTALL
:: ===============================
py --version >nul 2>&1
if errorlevel 1 (
    echo Python installation failed.
    pause
    exit /b
)

echo Python installed successfully!
py --version

del %PYTHON_INSTALLER%

:INSTALL_DEPS
echo.
echo Installing dependencies...

py -m pip install --upgrade pip

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

echo.
echo Installation completed successfully!
pause
