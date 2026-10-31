import os
from dotenv import load_dotenv
from supabase import create_client

# .env file se variables load karo (local testing ke liye)
load_dotenv()

_supabase_client = None

def get_supabase():
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        # Render par hum service role key use karte hain
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables")
            
        _supabase_client = create_client(url, key)
    return _supabase_client
