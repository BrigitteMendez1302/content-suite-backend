from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.health import router as health_router
from app.routes.brands import router as brands_router
from app.routes.content import router as content_router
from app.routes.governance import router as governance_router

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