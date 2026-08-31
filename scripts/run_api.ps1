.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "backend"
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload

