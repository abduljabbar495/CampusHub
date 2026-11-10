@echo off
setlocal
cd /d "%~dp0"
if not exist .venv (
  py -3 -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py makemigrations accounts academics campus security
python manage.py migrate
if not exist .superuser_created (
  echo.
  echo Create your administrator account now.
  python manage.py createsuperuser
  type nul > .superuser_created
)
python manage.py runserver
