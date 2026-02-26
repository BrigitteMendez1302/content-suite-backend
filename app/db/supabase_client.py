"""Supabase database client initialization."""
from supabase import create_client, Client
from app.core.config import settings


def get_supabase() -> Client:
    """Initialize and return a Supabase client with service role permissions.

    Uses service role key for admin operations (bypass RLS policies).
    Can perform unrestricted table operations, auth management, and storage access.

    Returns:
        Client: Authenticated Supabase client connected to configured database.

    Raises:
        Exception: If SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY settings are
                  missing or invalid.

    Note:
        Service role key grants full admin access. Use with care in production.
        Consider using user-scoped access tokens for client-side operations.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)