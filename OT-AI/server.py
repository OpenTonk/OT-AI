import streaming
import asyncio

asyncio.run(streaming.startServer('127.0.0.1', 8083))
print("server started")
