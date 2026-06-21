from supabase import create_client, Client

supabase: Client = None

def init_supabase(app):
    global supabase
    url = app.config.get("SUPABASE_URL")
    # Use service role key to bypass RLS since Flask handles authorization securely
    key = app.config.get("SUPABASE_SERVICE_ROLE_KEY") or app.config.get("SUPABASE_KEY")
    if url and key:
        supabase = create_client(url, key)
    else:
        print("Warning: Supabase credentials not found. Supabase not initialized.")
