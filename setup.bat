@echo off
SETLOCAL EnableDelayedExpansion

echo ===========================================
echo   ML Environment Setup Initializing...
echo ===========================================

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH. 
    echo Please install Python and try again.
    pause
    exit /b
)

:: 2. Create folder structure
echo [1/4] Creating project folders...
if not exist "data" mkdir data
if not exist "notebooks" mkdir notebooks
if not exist "src" mkdir src
if not exist "models" mkdir models
echo    - /data, /notebooks, /src, /models created.

:: 3. Create Virtual Environment
echo [2/4] Creating virtual environment (venv)...
python -m venv venv
echo    - Virtual environment "venv" created.

:: 4. Activate and Install Packages
echo [3/4] Installing ML libraries (this may take a minute)...
call .\venv\Scripts\activate

:: Upgrading pip first
python -m pip install --upgrade pip >nul

:: Installing the essentials
:: numpy, pandas: Data manipulation
:: matplotlib, seaborn: Visualization
:: scikit-learn: Machine Learning
:: jupyter: Notebooks
pip install numpy pandas matplotlib seaborn scikit-learn jupyter

echo [4/4] Generating requirements.txt...
pip freeze > requirements.txt

echo ===========================================
echo   SETUP COMPLETE!
echo ===========================================
echo To start working:
echo 1. Run: .\venv\Scripts\activate
echo 2. Run: jupyter notebook
echo ===========================================
pause