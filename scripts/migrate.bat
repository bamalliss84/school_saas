@echo off
title Django Migrate

cd /d D:\projects\school_saas\backend

call venv\Scripts\activate

python manage.py migrate

pause