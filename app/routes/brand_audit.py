import time
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.core.auth import require_roles
from app.db.supabase_client import get_supabase
from app.core.langfuse_client import langfuse
from app.services.embeddings import embed_texts
from app.services.rerank import rerank_chunks
from app.services.storage import upload_audit_image
from app.services.multimodal_audit import audit_image_with_gemini

router = APIRouter(prefix="/brands", tags=["brand-audit"])

@router.post("/{brand_id}/audit-image")
async def audit_brand_image(
    brand_id: str,
    file: UploadFile = File(...),
    profile=Depends(require_roles("approver_b")),
):
    sb = get_supabase()
    trace = langfuse.trace(
        name="module3.audit.multimodal.by_brand",
        input={"brand_id": brand_id, "filename": file.filename, "role": profile["role"]},
    )
    t0 = time.time()

    # 1) Find latest manual for brand
    mres = (
        sb.table("brand_manuals")
        .select("id, created_at")
        .eq("brand_id", brand_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not mres.data:
        trace.update(output={"error": "no_manual"})
        raise HTTPException(status_code=409, detail="Esta marca no tiene manual. Crea Brand DNA primero.")
    manual_id = mres.data[0]["id"]

    # 2) Read bytes
    img_bytes = await file.read()
    mime = file.content_type or "image/jpeg"

    # 3) Upload to storage (reuse same bucket)
    up = upload_audit_image(profile["id"], f"brand_{brand_id}", file.filename or "image.jpg", mime, img_bytes)

    # 4) RAG retrieve visual rules
    rag_query = "visual guidelines logo rules colors typography image style"
    qvec = (await embed_texts([rag_query]))[0]

    rpc = sb.rpc("match_brand_manual_chunks_openai", {
        "p_brand_manual_id": manual_id,
        "p_query_embedding": qvec,
        "p_match_count": 12
    }).execute()
    rag_chunks = rpc.data or []
    reranked = rerank_chunks(rag_chunks, content_type="image_prompt", keep_k=6)

    rules_text = "\n\n".join([f"[{c.get('section')}] {c.get('chunk_text')}" for c in reranked])

    # log evidence
    try:
        trace.update(output={
            "brand_manual_id": manual_id,
            "rag_rules": [{"section": c.get("section"), "similarity": c.get("similarity"), "snippet": (c.get("chunk_text") or "")[:240]} for c in reranked],
            "image_path": up["path"],
        })
    except Exception:
        pass

    # 5) Multimodal audit
    audit = audit_image_with_gemini(img_bytes, mime, rules_text)

    violations = audit.get("violations") or []
    try:
        validated_count = int(audit.get("validated_rules_count") or 0)
    except Exception:
        validated_count = 0

    # ✅ Veredicto final determinístico
    verdict = "CHECK"
    if len(violations) > 0:
        verdict = "FAIL"
    elif validated_count < 2:
        verdict = "FAIL"

    report_json = {
        "verdict": verdict,
        "validated_rules_count": validated_count,
        "validated_rules": audit.get("validated_rules", []) or [],
        "violations": violations,
        "notes": audit.get("notes", []) or [],
        "raw": audit.get("_raw", ""),
    }

    # 6) Persist audit report
    sb.table("brand_audit_images").insert({
        "brand_id": brand_id,
        "brand_manual_id": manual_id,
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
        "brand_id": brand_id,
        "brand_manual_id": manual_id,
        "image_path": up["path"],
        "image_url": up.get("signed_url"),
        "verdict": verdict,
        "report": report_json,
    }