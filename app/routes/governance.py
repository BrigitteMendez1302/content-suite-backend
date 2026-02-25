import time
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.core.auth import get_current_profile, require_roles
from app.db.supabase_client import get_supabase
from app.core.langfuse_client import langfuse
from app.services.embeddings import embed_texts
from app.services.storage import upload_audit_image
from app.services.multimodal_audit import audit_image_with_gemini
from app.services.rerank import rerank_chunks  # re-use

router = APIRouter(tags=["governance"])

class DecisionBody(BaseModel):
    comment: str | None = None

@router.get("/inbox")
async def inbox(profile=Depends(get_current_profile)):
    sb = get_supabase()
    role = profile["role"]

    if role == "creator":
        res = (
            sb.table("content_items")
            .select("id, brand_id, type, status, input_brief, output_text, created_at, brand_manual_id")
            .eq("created_by", profile["id"])
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        return {"items": res.data or []}


    # approvers see PENDING
    res = (
        sb.table("content_items")
        .select("id, brand_id, type, status, input_brief, output_text, created_at, brand_manual_id")
        .eq("status", "PENDING")
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return {"items": res.data or []}

@router.post("/content/{content_id}/approve")
async def approve(content_id: str, body: DecisionBody, profile=Depends(require_roles("approver_a","approver_b"))):
    sb = get_supabase()
    trace = langfuse.trace(name="module3.governance.approve", input={"content_id": content_id, "role": profile["role"], "comment": body.comment})
    t0 = time.time()

    # Update content item
    upd = sb.table("content_items").update({"status": "APPROVED"}).eq("id", content_id).execute()
    if not upd.data:
        trace.update(output={"error": "not_found"})
        raise HTTPException(status_code=404, detail="Content not found")

    # Insert approval history
    sb.table("approvals").insert({
        "content_item_id": content_id,
        "role": profile["role"],
        "decision": "APPROVED",
        "comment": body.comment,
        "created_by": profile["id"],
    }).execute()

    trace.update(output={"status": "APPROVED", "latency_ms": int((time.time()-t0)*1000)})
    return {"status": "APPROVED", "content_id": content_id}

@router.post("/content/{content_id}/reject")
async def reject(content_id: str, body: DecisionBody, profile=Depends(require_roles("approver_a","approver_b"))):
    sb = get_supabase()
    trace = langfuse.trace(name="module3.governance.reject", input={"content_id": content_id, "role": profile["role"], "comment": body.comment})
    t0 = time.time()

    upd = sb.table("content_items").update({"status": "REJECTED"}).eq("id", content_id).execute()
    if not upd.data:
        trace.update(output={"error": "not_found"})
        raise HTTPException(status_code=404, detail="Content not found")

    sb.table("approvals").insert({
        "content_item_id": content_id,
        "role": profile["role"],
        "decision": "REJECTED",
        "comment": body.comment,
        "created_by": profile["id"],
    }).execute()

    trace.update(output={"status": "REJECTED", "latency_ms": int((time.time()-t0)*1000)})
    return {"status": "REJECTED", "content_id": content_id}

@router.post("/content/{content_id}/audit-image")
async def audit_image(
    content_id: str,
    file: UploadFile = File(...),
    profile=Depends(require_roles("approver_b")),
):
    sb = get_supabase()
    trace = langfuse.trace(name="module3.audit.multimodal", input={"content_id": content_id, "filename": file.filename, "role": profile["role"]})
    t0 = time.time()

    # Validate content item exists and get manual_id + brand_id
    cres = (
        sb.table("content_items")
        .select("id, brand_id, brand_manual_id, type, input_brief")
        .eq("id", content_id)
        .limit(1)
        .execute()
    )
    if not cres.data:
        trace.update(output={"error": "not_found"})
        raise HTTPException(status_code=404, detail="Content not found")
    item = cres.data[0]
    manual_id = item["brand_manual_id"]

    # Read bytes
    img_bytes = await file.read()
    mime = file.content_type or "image/jpeg"

    # Upload to storage
    up = upload_audit_image(profile["id"], content_id, file.filename or "image.jpg", mime, img_bytes)

    # RAG retrieve brand rules for audit
    # Query tuned to visual governance:
    rag_query = "logo rules size clear space colors typography image style visual guidelines approval checklist"
    qvec = (await embed_texts([rag_query]))[0]

    rpc = sb.rpc("match_brand_manual_chunks_openai", {
        "p_brand_manual_id": manual_id,
        "p_query_embedding": qvec,
        "p_match_count": 10
    }).execute()
    rag_chunks = rpc.data or []
    reranked = rerank_chunks(rag_chunks, content_type="image_prompt", keep_k=6)

    # Build text rules context
    rules_text = "\n\n".join([f"[{c.get('section')}] {c.get('chunk_text')}" for c in reranked])

    # Log evidence in Langfuse
    trace.update(output={
        "rag_rules": [{"section": c.get("section"), "similarity": c.get("similarity"), "snippet": (c.get("chunk_text") or "")[:240]} for c in reranked],
        "image_path": up["path"],
    })

    # Call Gemini multimodal
    audit = audit_image_with_gemini(img_bytes, mime, rules_text)

    verdict = audit.get("verdict", "FAIL")
    report_json = {
        "verdict": verdict,
        "violations": audit.get("violations", []),
        "notes": audit.get("notes", []),
        "raw": audit.get("_raw", ""),
    }

    # Persist audit report
    sb.table("audit_images").insert({
        "content_item_id": content_id,
        "image_path": up["path"],
        "image_public_url": up.get("signed_url"),
        "verdict": verdict,
        "report_json": report_json,
        "created_by": profile["id"],
    }).execute()

    trace.update(output={
        "verdict": verdict,
        "audit_latency_ms": audit.get("_latency_ms"),
        "latency_ms": int((time.time()-t0)*1000),
    })

    return {
        "content_id": content_id,
        "image_path": up["path"],
        "image_url": up.get("signed_url"),
        "verdict": verdict,
        "report": report_json,
    }