# Insurance Chat

Full-page health-insurance chat assistant: React 19 + TypeScript + Tailwind CSS v4, built with Vite.

Runs on scripted mock flows out of the box. Point it at your backend with one env var.

## Getting started

```bash
npm install
cp .env.example .env.local   # optional — leave VITE_CHAT_API_URL empty for mock mode
npm run dev                  # http://localhost:5173
```

| Script              | What it does                     |
| ------------------- | -------------------------------- |
| `npm run dev`       | Dev server with HMR              |
| `npm run build`     | Type-check, then production build to `dist/` |
| `npm run preview`   | Serve the production build       |
| `npm run typecheck` | TypeScript only                  |
| `npm run lint`      | ESLint                           |
| `npm test`          | Unit tests (Vitest)              |
| `npm run format`    | Prettier + Tailwind class sorting |

## Project structure

```
src/
├── main.tsx                  # Entry: mounts <App/> in StrictMode
├── App.tsx                   # Creates the chat service once, wraps in ErrorBoundary
├── index.css                 # Tailwind import + design tokens (@theme)
├── config/env.ts             # Typed env access — use this, not import.meta.env
├── lib/                      # Framework-free helpers (cn, id, sleep)
├── components/               # Shared, app-wide UI
│   ├── ErrorBoundary.tsx
│   ├── icons/SendIcon.tsx
│   └── ui/Button.tsx
└── features/
    └── chat/                 # Self-contained feature module
        ├── index.ts          # Public API — import from '@/features/chat' only
        ├── types.ts          # Message, ChatRequest/ChatTurn contract, ChatService
        ├── constants.ts      # Copy per mode, timings, limits
        ├── components/       # ChatWindow, ChatHeader, MessageList, MessageBubble,
        │                     # SystemNotice, TypingIndicator, QuickReplies, ChatComposer
        ├── hooks/
        │   ├── useChat.ts        # Conversation engine (reducer + cancellable playback)
        │   └── useAutoScroll.ts
        ├── state/chatReducer.ts  # Pure reducer (+ tests)
        └── services/
            ├── index.ts          # createChatService(): HTTP if env set, else mock
            ├── httpChatService.ts
            ├── parseChatTurn.ts  # Validates backend responses (+ tests)
            ├── errors.ts
            └── mock/             # Scripted flows + keyword router (+ tests)
```

New features go in `src/features/<name>/` with the same shape.

## Connecting the Python backend

The backend lives in [`../backend`](../backend). Set `VITE_CHAT_API_URL` (e.g. `/api`). In dev, `/api/*` is proxied to `http://localhost:8000`
(override with `API_PROXY_TARGET`), so the browser stays same-origin and session cookies work.

The client sends `POST {VITE_CHAT_API_URL}/chat` with `credentials: 'include'`:

```jsonc
// Request
{ "conversationId": "uuid", "mode": "bot", "text": "Is an MRI covered?" }   // typed message
{ "conversationId": "uuid", "mode": "bot", "intent": "deductible" }         // quick reply

// Response
{
  "steps": [
    { "sender": "bot", "text": "Good news: MRIs are covered…" },
    { "sender": "system", "text": "You're #2 in line" },
    { "sender": "agent", "text": "Hi, I'm Sam…", "author": "Sam · Member advocate" }
  ],
  "replies": [{ "label": "What is prior approval?", "intent": "prior" }],
  "mode": "agent",                                   // optional: switch to live agent
  "followUp": { "intent": "agentJoin", "delayMs": 4000 }  // optional: auto-run later
}
```

The conversation opens with `intent: "start"`. Responses are validated in `parseChatTurn`; `null`
optional fields are fine. Auth (policy number + DOB) should set an httpOnly session cookie on the
backend — the frontend never stores tokens or policy data.
