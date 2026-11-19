@echo off
chcp 65001 >nul
title MoE-SHD Ultimate Launcher
color 0A

echo ============================================
echo  MoE-SHD 3D Holographic Sandbox - Launcher
echo ============================================
echo.

set "SCRIPT_DIR=%~dp0"

:: ========== Step 0: Clean old processes ==========
echo [0/5] Cleaning old processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 "') do taskkill /F /PID %%a >nul 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000 "') do taskkill /F /PID %%a >nul 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501 "') do taskkill /F /PID %%a >nul 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8502 "') do taskkill /F /PID %%a >nul 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8503 "') do taskkill /F /PID %%a >nul 2>nul
echo  [OK] Done
timeout /t 1 /nobreak >nul
echo.

:: ========== Step 1: Check Python ==========
echo [1/5] Checking Python...
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    pause
    exit /b
)
echo [OK] Python OK
echo.

:: ========== Step 2: Check venv ==========
echo [2/5] Checking virtual environment...
if exist "%SCRIPT_DIR%venv\Scripts\python.exe" (
    echo [OK] venv exists
) else (
    echo Creating virtual environment...
    python -m venv "%SCRIPT_DIR%venv"
)
echo.

:: ========== Step 3: Install dependencies ==========
echo [3/5] Checking dependencies...
if exist "%SCRIPT_DIR%requirements.txt" (
    "%SCRIPT_DIR%venv\Scripts\pip.exe" install -r "%SCRIPT_DIR%requirements.txt" -q
    echo [OK] Dependencies checked
) else (
    echo [WARNING] requirements.txt not found!
)
echo.

:: ========== Step 4: Start Backend ==========
echo [4/5] Starting Backend API...
set "BACKEND_FILE=backend_service.py"
if exist "%SCRIPT_DIR%backend_service_2.py" set "BACKEND_FILE=backend_service_2.py"

start "" /min "%SCRIPT_DIR%venv\Scripts\python.exe" "%SCRIPT_DIR%%BACKEND_FILE%"
echo [OK] Backend started (port 8000)
timeout /t 3 /nobreak >nul
echo.

:: ========== Step 5: Start all frontends ==========
echo [5/5] Starting frontends...

:: 注意：pages 文件夹已改名为 _pages
start "" /min "%SCRIPT_DIR%venv\Scripts\python.exe" "%SCRIPT_DIR%_pages\02_Honeypot_Attack.py"
echo [OK] Flask honeypot started (port 5000)

start "" /min "%SCRIPT_DIR%venv\Scripts\streamlit.exe" run "%SCRIPT_DIR%_pages\01_Algorithm_Workbench.py" --server.port 8501 --server.address 0.0.0.0 --server.headless true
echo [OK] Streamlit workbench started (port 8501)

start "" /min "%SCRIPT_DIR%venv\Scripts\streamlit.exe" run "%SCRIPT_DIR%_pages\03_Command_Center.py" --server.port 8502 --server.address 0.0.0.0 --server.headless true
echo [OK] Streamlit command center started (port 8502)

start "" /min "%SCRIPT_DIR%venv\Scripts\streamlit.exe" run "%SCRIPT_DIR%Home.py" --server.port 8503 --server.address 0.0.0.0 --server.headless true
echo [OK] Unified portal started (port 8503)

echo.
echo ============================================
echo  System Ready! Opening login portal...
echo ============================================
echo.
start "" "http://localhost:8503"

echo  Press any key to close this window (services keep running)...
pause >nul