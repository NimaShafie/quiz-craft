# Architecture

## Deployment Modes

QuizCraft supports three deployment configurations. In all cases the app communicates with Ollama over HTTP using the `/api/generate` and `/api/tags` endpoints.

---

### Option A — Same Machine (default)

The simplest setup. Ollama and Streamlit run on the same host.

```
┌─────────────────────────────────┐
│           Your Machine          │
│                                 │
│  Browser → Streamlit :8501      │
│               │                 │
│               ▼                 │
│         Ollama :11434           │
│         (localhost)             │
└─────────────────────────────────┘
```

Config:
```ini
ollama_host = http://localhost:11434
```

---

### Option B — Docker Compose (local)

Ollama and Streamlit run in separate containers on the same host, networked via an internal Docker bridge (`quizcraft_net`). The Ollama port is not exposed to the host unless explicitly mapped.

```
┌────────────────────────────────────────────────┐
│                   Docker Host                  │
│                                                │
│  ┌──────────────────┐   ┌───────────────────┐  │
│  │  quizcraft_v1    │   │  quizcraft_ollama │  │
│  │  Streamlit :8501 │──▶│  Ollama :11434    │  │
│  └──────────────────┘   └───────────────────┘  │
│           (quizcraft_net — internal bridge)     │
│                                                │
│  Host port 8501 → quizcraft_v1                 │
└────────────────────────────────────────────────┘
```

Config (set via environment variable in docker-compose.yml):
```
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=qwen3:4b
```

---

### Option C — Remote Ollama Server

Ollama runs on a dedicated server (e.g. a VM with a GPU or a home server). The QuizCraft machine only runs Streamlit and makes API calls over the local network.

```
┌─────────────────────┐         ┌─────────────────────┐
│   App Machine       │         │   AI/LLM Server     │
│                     │         │                     │
│  Browser →          │  HTTP   │  Ollama :11434      │
│  Streamlit :8501 ───┼────────▶│  (0.0.0.0)          │
│                     │  LAN    │  Model: qwen3:4b    │
└─────────────────────┘         └─────────────────────┘
```

Config:
```ini
ollama_host = http://<server-ip>:11434
```

Ollama must be bound to `0.0.0.0` on the server (not the default `127.0.0.1`):
```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

---

### Public Deployment (Hosted Mode)

The public instance at [quizcraft.shafie.org](https://quizcraft.shafie.org) adds a Cloudflare Tunnel in front so no ports need to be opened on the host.

```
Internet
   │
   ▼
Cloudflare CDN / WAF
   │
   ▼
cloudflared tunnel (outbound only, no inbound ports)
   │
   ▼
nginx :80 (reverse proxy)
   │
   ▼
Streamlit :8502  (HOSTED_MODE=true — rate limited)
   │
   ▼
Ollama :11434 (internal, not reachable from outside)
```

---

## Request Flow

For every quiz generation:

1. User submits the form in the browser
2. `quiz_craft.py` validates and sanitizes the input
3. It spawns `generate_quiz_from_prompt.py` as a subprocess, passing the prompt via stdin
4. That script calls `POST /api/generate` on the Ollama server with the structured prompt
5. Ollama runs inference and returns a JSON response
6. The script extracts and normalizes the quiz JSON, writes it to stdout
7. `quiz_craft.py` reads stdout, parses the result, and renders the quiz

The subprocess boundary isolates the LLM call from the Streamlit process and prevents stdout contamination from any Ollama debug output.

---

## Config Resolution Order

For `OLLAMA_HOST` and `OLLAMA_MODEL`, the resolution priority is:

```
1. Environment variable (OLLAMA_HOST / OLLAMA_MODEL)  ← highest priority
2. config.ini  [OLLAMA_DETAILS] ollama_host / model_name
3. Hardcoded fallback: http://localhost:11434 / qwen3:4b  ← lowest priority
```
