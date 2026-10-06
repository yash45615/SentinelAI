$env:PYTHONPATH = "D:\SentinelAI"

uvicorn services.payments.main:app --host 127.0.0.1 --port 8102