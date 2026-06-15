import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class SupabaseDB:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if url and key:
            self.client: Client = create_client(url, key)
        else:
            self.client = None

    def get_client(self) -> Client:
        return self.client
        
db = SupabaseDB()
