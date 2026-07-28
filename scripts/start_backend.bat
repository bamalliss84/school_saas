@echo off
title School SaaS Backend

cd /d D:\projects\school_saas\backend

call venv\Scripts\activate

echo.
echo ==========================================
echo      Starting Django Backend...
echo ==========================================
echo.

python manage.py runserver

pause