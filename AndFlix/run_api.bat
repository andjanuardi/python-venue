@echo off
cd /d E:\python-venue\AndFlix
"C:\Users\Andri Januardi\AppData\Local\Programs\Python\Python312\python.exe" -m uvicorn api.server:app --host 127.0.0.1 --port 8000
