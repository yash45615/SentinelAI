$env:PYTHONPATH = "D:\SentinelAI"

uvicorn services.gateway.main:app --host 127.0.0.1 --port 8100