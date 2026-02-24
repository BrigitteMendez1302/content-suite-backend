import time
from app.db.supabase_client import get_supabase

def upload_audit_image(user_id: str, content_item_id: str, filename: str, content_type: str, data: bytes) -> dict:
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

    # signed URL (private bucket). For MVP: generate a signed URL valid for 1 hour
    signed = sb.storage.from_("audit-images").create_signed_url(path, 3600)
    signed_url = signed.get("signedURL") or signed.get("signedUrl") or None

    return {"path": path, "signed_url": signed_url}