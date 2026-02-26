# Content Suite — Backend (FastAPI)

Backend del MVP **Content Suite** para generación gobernada por Brand DNA (RAG), workflow de aprobación (RBAC) y auditoría multimodal, con observabilidad end-to-end en Langfuse.

## ✨ Features (MVP)
- **RAG obligatorio**: toda generación recupera contexto del **Brand DNA** desde **Supabase Postgres + pgvector**.
- **Generación**: descripciones / guiones / prompt de imagen vía **Groq**.
- **Embeddings**: generación de embeddings vía **OpenAI** *(solo embeddings; los vectores se guardan en Supabase)*.
- **Governance + RBAC**
  - Roles: **CREATOR**, **APPROVER_A**, **APPROVER_B**
  - Estados: **PENDING → APPROVED / REJECTED**
  - Restricción: el **CREATOR** solo ve/gestiona sus piezas; aprobadores revisan y deciden.
- **Auditoría multimodal** (**APPROVER_B**): sube imagen → compara contra reglas del manual → **PASS/CHECK o FAIL** con explicación accionable.
- **Observabilidad (Langfuse)**: trazas con contexto recuperado, prompt final, latencias y outputs.

## 🧱 Tech Stack
- **FastAPI** (Python)
- **Supabase** (Auth + Postgres + pgvector)
- **Groq** (LLM)
- **OpenAI** (Embeddings)
- **Google AI Studio** (Visión / multimodal)
- **Langfuse** (Tracing)

## 🚀 Deploy
- **Render** (producción)
- Variables de entorno configuradas en Render (ver sección **Environment Variables**)

## ✅ Requisitos
- Python 3.10+
- Proyecto en Supabase con:
  - Auth habilitado
  - Postgres con extensión **pgvector**
- API keys:
  - Groq
  - OpenAI (embeddings)
  - Google AI Studio
  - Langfuse

## ⚙️ Setup local

```bash
# 1) crear venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) instalar deps
pip install -r requirements.txt

# 3) levantar
uvicorn app.main:app --reload --port 8000
```

Backend: `http://localhost:8000`  
Swagger: `http://localhost:8000/docs`

## 🔐 Environment Variables

Crea un `.env` (local) o configura en Render:

### Supabase
- `SUPABASE_URL=`
- `SUPABASE_ANON_KEY=` *(si aplica)*
- `SUPABASE_SERVICE_ROLE_KEY=` *(recomendado para operaciones server-side)*
- `SUPABASE_JWT_SECRET=` *(opcional; solo si validas JWT localmente)*

### LLM / Embeddings / Visión
- `GROQ_API_KEY=`
- `OPENAI_API_KEY=`
- `OPENAI_EMBEDDING_MODEL=text-embedding-3-small` *(o el que uses)*
- `GOOGLE_AI_STUDIO_API_KEY=`

### Langfuse
- `LANGFUSE_PUBLIC_KEY=`
- `LANGFUSE_SECRET_KEY=`
- `LANGFUSE_HOST=https://us.cloud.langfuse.com`

### App
- `ENV=local|prod`
- `CORS_ORIGINS=http://localhost:5173,https://<tu-frontend-vercel>`

> ⚠️ No commitear `.env`.

## 🗄️ Data model (Supabase)
> Puede variar según implementación, pero el MVP normalmente incluye:

- `brand_manuals` (manual / Brand DNA)
- `brand_chunks` (chunks + embedding vector)
- `content_pieces` (piezas generadas + estado)
- `approvals` (decisiones + feedback)
- `audits` (resultado multimodal PASS/FAIL + explicación)
- `profiles` (user_id → role)

✅ **pgvector vive dentro de Supabase Postgres**. No hay otra “base de vectores”.

## 🔁 Flujos principales

### 1) Ingesta de Manual (Brand DNA)
1. Se carga manual (texto)
2. Backend lo estructura/chunkea
3. Genera embeddings (OpenAI)
4. Guarda chunks + embeddings en Supabase (pgvector)

### 2) Generación (RAG → prompt final → LLM)
1. Recibe request de generación (tipo + inputs)
2. Retrieval top-k desde Supabase pgvector
3. Construye **prompt final** con reglas del manual
4. Genera con Groq
5. Guarda pieza en estado **PENDING**
6. Registra traza en Langfuse (contexto + prompt + latencias + output)

### 3) Governance (Approve/Reject)
- Solo **APPROVER_A / APPROVER_B** pueden aprobar/rechazar
- **CREATOR** solo ve sus piezas

### 4) Auditoría multimodal (APPROVER_B)
1. Sube imagen
2. Visión evalúa contra reglas del manual + contexto
3. Respuesta: **PASS/CHECK** o **FAIL** + pasos para corregir
4. Todo queda trazado en Langfuse

## 🌐 Endpoints (resumen)
> Ajusta nombres/rutas a tu implementación real.

- `POST /generate` — generar (description/script/image_prompt) **(RAG obligatorio)**
- `GET /content` — listar piezas (filtrado por rol)
- `POST /content/{id}/approve` — aprobar (approvers)
- `POST /content/{id}/reject` — rechazar (approvers)
- `POST /content/{id}/audit-image` — auditoría multimodal (APPROVER_B)

## ✅ Checklist de QA (rápido)
- [ ] CREATOR crea pieza → queda **PENDING**
- [ ] APPROVER_A ve **PENDING** → **APPROVE/REJECT**
- [ ] APPROVER_B audita imagen → **PASS/FAIL + explicación**
- [ ] Langfuse muestra trace con: retrieval, prompt final, latencias, output

## 🛡️ Seguridad (MVP)
- Validación de JWT de Supabase en cada request
- RBAC server-side (no confiar en el front)
- CORS restringido a dominios permitidos

## 📎 Troubleshooting
- **401/403**: revisar token Supabase + rol en `profiles`
- **Retrieval vacío**: verificar embeddings guardados + pgvector habilitado
- **Sin trazas**: revisar `LANGFUSE_*` y conectividad desde Render
