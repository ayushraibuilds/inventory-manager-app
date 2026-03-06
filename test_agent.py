import sys
import logging
import asyncio
sys.path.append("/Users/dankmagician/Documents/New project/ondc-super-seller/backend")

logging.basicConfig(level=logging.INFO)

async def run():
    from agent import process_whatsapp_message
    from dotenv import load_dotenv
    load_dotenv("/Users/dankmagician/Documents/New project/ondc-super-seller/backend/.env")
    
    seller_id = "test-seller-123"
    message = "add 5 apples for 100rs"
    print(f"Testing message: {message}")
    
    try:
        result = await asyncio.to_thread(process_whatsapp_message, message, seller_id, [])
        print("RESULT:")
        print(result)
    except Exception as e:
        print(f"CRASH: {e}")

asyncio.run(run())
