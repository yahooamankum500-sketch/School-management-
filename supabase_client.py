# supabase_client.py

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# .env file se variables load karo (local testing ke liye)
load_dotenv()

# Global variable (memory mein ek hi client rahega)
_supabase_client: Client = None

def init_supabase() -> Client:
    """Supabase client ko initialize karne ke liye (App startup par)"""
    global _supabase_client
    
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        # Render par hum service role key use karte hain, warna normal key
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise RuntimeError("❌ SUPABASE_URL and SUPABASE_KEY (or SERVICE_ROLE_KEY) must be set in environment variables")
            
        _supabase_client = create_client(url, key)
        print("✅ Supabase client successfully initialized!")
        
    return _supabase_client

def get_supabase() -> Client:
    """Kisi bhi dusri file mein Supabase client access karne ke liye"""
    global _supabase_client
    if _supabase_client is None:
        return init_supabase()
    return _supabase_client
