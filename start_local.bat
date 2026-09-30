@echo off
echo ========================================================
echo           EduPulse - CBSE AI Learning Platform
echo ========================================================
echo Starting Backend Server on http://127.0.0.1:8001...
start "EduPulse Backend (FastAPI)" cmd /k "cd backend && venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload"

echo Starting Frontend Server on http://localhost:5173...
start "EduPulse Frontend (Vite)" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers launched!
echo - Frontend:  http://localhost:5173
echo - Backend:   http://127.0.0.1:8001
echo - API Docs:  http://127.0.0.1:8001/docs
echo ========================================================
