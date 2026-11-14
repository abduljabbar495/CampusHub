@echo off
cd /d "%~dp0"
if not exist venv python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
python manage.py makemigrations accounts courses attendance
python manage.py migrate
python manage.py seed_demo
echo.
echo Open http://127.0.0.1:8000/  in your browser
python manage.py runserver 0.0.0.0:8000
pause
