@echo off
cd /d %~dp0
call venv\Scripts\activate
set FLASK_APP=app.py
set FLASK_ENV=development
flask run
pause