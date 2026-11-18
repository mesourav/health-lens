# Insurance Chat — Backend

FastAPI service behind the chat UI. Serves `POST /api/chat` (contract in `app/schemas/chat.py`,
mirrors `frontend/src/features/chat/types.ts`).

## Getting started

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

Then in `frontend/.env.local` set `VITE_CHAT_API_URL=/api` and run `npm run dev` — Vite proxies
`/api` to port 8000.

| Command          | What it does |
| ---------------- | ------------ |
| `pytest`         | Tests        |
| `ruff check .`   | Lint         |
| `ruff format .`  | Format       |

## Structure

```
app/
├── main.py              # FastAPI app factory, CORS, mounts /api
├── core/config.py       # Settings from env / .env
├── api/
│   ├── router.py        # Aggregates route modules
│   └── routes/          # chat.py (POST /chat), health.py (GET /health)
├── schemas/chat.py      # Pydantic request/response models (camelCase on the wire)
├── services/            # Business logic (chat_service.respond)
└── rag/                 # Retrieval + LLM code goes here
tests/                   # pytest
```
