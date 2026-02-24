from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
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