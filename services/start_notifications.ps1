$env:PYTHONPATH = "D:\SentinelAI"

uvicorn services.notifications.main:app --host 127.0.0.1 --port 8104