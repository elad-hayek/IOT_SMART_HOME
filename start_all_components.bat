@echo off
REM Batch file to start all components of the Smart Home Climate Control System
REM Each component runs in its own terminal window

setlocal enabledelayedexpansion

echo ============================================================
echo Smart Home Climate Control System - Starting All Components
echo ============================================================
echo.

REM Start Data Manager
echo Starting Data Manager...
start "Data Manager" cmd /k python manager/data_manager.py
timeout /t 2 /nobreak

REM Start DHT Emulators
echo Starting DHT Emulators...
start "DHT Living Room" cmd /k python emulators/dht_emulator.py
start "DHT Bedroom" cmd /k python emulators/dht_emulator.py bedroom
timeout /t 1 /nobreak

REM Start Thermostat Controller
echo Starting Thermostat Controller...
start "Thermostat Controller" cmd /k python emulators/thermostat_emulator.py
timeout /t 1 /nobreak

REM Start AC Relay
echo Starting AC Relay...
start "AC Relay" cmd /k python emulators/relay_emulator.py
timeout /t 1 /nobreak

REM Start GUI Dashboard
echo Starting GUI Dashboard...
start "GUI Dashboard" cmd /k python gui/gui_main.py

echo.
echo ============================================================
echo All components started in separate terminal windows!
echo ============================================================
echo.
pause
