@echo off
echo ========================================================
echo   Building Drone Hunter 3D Standalone Windows Executable
echo ========================================================
echo.

python -m PyInstaller --noconfirm --onefile --windowed --name "DroneHunter3DSingle" --add-data "src;src" main_3d.py

echo.
echo ========================================================
echo   Build Completed! 
echo   Executable location: dist\DroneHunter3DSingle.exe
echo ========================================================
pause
