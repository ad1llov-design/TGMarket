from supabase import create_client, Client
from config import config

# Create the Supabase client
supabase: Client = create_client(config.supabase_url, config.supabase_key)
