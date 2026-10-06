$env:PYTHONPATH = "D:\SentinelAI"

uvicorn services.inventory.main:app --host 127.0.0.1 --port 8103