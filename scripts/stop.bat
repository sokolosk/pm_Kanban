@echo off
REM Stop the Kanban Studio application
REM Usage: scripts\stop.bat

cd /d "%~dp0.."

echo Stopping Kanban Studio...

docker compose down

echo Kanban Studio has been stopped.