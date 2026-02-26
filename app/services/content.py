from typing import Any, Dict, List
import time

from app.core.langfuse_client import langfuse
from app.services.embeddings import embed_texts
from app.services.rerank import rerank_chunks
from app.services.groq_llm import groq_chat
from app.repositories import brand_manual as manual_repo
from app.repositories import brand_audit as audit_repo
from app.repositories import content as content_repo
from fastapi import HTTPException


class GenerateRequest:
    # keep the Pydantic model in routes; this is just a typing stub
    pass


def build_generation_prompt(content_type: str, brief: str, rag_chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Construct the system+user messages for the generation task.

    ``rag_chunks`` should already be reranked and filtered by relevance.  This
    helper mirrors the logic that used to live in ``routes/content.py``.
    """

    context = "\n\n".join([f"[{c['section']}] {c['chunk_text']}" for c in rag_chunks])

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

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


async def generate_content(req: Any) -> Dict[str, Any]:
    """Execute the full content generation workflow.

    ``req`` is expected to behave like ``GenerateRequest`` from the router (it
    has attributes ``brand_id``, ``type`` and ``brief`` and a ``model_dump``
    method). This function:
    1. Fetches latest manual or raises 409
    2. Embeds the brief and retrieves RAG chunks (RPC)
    3. Ensures a minimum number of chunks, reranks them
    4. Builds a prompt, logs tracing information
    5. Calls the LLM
    6. Persists the content item via repository

    Raises ``HTTPException`` for any error that should result in an HTTP error
    code; unexpected exceptions bubble up as 500s.
    """

    # create trace
    trace = langfuse.trace(name="module2.creative_engine.generate", input=req.model_dump())
    t0 = time.time()

    trace_output: Dict[str, Any] = {}

    def safe_update(payload: Dict[str, Any]) -> None:
        trace_output.update(payload)
        try:
            trace.update(output=trace_output)
        except Exception:
            pass

    # 1) latest manual
    manual_record = manual_repo.get_latest_manual(req.brand_id)
    if not manual_record:
        safe_update({"error": "no_manual"})
        raise HTTPException(status_code=409, detail="No existe manual. Crea Brand DNA primero.")
    manual_id = manual_record["id"]

    # 2) embedding query
    emb_span = trace.span(name="embeddings.query")
    qvec = (await embed_texts([req.brief]))[0]
    try:
        emb_span.end(output={"dim": len(qvec)})
    except Exception:
        pass

    # 3) RAG retrieve via RPC
    rag_span = trace.span(name="rag.retrieve", input={"top_k": 6})
    rag_chunks = audit_repo.match_manual_chunks(manual_id, qvec, match_count=6)
    try:
        rag_span.end(output={"chunks": len(rag_chunks)})
    except Exception:
        pass

    if len(rag_chunks) < 3:
        safe_update({"error": "rag_insufficient", "chunks": len(rag_chunks)})
        raise HTTPException(status_code=422, detail="RAG insuficiente: no se recuperó contexto suficiente del manual.")

    reranked_chunks = rerank_chunks(rag_chunks, req.type, keep_k=6)

    # 4) Build prompt and update trace
    prompt_msgs = build_generation_prompt(req.type, req.brief, reranked_chunks)

    safe_update({
        "reranked_chunks": [
            {
                "id": c.get("id"),
                "section": c.get("section"),
                "similarity": c.get("similarity"),
                "snippet": (c.get("chunk_text") or "")[:240],
            }
            for c in reranked_chunks
        ],
        "final_prompt": {"system": prompt_msgs[0]["content"], "user": prompt_msgs[1]["content"]},
    })

    # 5) Generate with LLM
    gen_span = trace.span(
        name="groq.generate",
        input={
            "type": req.type,
            "final_prompt": {"system": prompt_msgs[0]["content"], "user": prompt_msgs[1]["content"]},
        },
    )
    output_text = await groq_chat(prompt_msgs, temperature=0.5)
    try:
        gen_span.end(output={"len": len(output_text)})
    except Exception:
        pass

    # 6) Persist content
    content_id = content_repo.insert_content_item(
        brand_id=req.brand_id,
        manual_id=manual_id,
        content_type=req.type,
        brief=req.brief,
        output_text=output_text,
        rag_chunks=reranked_chunks,
    )
    if not content_id:
        safe_update({"error": "db_insert_failed"})
        raise HTTPException(status_code=500, detail="Failed to save content item")

    latency_ms = int((time.time() - t0) * 1000)
    safe_update({"content_id": content_id, "chunks": len(reranked_chunks), "latency_ms": latency_ms})

    return {
        "content_id": content_id,
        "status": "PENDING",
        "brand_manual_id": manual_id,
        "reranked_chunks": reranked_chunks,
        "output_text": output_text,
        "latency_ms": latency_ms,
    }
