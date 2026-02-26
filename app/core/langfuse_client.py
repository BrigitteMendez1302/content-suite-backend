"""Langfuse instrumentation client for LLM observability and tracing.

Langfuse is integrated for monitoring generation pipelines, tracking token usage,
and debugging LLM outputs in production.
"""
from langfuse import Langfuse
from app.core.config import settings


langfuse = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_HOST,
)