import time
from fastapi import APIRouter, HTTPException
from app.db.supabase_client import get_supabase
from app.models.brand import BrandCreateRequest, BrandCreateResponse
from app.models.manual import BrandManual
from app.services.brand_manual import generate_brand_manual
from app.utils.json_repair import extract_json
from app.services.chunking import chunk_manual
from app.services.embeddings import embed_texts
from app.core.langfuse_client import langfuse
from app.services.manual_normalize import normalize_manual_dict

router = APIRouter(prefix="/brands", tags=["brands"])

@router.post("", response_model=BrandCreateResponse)
def create_brand(req: BrandCreateRequest):
    sb = get_supabase()
    res = sb.table("brands").insert({"name": req.name}).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create brand")
    row = res.data[0]
    return BrandCreateResponse(id=row["id"], name=row["name"])

@router.post("/{brand_id}/manual")
async def create_manual(brand_id: str, body: dict):
    """
    body: { product, tone, audience, brand_name?, extra_constraints? }
    """
    trace = langfuse.trace(name="module1.brand_dna.create_manual", input=body)
    t0 = time.time()

    def safe_trace_update(payload: dict):
        try:
            trace.update(output=payload)
        except Exception:
            pass

    # 1) LLM generate manual JSON
    gen_span = trace.span(name="groq.generate_manual")
    try:
        raw = await generate_brand_manual(body)
        try:
            gen_span.end(output={"raw_len": len(raw)})
        except Exception:
            pass
    except Exception as e:
        try:
            gen_span.end(output={"error": str(e)})
        except Exception:
            pass
        safe_trace_update({"error": "groq_failed", "detail": str(e)})
        raise

    # 2) Parse + validate
    parse_span = trace.span(name="validate.manual_json")
    try:
        parsed = extract_json(raw)
        parsed = normalize_manual_dict(parsed)
        manual = BrandManual.model_validate(parsed).model_dump()
        parse_span.end(output={"validated": True})
    except Exception as e:
        parse_span.end(output={"validated": False, "error": str(e)})
        safe_trace_update({"error": "invalid_json", "detail": str(e)})
        raise HTTPException(status_code=422, detail=f"Invalid manual JSON: {e}")

    # 3) Persist manual
    sb = get_supabase()
    db_span = trace.span(name="db.insert_manual")
    res = sb.table("brand_manuals").insert({"brand_id": brand_id, "manual_json": manual}).execute()
    if not res.data:
        db_span.end(output={"inserted": False})
        safe_trace_update({"error": "db_insert_failed"})
        raise HTTPException(status_code=500, detail="Failed to save manual")
    manual_row = res.data[0]
    manual_id = manual_row["id"]
    db_span.end(output={"inserted": True, "manual_id": manual_id})

    # 4) Chunk + embed
    chunks = chunk_manual(manual)
    chunk_texts = [c["chunk_text"] for c in chunks]

    emb_span = trace.span(name="embeddings.embed_chunks", input={"n": len(chunk_texts)})
    vectors = await embed_texts(chunk_texts)
    emb_span.end(output={"n": len(vectors)})

    # 5) Persist chunks
    ins_span = trace.span(name="db.insert_chunks")
    payload = []
    for c, v in zip(chunks, vectors):
        payload.append({
            "brand_manual_id": manual_id,
            "section": c["section"],
            "chunk_text": c["chunk_text"],
            "embedding": v,
            "metadata": c["metadata"],
        })

    cres = sb.table("brand_manual_chunks_openai").insert(payload).execute()
    if not cres.data:
        ins_span.end(output={"inserted": False})
        safe_trace_update({"error": "chunk_insert_failed"})
        raise HTTPException(status_code=500, detail="Failed to save manual chunks")
    ins_span.end(output={"inserted": True, "chunks": len(cres.data)})

    latency_ms = int((time.time() - t0) * 1000)
    safe_trace_update({"manual_id": manual_id, "chunks": len(cres.data), "latency_ms": latency_ms})

    return {
        "brand_id": brand_id,
        "manual_id": manual_id,
        "manual_json": manual,
        "chunks_indexed": len(cres.data),
        "latency_ms": latency_ms,
    }

@router.get("/{brand_id}/manual")
def get_latest_manual(brand_id: str):
    sb = get_supabase()
    res = (
        sb.table("brand_manuals")
        .select("id, brand_id, manual_json, version, created_at")
        .eq("brand_id", brand_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="No manual found for brand")
    return res.data[0]