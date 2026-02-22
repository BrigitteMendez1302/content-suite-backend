# Content Suite - Backend (Module I)

## Setup
1) Create Supabase project and run `app/db/schema.sql` in SQL editor.
2) Create `.env` in `backend/app`:

```env
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...

GROQ_API_KEY=...
GROQ_MODEL=llama-3.1-70b-versatile

LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
LANGFUSE_HOST=https://cloud.langfuse.com

EMBEDDINGS_PROVIDER=local
LOCAL_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIM=384