# Health Lens — Architecture

## 0. Prototype vs. later

**Right now we are building a showcase prototype**, using as few GCP services as possible.
The privacy idea (sections 1–3) is fully in place. The heavier infrastructure (sections 4–9)
is the later production target.

| Piece | Prototype (now) | Later (production) |
|---|---|---|
| Hosting | **Cloud Run only**: 2 services (app + private model) | + Load Balancer, Cloud Armor, VPC |
| Policy data | Fake JSON file (`backend/data/policies.json`) | Cloud SQL (PostgreSQL) |
| Plan documents (RAG) | Markdown files, vectors in memory | pgvector in Cloud SQL |
| Login sessions | Signed cookie | Redis (Memorystore) |
| Secrets | Env var | Secret Manager |
| Redaction | Regex rules | Microsoft Presidio |
| AI model | Gemma 3 4B on Ollama (Cloud Run GPU) | Same idea, possibly vLLM |
| If model is down | Falls back to keyword matching | Same |

### What is RAG and where do we use it?
**RAG (Retrieval-Augmented Generation)** = before the AI answers, we *search our own documents*
and give it only the relevant passages, so it answers from **our** rules, not from memory.

- We use it **only for general questions** ("What is prior approval?").
- Documents: `backend/data/docs/*.md` (plan guides, same for every customer).
- Steps: split docs into sections → turn each into a vector (embedding model) → find the
  closest sections to the question → AI writes a short answer from them → we show the source.
- **Personal questions never use RAG.** Customer data is not indexed or sent to the AI.

## 1. Goal

Customers can ask anything about their health-insurance policy in a chat and get correct,
personal answers.

**Rule #1: customer policy data is never shared with any outside AI company.**
No OpenAI, no Anthropic, no Google Gemini. Everything runs inside our own GCP project.

**Rule #2: even our own AI model never sees customer policy data.**
The AI only *understands the question*. Our normal backend code *looks up the answer*
in our database. The AI cannot leak or invent data it never received.

---

## 2. The big idea in one example

Customer types: **"How much of my deductible is left?"**

| Step | Who does it | What happens | Sees policy data? |
|---|---|---|---|
| 1 | Backend | Checks the customer is logged in (session cookie). Knows their policy ID. | Yes (ID only) |
| 2 | Backend | Removes personal details from the text (names, numbers, phone). | — |
| 3 | **AI model** | Reads *"How much of my deductible is left?"* and returns `intent = deductible_status`. | **No** |
| 4 | Backend | Runs `deductible_status(policy_id)` → database says used ₹12,000 of ₹25,000. | Yes |
| 5 | Backend | Fills the answer: *"You've used ₹12,000 of your ₹25,000 deductible. ₹13,000 is left."* | Yes |
| 6 | Frontend | Shows the answer. | — |

The AI only did step 3. It never saw the numbers.

### Placeholder trick (for natural-sounding answers)

If fixed templates feel robotic, the AI may write the sentence, but with **blanks**:

```
AI writes:      "Good news! You have {DEDUCTIBLE_LEFT} left on your deductible this year."
Backend fills:  {DEDUCTIBLE_LEFT} → ₹13,000      (after the AI is finished)
```

---

## 3. Three kinds of questions

| Kind | Example | How we answer |
|---|---|---|
| **General** (same for everyone) | "What is prior approval?" | **RAG**: search our plan documents, AI writes the answer from them. Plan docs are not customer data. |
| **Personal** (about *my* policy) | "Is my MRI claim approved?" | **Tool**: AI picks the intent, backend reads the database, fills the answer. |
| **Sensitive / unclear** | Complaints, disputes, angry customer | **Human agent** handoff (frontend already supports `mode: "agent"`). |

---

## 4. Components

### 4.1 Frontend — `frontend/`
- React chat UI (already built).
- Stores **no** policy data and **no** tokens. Login is a secure httpOnly cookie set by the backend.
- Talks only to `POST /api/chat`.

### 4.2 Backend — `backend/` (Python, FastAPI)
The brain of the system. The **only** component that touches policy data.

| Module | Job |
|---|---|
| `app/auth/` | Login with policy number + date of birth → creates a session. Locks after too many wrong tries. |
| `app/privacy/` | Removes personal details from customer text before the AI sees it (Microsoft Presidio, runs locally). |
| `app/llm/` | Small client that calls our private AI model. |
| `app/intents/` | The list of things a customer can ask (intents) and the tool for each one. |
| `app/policy/` | The **only** code that reads the policy database. Every query is limited to the logged-in customer's policy. |
| `app/rag/` | Plan documents → search index → relevant passages for general questions. |
| `app/services/chat_service.py` | Connects everything: redact → understand → tool or RAG → answer. |

### 4.3 AI model service — `llm/`
- Open-source model (**Gemma** or **Llama**, ~7–14B) running with **vLLM** or **Ollama**.
- Also runs the **embedding model** (for RAG search), so plan documents don't leave either.
- Has **no internet access** and **no database access**. Only the backend can call it.

### 4.4 Database
- **PostgreSQL** with:
  - policy tables (policies, members, coverage, claims, deductibles)
  - **pgvector** extension for RAG search over plan documents

### 4.5 Sessions
- **Redis** stores who is logged in. Cookie holds only a random session ID.

---

## 5. Where it runs on GCP

```
Customer browser
   │ HTTPS
   ▼
Load Balancer + Cloud Armor         ← firewall, rate limit, bot protection
   ├── /        → Cloud Storage + CDN        (frontend files)
   └── /api/*   → Cloud Run: backend         (FastAPI)
                    │   private network (VPC) — nothing below has a public IP
                    ├─► Cloud Run (GPU, internal only): AI model service
                    ├─► Cloud SQL (PostgreSQL + pgvector)
                    ├─► Memorystore (Redis)
                    └─► Secret Manager (passwords, keys)
```

| Need | GCP service | Why |
|---|---|---|
| Run backend | Cloud Run | Containers, autoscaling, no servers to manage |
| Run AI model | Cloud Run with GPU (L4), **internal ingress** | Our own model, scales to zero when idle |
| Database | Cloud SQL for PostgreSQL, **private IP** | Managed Postgres, pgvector supported |
| Sessions | Memorystore for Redis | Fast session lookup |
| Secrets | Secret Manager | No passwords in code |
| Frontend hosting | Cloud Storage + Cloud CDN | Cheap, fast static hosting |
| Protection | Cloud Armor | Blocks attacks, limits login attempts |
| Data fence | VPC Service Controls | Data cannot be copied out of our project |
| Encryption | CMEK (our own keys) | We control the encryption keys |
| Logs | Cloud Logging + Audit Logs | Only redacted text is logged |
| Deploy | GitHub Actions → Artifact Registry → Cloud Run | Keyless login (Workload Identity Federation) |

**Why the same address for frontend and `/api`?** The browser sees one website, so the login
cookie works safely without CORS.

---

## 6. Security rules (must always be true)

1. Policy data lives **only** in Cloud SQL and is read **only** by `app/policy/`.
2. The AI model receives **only redacted text**, never database values.
3. Every database query is filtered by the **policy ID from the session**, never by a number
   typed in the chat.
4. No component except the load balancer has a public IP.
5. Each service has its own service account with the **minimum** permissions.
6. Logs contain **redacted** text only.
7. No API keys or passwords in code or in Git — Secret Manager only.

---

## 7. Local development (no GCP needed)

| On GCP | On your laptop |
|---|---|
| Cloud Run backend | `uvicorn app.main:app --reload` |
| Cloud Run AI model | **Ollama** (`ollama run gemma3`) |
| Cloud SQL | PostgreSQL + pgvector in Docker |
| Memorystore | Redis in Docker |
| Secret Manager | `backend/.env` |

Same code everywhere — only environment variables change.

---

## 8. Repository layout

```
health-lens/
├── frontend/             # React chat UI
├── backend/              # FastAPI — the only code that touches policy data
├── llm/                  # AI model service container (vLLM / Ollama + embeddings)
├── infra/                # Terraform for GCP
├── docs/                 # This document
├── docker-compose.yml    # Local Postgres + Redis (+ Ollama)
└── .github/workflows/    # CI/CD
```

---

## 9. Build plan

| Phase | What we build | Done when |
|---|---|---|
| **1. Local foundation** | docker-compose (Postgres, Redis, Ollama), DB tables + sample data | `docker compose up` works |
| **2. Login** | `app/auth`: policy no. + DOB → session cookie | Chat asks to verify, then remembers you |
| **3. First intent end-to-end** | `app/llm`, `app/privacy`, `app/intents`, `app/policy` for `deductible_status` | "How much deductible is left?" returns real DB numbers |
| **4. More intents** | coverage check, claim status, premium due, network hospitals… | Each has a tool + test |
| **5. General questions (RAG)** | Load plan PDFs → pgvector → answers with sources | "What is prior approval?" works |
| **6. Human handoff** | Escalation to agent | Sensitive topics go to a person |
| **7. GCP deploy** | Dockerfiles, Terraform, GitHub Actions | Live on GCP inside private network |
| **8. Hardening** | VPC-SC, CMEK, Cloud Armor rules, audit review | Security checklist (section 6) verified |
