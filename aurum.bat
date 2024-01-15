@echo off
:: Activate virtual environment
call .\venv\Scripts\activate

:: Change directory to django_pos
cd django_pos

:: Run Django development server
start python manage.py runserver

:: Wait for a moment to ensure the server is up before opening the browser
timeout /t 5 /nobreak >nul

:: Open browser
start http://127.0.0.1:8000/