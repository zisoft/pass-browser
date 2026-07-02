@echo off
REM Installation script for pass-browser native messaging host (Windows)

setlocal enabledelayedexpansion

echo pass-browser Native Messaging Host Installer (Windows)
echo.

REM Check for Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Python not found!
    echo Please install Python 3 from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Found Python: 
python --version

REM Install directory
set INSTALL_DIR=%USERPROFILE%\.local\share\pass-browser
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy the host script
echo Installing native host to %INSTALL_DIR%...
copy /Y "%~dp0pass_browser_host.py" "%INSTALL_DIR%\" >nul
echo [OK] Installed native host script

REM Create wrapper batch file for Windows
echo @echo off > "%INSTALL_DIR%\pass_browser_host.bat"
echo python "%INSTALL_DIR%\pass_browser_host.py" %%* >> "%INSTALL_DIR%\pass_browser_host.bat"

REM Create the manifest file with correct path
set MANIFEST_SRC=%~dp0de.zisoft.pass_browser.windows.json
set TEMP_MANIFEST=%TEMP%\de.zisoft.pass_browser.json

REM Replace INSTALL_PATH with actual path (escape backslashes for JSON)
set ESCAPED_PATH=%INSTALL_DIR:\=\\%
powershell -Command "(Get-Content '%MANIFEST_SRC%') -replace 'INSTALL_PATH', '%ESCAPED_PATH%' | Set-Content '%TEMP_MANIFEST%'"

REM Chrome manifest location
set CHROME_MANIFEST_DIR=%LOCALAPPDATA%\Google\Chrome\User Data\NativeMessagingHosts
if not exist "%CHROME_MANIFEST_DIR%" mkdir "%CHROME_MANIFEST_DIR%"
copy /Y "%TEMP_MANIFEST%" "%CHROME_MANIFEST_DIR%\de.zisoft.pass_browser.json" >nul
echo [OK] Installed manifest for Chrome

REM Edge manifest location
set EDGE_MANIFEST_DIR=%LOCALAPPDATA%\Microsoft\Edge\User Data\NativeMessagingHosts
if not exist "%EDGE_MANIFEST_DIR%" mkdir "%EDGE_MANIFEST_DIR%"
copy /Y "%TEMP_MANIFEST%" "%EDGE_MANIFEST_DIR%\de.zisoft.pass_browser.json" >nul
echo [OK] Installed manifest for Edge

REM Clean up
del "%TEMP_MANIFEST%"

echo.
echo Installation complete!
echo.
echo Next steps:
echo 1. Load the extension in Chrome/Edge:
echo    - Open chrome://extensions/ (or edge://extensions/)
echo    - Enable 'Developer mode'
echo    - Click 'Load unpacked'
echo    - Select: %~dp0..\extension
echo.
echo 2. Get the extension ID from the extensions page
echo.
echo 3. Update the manifest with your extension ID:
echo    Chrome: %CHROME_MANIFEST_DIR%\de.zisoft.pass_browser.json
echo    Edge: %EDGE_MANIFEST_DIR%\de.zisoft.pass_browser.json
echo.
echo    Replace EXTENSION_ID with your actual extension ID
echo.

pause
