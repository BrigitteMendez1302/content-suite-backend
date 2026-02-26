"""Application configuration loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support.

    All settings are loaded from .env file with UTF-8 encoding.
    
    Attributes:
        SUPABASE_URL: PostgreSQL database URL via Supabase.
        SUPABASE_SERVICE_ROLE_KEY: Service role API key for admin operations.
        
        GROQ_API_KEY: API key for Groq LLM service.
        GROQ_MODEL: Model name (default: llama-3.1-70b-versatile).
        
        LANGFUSE_PUBLIC_KEY: Public key for Langfuse tracing.
        LANGFUSE_SECRET_KEY: Secret key for Langfuse tracing.
        LANGFUSE_HOST: Langfuse server URL (default:
                      https://cloud.langfuse.com).
        
        EMBEDDINGS_PROVIDER: Vector embedding provider (default: "openai").
        EMBEDDING_DIM: Dimension of embedding vectors (default: 1536 for
                      OpenAI's text-embedding-3-small).
        
        OPENAI_API_KEY: API key for OpenAI embeddings (optional).
        OPENAI_EMBED_MODEL: Model name (default: text-embedding-3-small).
        
        GEMINI_API_KEY: API key for Google Gemini vision model (optional).
        GEMINI_MODEL: Model name (default: gemini-1.5-flash).
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # Groq
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.1-70b-versatile"

    # Langfuse
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_SECRET_KEY: str
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # Embeddings
    EMBEDDINGS_PROVIDER: str = "openai"
    EMBEDDING_DIM: int = 1536

    OPENAI_API_KEY: str | None = None
    OPENAI_EMBED_MODEL: str = "text-embedding-3-small"

    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

settings = Settings()