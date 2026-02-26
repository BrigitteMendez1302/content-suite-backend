"""Content Suite API - Module I: Brand Management and Content Generation.

FastAPI application for managing brand guidelines, generating on-brand content,
auditing content compliance, and managing approval workflows.

Features:
    - Brand manual generation with LLM (Groq)
    - Content generation with RAG (Semantic search + reranking)
    - Image audit with vision model (Google Gemini)
    - Approval workflow with role-based access control
    - Vector embeddings for semantic search (OpenAI)
    - Observability with Langfuse tracing

Routers:
    - health: Application health check
    - brands: Brand CRUD operations
    - content: Content generation and storage
    - governance: Approval workflows and decisions
    - brand_audit: Image compliance auditing
    - visual_rules: Visual guidelines CRUD
    - manuals: Brand manual retrieval
    - me: Current user profile
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.health import router as health_router
from app.routes.brands import router as brands_router
from app.routes.content import router as content_router
from app.routes.governance import router as governance_router
from app.routes.me import router as me_router
from app.routes.brand_audit import router as brand_audit_router
from app.routes.visual_rules import router as visual_rules_router
from app.routes.manual import router as manuals_router

app = FastAPI(title="Content Suite API (Module I)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(brands_router)
app.include_router(content_router)
app.include_router(governance_router)
app.include_router(me_router)
app.include_router(brand_audit_router)
app.include_router(visual_rules_router)
app.include_router(manuals_router)