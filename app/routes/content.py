import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Literal
from app.db.supabase_client import get_supabase
from app.core.langfuse_client import langfuse
from app.services.embeddings import embed_texts
from app.services.groq_llm import groq_chat

router = APIRouter(prefix="/content", tags=["content"])

class GenerateRequest(BaseModel):
    brand_id: str
    type: Literal["product_description", "video_script", "image_prompt"]
    brief: str

def build_generation_prompt(content_type: str, brief: str, rag_chunks: list[dict]) -> list[dict]:
    # Compacta el contexto RAG
    context = "\n\n".join(
        [f"[{c['section']}] {c['chunk_text']}" for c in rag_chunks]
    )

    system = (
        "Eres un copywriter. Debes obedecer estrictamente el Brand Manual proporcionado. "
        "No uses términos ni claims prohibidos. No inventes hechos no presentes."
    )

    if content_type == "product_description":
        user = f"""Brand Manual (RAG):
{context}

Tarea: Escribe una descripción de producto basada en el brief.
Brief: {brief}

Requisitos:
- 80-150 palabras (o sigue length_guidelines si se indica).
- Tono según manual.
- Evita tecnicismos si el manual lo prohíbe.
- No usar forbidden_terms ni forbidden_claims.
Devuelve solo el texto final."""
    elif content_type == "video_script":
        user = f"""Brand Manual (RAG):
{context}

Tarea: Escribe un guion de video corto (15s) basado en el brief.
Brief: {brief}

Formato:
- Hook (0-3s)
- Cuerpo (3-12s)
- Cierre + CTA (12-15s)
Evita forbidden_terms/claims. Devuelve solo el guion."""
    else:
        user = f"""Brand Manual (RAG):
{context}

Tarea: Genera un prompt de imagen basado en el brief.
Brief: {brief}

Formato de salida:
- Prompt principal (1 párrafo)
- Negative prompt (lista corta)
- Notas de cumplimiento (1-3 bullets)
Evita elementos/claims prohibidos. Devuelve solo eso."""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

@router.post("/generate")
async def generate(req: GenerateRequest):
    sb = get_supabase()
    trace = langfuse.trace(name="module2.creative_engine.generate", input=req.model_dump())
    t0 = time.time()

    def safe_update(payload: dict):
        try:
            trace.update(output=payload)
        except Exception:
            pass

    # 1) latest manual
    mres = (
        sb.table("brand_manuals")
        .select("id, manual_json, created_at")
        .eq("brand_id", req.brand_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not mres.data:
        safe_update({"error": "no_manual"})
        raise HTTPException(status_code=409, detail="No existe manual. Crea Brand DNA primero.")
    manual_id = mres.data[0]["id"]

    # 2) embedding query
    emb_span = trace.span(name="embeddings.query")
    qvec = (await embed_texts([req.brief]))[0]
    try:
        emb_span.end(output={"dim": len(qvec)})
    except Exception:
        pass

    # 3) RAG retrieve via RPC
    rag_span = trace.span(name="rag.retrieve", input={"top_k": 6})
    rpc = sb.rpc("match_brand_manual_chunks_openai", {
        "p_brand_manual_id": manual_id,
        "p_query_embedding": qvec,
        "p_match_count": 6
    }).execute()

    rag_chunks = rpc.data or []
    try:
        rag_span.end(output={"chunks": len(rag_chunks)})
    except Exception:
        pass

    # Enforce: must retrieve context before generate
    if len(rag_chunks) < 3:
        safe_update({"error": "rag_insufficient", "chunks": len(rag_chunks)})
        raise HTTPException(status_code=422, detail="RAG insuficiente: no se recuperó contexto suficiente del manual.")

    # 4) Build prompt (final) and log it BEFORE generation
    prompt_msgs = build_generation_prompt(req.type, req.brief, rag_chunks)

    safe_update({
        "rag_chunks": [
            {
                "id": c.get("id"),
                "section": c.get("section"),
                "similarity": c.get("similarity"),
                "snippet": (c.get("chunk_text") or "")[:240],
            }
            for c in rag_chunks
        ],
        # guarda ambos mensajes (system+user). Si prefieres, guarda solo prompt_msgs[1]["content"]
        "final_prompt": prompt_msgs,
    })

    # 5) Generate with Groq (using the SAME prompt)
    gen_span = trace.span(name="groq.generate", input={"type": req.type})
    output_text = await groq_chat(prompt_msgs, temperature=0.5)
    try:
        gen_span.end(output={"len": len(output_text)})
    except Exception:
        pass

    # 6) Persist content item
    ins = sb.table("content_items").insert({
        "brand_id": req.brand_id,
        "brand_manual_id": manual_id,
        "type": req.type,
        "input_brief": req.brief,
        "output_text": output_text,
        "status": "PENDING",
        "rag_chunks": rag_chunks
    }).execute()

    if not ins.data:
        safe_update({"error": "db_insert_failed"})
        raise HTTPException(status_code=500, detail="Failed to save content item")

    content_id = ins.data[0]["id"]
    latency_ms = int((time.time() - t0) * 1000)
    safe_update({"content_id": content_id, "chunks": len(rag_chunks), "latency_ms": latency_ms})

    return {
        "content_id": content_id,
        "status": "PENDING",
        "brand_manual_id": manual_id,
        "rag_chunks": rag_chunks,
        "output_text": output_text,
        "latency_ms": latency_ms,
    }