import os
import threading

from dotenv import load_dotenv

load_dotenv()

_url = os.getenv("SUPABASE_URL", "")
_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "")

if _url and _key:
    from supabase import create_client, Client as _Client

    _local = threading.local()

    def get_supabase_client() -> _Client:
        client = getattr(_local, "client", None)
        if client is None:
            client = create_client(_url, _key)
            _local.client = client
        return client
else:
    from database.in_memory_store import get_in_memory_client

    def get_supabase_client():
        return get_in_memory_client()
