@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=python"
"%PYTHON%" -m pip install -r requirements.txt
set PYTHONPATH=src
"%PYTHON%" -m lunar_ice_detection.main --config config\demo.yaml
pause
