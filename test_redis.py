import asyncio
import os
import sys

# Add backend to path
sys.path.append("/Users/dankmagician/Documents/New project/ondc-super-seller/backend")

async def test():
    print("Importing redis_client...")
    from redis_client import redis_client
    print("Pinging redis...")
    try:
        await redis_client.ping()
        print("Ping successful")
    except Exception as e:
        print(f"Ping failed: {e}")

asyncio.run(test())
