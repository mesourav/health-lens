# Insurance Chat

Health-insurance chat assistant — monorepo.

```
insurance-chat/
├── frontend/   # React 19 + TypeScript + Vite chat UI   → see frontend/README.md
└── backend/    # Python (FastAPI) API, POST /api/chat    → see backend/README.md
```

## Run both locally

```powershell
# Terminal 1 — backend on :8000
cd backend
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend on :5173 (proxies /api → :8000)
cd frontend
npm install
"VITE_CHAT_API_URL=/api" | Out-File -Encoding utf8 .env.local
npm run dev
```

Leave `VITE_CHAT_API_URL` empty to run the frontend on its built-in mock flows without the backend.

The request/response contract lives in two places that must stay in sync:
`frontend/src/features/chat/types.ts` and `backend/app/schemas/chat.py`.
