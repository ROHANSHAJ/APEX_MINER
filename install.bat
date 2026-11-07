@echo off
REM ==============================================================================
REM ApexMiner Studio - Universal Windows Installer
REM Automated installer for Windows 10 & Windows 11.
REM ==============================================================================

echo ==========================================================
echo        ApexMiner Studio - Windows Installer
echo ==========================================================

REM 1. Check Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python 3 was not found in your system PATH.
    echo Please install Python 3.8+ from https://www.python.org/ or the Microsoft Store.
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [OK] Python detected.

REM 2. Install requirements
echo.
echo Installing Python dependencies...
python -m pip install -r requirements.txt --quiet
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Dependency installation encountered an issue. Retrying with --user...
    python -m pip install -r requirements.txt --user
)

REM 3. Download & Configure native miner engines
echo.
echo Fetching native mining engines (Rigel & XMRig for Windows)...
python setup_binaries.py

REM 4. Create convenient launchers
echo @echo off > start_miner.bat
echo set PYTHONPATH=%%~dp0app;%%PYTHONPATH%% >> start_miner.bat
echo python "%%~dp0app\main.py" %%* >> start_miner.bat

echo @echo off > launch_hud.bat
echo start python "%%~dp0visualizer\server.py" >> launch_hud.bat
echo timeout /t 1 >nul >> launch_hud.bat
echo start http://127.0.0.1:8765 >> launch_hud.bat

echo.
echo ==========================================================
echo Installation complete!
echo Launch ApexMiner Studio: double-click start_miner.bat
echo Launch Cyber HUD:       double-click launch_hud.bat
echo ==========================================================
pause
