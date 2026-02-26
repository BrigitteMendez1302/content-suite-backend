import time
from typing import Any, Dict

from fastapi import HTTPException

from app.core.langfuse_client import langfuse
from app.repositories import brand_audit as audit_repo
from app.services.embeddings import embed_texts
from app.services.rerank import rerank_chunks
from app.services.storage import upload_audit_image
from app.services.multimodal_audit import audit_image_with_gemini


async def audit_brand_image(
    brand_id: str,
    img_bytes: bytes,
    filename: str,
    mime: str,
    profile: Dict[str, Any],
) -> Dict[str, Any]:
    """Perform the full multimodal audit flow for a brand image.

    This is the business‑logic layer that the route should call. It assumes the
    caller has already taken care of HTTP details such as extracting the file
    and validating permissions.
    """

    trace = langfuse.trace(
        name="module3.audit.multimodal.by_brand",
        input={"brand_id": brand_id, "filename": filename, "role": profile["role"]},
    )
    t0 = time.time()

    # 1) fetch most recent manual
    manual_id = audit_repo.get_latest_manual_id(brand_id)
    if not manual_id:
        trace.update(output={"error": "no_manual"})
        raise HTTPException(
            status_code=409,
            detail="Esta marca no tiene manual. Crea Brand DNA primero.",
        )

    # 2) upload image to storage
    up = upload_audit_image(
        profile["id"], f"brand_{brand_id}", filename or "image.jpg", mime, img_bytes
    )

    # 3) retrieve relevant chunks via RAG
    rag_query = "visual guidelines logo rules colors typography image style"
    qvec = (await embed_texts([rag_query]))[0]
    rag_chunks = audit_repo.match_manual_chunks(manual_id, qvec, match_count=12)
    reranked = rerank_chunks(rag_chunks, content_type="image_prompt", keep_k=6)
    rules_text = "\n\n".join(
        [f"[{c.get('section')}] {c.get('chunk_text')}" for c in reranked]
    )

    try:
        trace.update(
            output={
                "brand_manual_id": manual_id,
                "rag_rules": [
                    {
                        "section": c.get("section"),
                        "similarity": c.get("similarity"),
                        "snippet": (c.get("chunk_text") or "")[:240],
                    }
                    for c in reranked
                ],
                "image_path": up["path"],
            }
        )
    except Exception:
        # best effort tracing; ignore failures so they don't ruin the flow
        pass

    # 4) call external audit model
    audit = audit_image_with_gemini(img_bytes, mime, rules_text)

    violations = audit.get("violations") or []
    try:
        validated_count = int(audit.get("validated_rules_count") or 0)
    except Exception:
        validated_count = 0

    verdict = "CHECK"
    if len(violations) > 0:
        verdict = "FAIL"
    elif validated_count < 2:
        verdict = "FAIL"

    report_json: Dict[str, Any] = {
        "verdict": verdict,
        "validated_rules_count": validated_count,
        "validated_rules": audit.get("validated_rules", []) or [],
        "violations": violations,
        "notes": audit.get("notes", []) or [],
        "raw": audit.get("_raw", ""),
    }

    # 5) persist audit report
    audit_repo.insert_audit_report(
        brand_id=brand_id,
        manual_id=manual_id,
        image_path=up["path"],
        image_url=up.get("signed_url"),
        verdict=verdict,
        report_json=report_json,
        created_by=profile["id"],
    )

    trace.update(
        output={
            "verdict": verdict,
            "audit_latency_ms": audit.get("_latency_ms"),
            "latency_ms": int((time.time() - t0) * 1000),
        }
    )

    return {
        "brand_id": brand_id,
        "brand_manual_id": manual_id,
        "image_path": up["path"],
        "image_url": up.get("signed_url"),
        "verdict": verdict,
        "report": report_json,
    }
