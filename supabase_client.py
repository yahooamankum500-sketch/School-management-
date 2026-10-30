import os
import psycopg2
from supabase import create_client, Client

# ==========================================
# 1. SUPABASE REST CLIENT (दूसरे कोड के लिए)
# ==========================================
supabase_client = None

def init_supabase():
    global supabase_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if url and key:
        supabase_client = create_client(url, key)
        print("✅ Supabase Client Initialized successfully.")
    else:
        print("⚠️ Supabase credentials missing!")

def get_supabase():
    return supabase_client

# ==========================================
# 2. RAW DATABASE CONNECTION (पहले कोड के लिए)
# ==========================================
def get_conn():
    """
    Connects to Supabase PostgreSQL Database using psycopg2.
    Requires DATABASE_URL in your environment variables.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is missing in environment variables. Cannot connect to PostgreSQL.")
    
    try:
        # Render पर SSL के लिए sslmode='require' जोड़ना सुरक्षित रहता है
        conn = psycopg2.connect(db_url, sslmode='require')
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise e
