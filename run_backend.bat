@echo off
echo Starting Urban Flood Nowcasting API backend...
if exist "backend\venv\Scripts\python.exe" (
    backend\venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
)
