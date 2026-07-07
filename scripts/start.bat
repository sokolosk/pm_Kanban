@echo off
REM Start the Kanban Studio application
REM Usage: scripts\start.bat

cd /d "%~dp0.."

echo Starting Kanban Studio...
echo Building and starting Docker container...

docker compose up --build -d

echo.
echo Kanban Studio is running at http://localhost:8000
echo.
echo To stop the application, run: scripts\stop.bat