import sys
import logging
import asyncio
sys.path.append("/Users/dankmagician/Documents/New project/ondc-super-seller/backend")

from db import get_supabase_client
from dotenv import load_dotenv

load_dotenv("/Users/dankmagician/Documents/New project/ondc-super-seller/backend/.env")

sb = get_supabase_client()
response = sb.table("profiles").select("id, phone, store_name").execute()
print(response.data)

