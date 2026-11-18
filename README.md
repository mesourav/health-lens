# Health Lens

Prototype health-insurance chat assistant. Customers get help with their policy, and
**policy data is never sent to any AI model**, not even our own. See
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

```
health-lens/
├── frontend/     # React chat UI
├── backend/      # FastAPI: login, redaction, intents, policy tools, RAG
├── llm/          # Dockerfile for our private model server (Ollama on Cloud Run)
├── docs/         # Architecture
└── Dockerfile    # App image: frontend + backend in one container
```

## Demo accounts (fake data)

| Policy number | Date of birth | Plan | What this account shows |
|---|---|---|---|
| `HL-100234` | `1988-04-12` | Silver PPO (Jordan) | Mid-year, deductible partly used, a claim in review |
| `HL-200871` | `1975-11-30` | Gold PPO (Priya) | Deductible met, autopay off |
| `HL-300415` | `1996-07-08` | Bronze PPO (Marcus) | New member, nothing used, no claims yet |
| `HL-400562` | `1962-02-19` | Gold PPO (Elena) | Out-of-pocket max reached, a denied claim |
| `HL-500128` | `2001-09-03` | Silver PPO (Sam) | Therapy and urgent care, a claim pending |

Try: *"How much deductible is left?"*, *"Is a knee MRI covered?"*, *"Show my claims"*,
*"Are prescriptions covered?"*, *"Is urgent care covered?"*,
*"What is prior approval?"* (general questions work before login).

## Run locally

```powershell
# 1. Our own model (optional: without it the app falls back to keyword matching)
ollama pull gemma3:4b
ollama pull nomic-embed-text

# 2. Backend on :8000
cd backend
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# 3. Frontend on :5173 (proxies /api → :8000), in a second terminal
cd frontend
npm install
"VITE_CHAT_API_URL=/api" | Out-File -Encoding utf8 .env.local
npm run dev
```

## Run with Docker (same containers as GCP)

Needs Docker Desktop. Test this before deploying: it builds the exact image Cloud Run runs.

```powershell
# App container only, using Ollama installed on your PC (fastest)
docker compose up --build

# App + the llm/ model container, exactly like GCP (first build downloads the model into the image)
"OLLAMA_URL=http://llm:8080" | Out-File -Encoding utf8 .env
docker compose --profile llm up --build
```

Open http://localhost:8080. The frontend and API are served by the same container, as on Cloud Run.

## Deploy to GCP (Cloud Run only)

Two Cloud Run services: **health-lens-llm** (private, GPU, our model) and **health-lens**
(public app). Run from the repo root with the [gcloud CLI](https://cloud.google.com/sdk/docs/install).

```powershell
$PROJECT = "your-gcp-project-id"
$REGION  = "us-central1"          # must be a region with Cloud Run L4 GPUs
gcloud config set project $PROJECT
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

# 1. Private model service. Nobody can call it without permission.
gcloud run deploy health-lens-llm --source llm --region $REGION `
  --no-allow-unauthenticated --gpu 1 --gpu-type nvidia-l4 --no-gpu-zonal-redundancy `
  --cpu 4 --memory 16Gi --no-cpu-throttling --max-instances 1 --concurrency 4 --timeout 600
$LLM_URL = gcloud run services describe health-lens-llm --region $REGION --format "value(status.url)"

# 2. Identity for the app, allowed to call ONLY the model service
gcloud iam service-accounts create health-lens-app
$SA = "health-lens-app@$PROJECT.iam.gserviceaccount.com"
gcloud run services add-iam-policy-binding health-lens-llm --region $REGION `
  --member "serviceAccount:$SA" --role roles/run.invoker

# 3. Public app (frontend + backend)
$SECRET = [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")
gcloud run deploy health-lens --source . --region $REGION --allow-unauthenticated `
  --service-account $SA --max-instances 2 `
  --set-env-vars "OLLAMA_URL=$LLM_URL,OLLAMA_USE_ID_TOKEN=true,SESSION_SECRET=$SECRET"
```

The last command prints the app URL. The first request after idle can take ~30-60 s while the
GPU service starts. The model service scales to zero, so you pay for the GPU only while it runs.

**No GPU quota?** Remove the `--gpu*` flags, use `--cpu 8 --memory 16Gi`, and build with a
smaller model: set `ARG CHAT_MODEL=gemma3:1b` in `llm/Dockerfile` and add
`CHAT_MODEL=gemma3:1b` to the app's env vars. It's slower but works.

## Tests

```powershell
cd backend; pytest        # no model needed
cd frontend; npm test
```
