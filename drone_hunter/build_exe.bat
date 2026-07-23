@echo off
echo ========================================================
echo   Building Drone Hunter Standalone Windows Executable
echo ========================================================
echo.

python -m PyInstaller --noconfirm --onedir --windowed --name "DroneHunter" --add-data "src;src" main.py

echo.
echo ========================================================
echo   Build Completed! 
echo   Executable location: dist\DroneHunter\DroneHunter.exe
echo ========================================================
pause
