"""Cloud storage service using Supabase Storage."""
import time
from app.db.supabase_client import get_supabase


def upload_audit_image(
    user_id: str,
    content_item_id: str,
    filename: str,
    content_type: str,
    data: bytes,
) -> dict:
    """Upload an image file to Supabase Storage and generate a signed URL.

    Stores the image in the 'audit-images' bucket under a path that includes
    the content item id, user id, and timestamp for organization and traceability.

    Args:
        user_id: ID of the user performing the upload (for path organization).
        content_item_id: ID of the content item being audited/attached to.
        filename: Original filename (spaces will be replaced with underscores).
        content_type: MIME type of the file (e.g., 'image/jpeg', 'image/png').
        data: Raw bytes of the image file.

    Returns:
        dict: Contains two keys:
            - 'path': Storage path where file is stored
              (format: '{content_item_id}/{user_id}/{timestamp}_{filename}')
            - 'signed_url': Temporary signed URL valid for 1 hour that allows
                           downloading the private file without authentication.

    Raises:
        Exception: On Supabase API failures (authentication, network, storage
                  quota exceeded, etc.).

    Example:
        >>> result = upload_audit_image(
        ...     user_id="user123",
        ...     content_item_id="content456",
        ...     filename="brand_logo.jpg",
        ...     content_type="image/jpeg",
        ...     data=image_bytes
        ... )
        >>> print(result['signed_url'])  # Valid for 1 hour
    """
    sb = get_supabase()
    ts = int(time.time())
    safe_name = filename.replace(" ", "_")
    path = f"{content_item_id}/{user_id}/{ts}_{safe_name}"

    # Upload to Supabase Storage bucket
    sb.storage.from_("audit-images").upload(
        path,
        data,
        {"content-type": content_type, "upsert": "true"},
    )

    # Generate signed URL (private bucket). Valid for 1 hour (3600 seconds)
    signed = sb.storage.from_("audit-images").create_signed_url(path, 3600)
    signed_url = signed.get("signedURL") or signed.get("signedUrl") or None

    return {"path": path, "signed_url": signed_url}
