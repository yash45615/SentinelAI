$env:PYTHONPATH = "D:\SentinelAI"

uvicorn services.orders.main:app --host 127.0.0.1 --port 8101