@echo off
TITLE KYNIKOS - Perro Guardian de Julian Juarez
echo [KYNIKOS] Iniciando conciencia...
cd /d "C:\Users\QUINTANA\sistemas\NANOBOT"
poetry run python -m uvicorn app.main:app --port 8000 --host 0.0.0.0
pause
