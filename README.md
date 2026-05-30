# Video RAG Compare

Compare a YouTube video and an Instagram Reel side-by-side. RAG chatbot answers
questions about engagement, hooks, and content with citations and streaming.

## Stack
- **Backend:** FastAPI, LangChain, ChromaDB, BGE-small embeddings (local), Whisper (Instagram audio)
- **Frontend:** Next.js 14 (App Router), React 18, TypeScript, Tailwind
- **LLM (swappable):** Groq (default) / OpenAI / Anthropic — set `LLM_PROVIDER`

## Why this stack
- **BGE-small + ChromaDB:** zero embedding cost, runs on CPU, persists locally. At 1k creators/day this beats hosted vector DBs on cost.
- **Groq Llama 3.1 70B:** fastest free streaming, beats OpenAI on latency for the chat loop.
- **LangChain:** mandated; swap providers without touching chain code.
- **Whisper-base:** transcribes a 60s reel in ~30s on CPU. Worth the time savings vs paid API.

## Cost at scale (1,000 creators/day)
- Embeddings: $0 (local BGE)
- Vector DB: ~$20/mo (single VPS hosting Chroma)
- LLM: free tier (Groq) → ~$0.0006/1k tokens paid
- Whisper: $0 (CPU) — bottleneck at scale; swap to Modal GPU workers above ~5k/day
- **~$0.001–0.003 per creator session**

## What breaks at 10k users
- ChromaDB single-process: swap to Qdrant (horizontal)
- Stateless FastAPI: move memory to Redis
- Whisper CPU: move to GPU queue (Modal, Replicate)

## Setup

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in GROQ_API_KEY (free at console.groq.com)
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000.

## Tests
```bash
cd backend && pytest -v
```
