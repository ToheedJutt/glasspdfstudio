@echo off
cd /d "%~dp0"
set "PYTHON=.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
  py -3.13 -m venv .venv
)

"%PYTHON%" -c "import flask, fitz, docx, openpyxl, PIL, pptx, pypdf, reportlab" >nul 2>nul
if errorlevel 1 (
  "%PYTHON%" -m pip install -r requirements.txt
)

start "" /min "%PYTHON%" app.py

for /l %%i in (1,1,20) do (
  "%PYTHON%" -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:5055/api/health', timeout=1).read()" >nul 2>nul
  if not errorlevel 1 goto ready
  timeout /t 1 /nobreak >nul
)

:ready
start "" "http://127.0.0.1:5055"
