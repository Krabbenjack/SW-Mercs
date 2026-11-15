@echo off
cd /d "%~dp0"
python swmercs.py
if errorlevel 1 pause
