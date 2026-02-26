from typing import Any, Dict, Optional, List
import time

from fastapi import HTTPException
from app.core.langfuse_client import langfuse
from app.services.embeddings import embed_texts
from app.services.rerank import rerank_chunks
from app.services.storage import upload_audit_image
from app.services.multimodal_audit import audit_image_with_gemini
from app.repositories import governance as gov_repo


def inbox(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return inbox items for a user profile.

    Delegates directly to the repository which applies the role-based logic.
    """
    return gov_repo.fetch_content_for_inbox(profile)


def _record_decision(
    content_id: str,
    decision: str,
    comment: Optional[str],
    profile: Dict[str, Any],
) -> None:
    """Common implementation for approve/reject.

    Raises HTTPException if the content item does not exist.
    """
    trace = langfuse.trace(
        name=f"module3.governance.{decision.lower()}",
        input={"content_id": content_id, "role": profile.get("role"), "comment": comment},
    )
    t0 = time.time()

    if not gov_repo.update_content_status(content_id, decision.upper()):
        trace.update(output={"error": "not_found"})
        raise HTTPException(status_code=404, detail="Content not found")

    gov_repo.insert_approval(
        content_id=content_id,
        role=profile.get("role"),
        decision=decision.upper(),
        comment=comment,
        created_by=profile.get("id"),
    )

    trace.update(output={"status": decision.upper(), "latency_ms": int((time.time() - t0) * 1000)})


def approve(content_id: str, comment: Optional[str], profile: Dict[str, Any]) -> Dict[str, Any]:
    """Mark a content item as approved and log the approval."""
    _record_decision(content_id, "APPROVED", comment, profile)
    return {"status": "APPROVED", "content_id": content_id}


def reject(content_id: str, comment: Optional[str], profile: Dict[str, Any]) -> Dict[str, Any]:
    """Mark a content item as rejected and log the rejection."""
    _record_decision(content_id, "REJECTED", comment, profile)
    return {"status": "REJECTED", "content_id": content_id}


async def audit_image(
    content_id: str,
    img_bytes: bytes,
    filename: str,
    mime: str,
    profile: Dict[str, Any],
) -> Dict[str, Any]:
    """Perform a multimodal governance audit on a content item's image.

    Uses RAG against the brand manual associated with the content item and
    persists the resulting report. Raises HTTPException if the content item is
    not found or if other persistence steps fail.
    """
    trace = langfuse.trace(
        name="module3.audit.multimodal",
        input={"content_id": content_id, "filename": filename, "role": profile.get("role")},
    )
    t0 = time.time()

    item = gov_repo.get_content_item(content_id)
    if not item:
        trace.update(output={"error": "not_found"})
        raise HTTPException(status_code=404, detail="Content not found")

    manual_id = item.get("brand_manual_id")

    # upload
    up = upload_audit_image(profile.get("id"), content_id, filename or "image.jpg", mime, img_bytes)

    # RAG retrieve
    rag_query = "logo rules size clear space colors typography image style visual guidelines approval checklist"
    qvec = (await embed_texts([rag_query]))[0]
    rag_chunks = gov_repo.match_manual_chunks(manual_id, qvec, match_count=10) if hasattr(gov_repo, 'match_manual_chunks') else []
    # note: governance repo doesn't have matching, use audit_repo from brand_audit maybe

    # Actually we could call brand_audit.match_manual_chunks directly
    from app.repositories import brand_audit as audit_repo
    rag_chunks = audit_repo.match_manual_chunks(manual_id, qvec, match_count=10)

    reranked = rerank_chunks(rag_chunks, content_type="image_prompt", keep_k=6)
    rules_text = "\n\n".join([f"[{c.get('section')}] {c.get('chunk_text')}" for c in reranked])

    trace.update(output={
        "rag_rules": [
            {"section": c.get("section"), "similarity": c.get("similarity"),
             "snippet": (c.get("chunk_text") or "")[:240]}
            for c in reranked
        ],
        "image_path": up["path"],
    })

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

    report_json = {
        "verdict": verdict,
        "validated_rules_count": validated_count,
        "validated_rules": audit.get("validated_rules", []) or [],
        "violations": violations,
        "notes": audit.get("notes", []) or [],
        "raw": audit.get("_raw", ""),
    }

    gov_repo.insert_audit_report(
        content_id=content_id,
        image_path=up["path"],
        image_url=up.get("signed_url"),
        verdict=verdict,
        report_json=report_json,
        created_by=profile.get("id"),
    )

    trace.update(output={
        "verdict": verdict,
        "audit_latency_ms": audit.get("_latency_ms"),
        "latency_ms": int((time.time() - t0) * 1000),
    })

    return {
        "content_id": content_id,
        "image_path": up["path"],
        "image_url": up.get("signed_url"),
        "verdict": verdict,
        "report": report_json,
    }
