# Health Lens — Backend

FastAPI service behind the chat UI. Serves `POST /api/chat` (contract in `app/schemas/chat.py`,
mirrors `frontend/src/features/chat/types.ts`). See the root README to run and deploy.

## How a message is handled

```
text ──► login check ──► redact ──► classify (our model) ──┬─► personal → tools (policy data, templates)
                                                           ├─► general  → RAG (plan docs + our model)
                                                           └─► handoff  → human agent flow
```

The model only ever receives **redacted customer text** or **general plan documents**.
Policy values are added by `app/intents/tools.py` after the model is done.

## Structure

```
app/
├── main.py                  # App, session cookie, /api, serves frontend in Docker
├── core/config.py           # Settings (env vars / .env)
├── api/routes/              # chat.py (POST /chat), health.py (GET /health)
├── schemas/chat.py          # Request/response models (camelCase on the wire)
├── services/chat_service.py # The conversation engine
├── privacy/redact.py        # Removes personal details before the model sees text
├── llm/ollama.py            # Client for OUR model server (no third-party AI)
├── intents/
│   ├── classifier.py        # Model → intent (keyword fallback if model is down)
│   ├── tools.py             # Personal answers from policy data (no AI)
│   └── replies.py           # Quick-reply chips
├── policy/repository.py     # ONLY code that reads policy data
└── rag/
    ├── index.py             # Load docs → chunks → embeddings → search
    └── answer.py            # Answer general questions from retrieved chunks
data/
├── policies.json            # FAKE customers
├── plans.json               # FAKE plan coverage tables
└── docs/*.md                # General plan documents (indexed for RAG)
tests/                       # pytest (run without a model)
```

Settings you may change in `backend/.env`: `OLLAMA_URL`, `CHAT_MODEL`, `EMBED_MODEL`,
`SESSION_SECRET`.
