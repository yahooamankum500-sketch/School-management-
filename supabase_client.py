from config import Config

supabase = None

def init_supabase():
    global supabase

    if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
        print("Supabase is not configured yet.")
        return None

    try:
        from supabase import create_client

        supabase = create_client(
            Config.SUPABASE_URL,
            Config.SUPABASE_KEY
        )

        print("Supabase connection initialized.")
        return supabase

    except Exception as error:
        print("Supabase initialization failed:", error)
        return None


def get_supabase():
    return supabase
