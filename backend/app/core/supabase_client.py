from supabase import create_client, Client
from typing import Optional
from .config import settings

def get_supabase_client() -> Optional[Client]:
    """
    Initialize and return the Supabase client if keys are available.
    Returns None if SUPABASE_SERVICE_ROLE_KEY is not set.
    """
    if not settings.SUPABASE_SERVICE_ROLE_KEY:
        return None
    
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
