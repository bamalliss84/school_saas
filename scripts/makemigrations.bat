@echo off
title Django MakeMigrations

cd /d D:\projects\school_saas\backend

call venv\Scripts\activate

python manage.py makemigrations

pause