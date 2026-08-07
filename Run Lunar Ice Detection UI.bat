@echo off
cd /d "%~dp0"
set "PYTHON=python"
"%PYTHON%" -m pip install -r requirements.txt
set PYTHONPATH=src
"%PYTHON%" -m streamlit run app.py --server.port 8502
pause
